import asyncio
import os
import re
import random
import logging
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from googleapiclient.discovery import build 
from googleapiclient.errors import HttpError

import config 
from PURVIMUSIC.utils.formatters import time_to_seconds # Path check kar lein

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- API ROTATION LOGIC ---
# config.py mein API_KEY = "key1, key2, key3" aise likhein
API_KEYS = [k.strip() for k in config.API_KEY.split(",")]

def get_youtube_client():
    """Randomly selects an API Key and returns a YouTube client"""
    if not API_KEYS:
        return None
    selected_key = random.choice(API_KEYS)
    return build("youtube", "v3", developerKey=selected_key, static_discovery=False)

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    return out.decode("utf-8") if not errorz else errorz.decode("utf-8")

# --- COOKIES FILE SETUP ---
cookie_txt_file = "PURVIMUSIC/cookies.txt"
if not os.path.exists(cookie_txt_file):
    cookie_txt_file = None

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    def parse_duration(self, duration):
        if not duration: return "00:00", 0
        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        hours, minutes, seconds = [int(match.group(i) or 0) for i in range(1, 4)]
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return (f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"), total_seconds

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1, message_1.reply_to_message] if message_1.reply_to_message else [message_1]
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        return (message.text or message.caption)[entity.offset : entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    # --- YT-DLP FALLBACK (Agar API fail ho jaye) ---
    async def ytdl_fallback(self, query):
        loop = asyncio.get_running_loop()
        ydl_opts = {"quiet": True, "no_warnings": True, "format": "bestaudio/best", "skip_download": True}
        if cookie_txt_file: ydl_opts["cookiefile"] = cookie_txt_file
        
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                is_url = re.search(self.regex, query)
                search_query = query if is_url else f"ytsearch1:{query}"
                info = ydl.extract_info(search_query, download=False)
                return info["entries"][0] if "entries" in info else info

        try:
            info = await loop.run_in_executor(None, extract)
            title, duration, thumb, vidid = info.get("title"), info.get("duration"), info.get("thumbnail"), info.get("id")
            d_str = f"{duration // 60:02d}:{duration % 60:02d}"
            return title, d_str, duration, thumb, vidid
        except Exception as e:
            logger.error(f"Fallback Error: {e}")
            return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        # 1. Try with API Keys first
        if API_KEYS:
            try:
                if videoid: vidid = link
                else:
                    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
                    vidid = match.group(1) if match else None
                
                youtube = get_youtube_client()
                if not vidid:
                    search_res = await asyncio.to_thread(youtube.search().list(q=link, part="id", maxResults=1, type="video").execute)
                    if search_res.get("items"): vidid = search_res["items"][0]["id"]["videoId"]
                
                if vidid:
                    v_res = await asyncio.to_thread(youtube.videos().list(part="snippet,contentDetails", id=vidid).execute)
                    if v_res.get("items"):
                        data = v_res["items"][0]
                        d_str, _ = self.parse_duration(data["contentDetails"]["duration"])
                        return data["snippet"]["title"], d_str, None, data["snippet"]["thumbnails"]["high"]["url"], vidid
            except HttpError as e:
                if e.resp.status == 403:
                    logger.warning("API Quota exceeded, trying fallback...")
            except Exception as e:
                logger.error(f"API Error: {e}")

        # 2. Fallback to YT-DLP if API fails
        return await self.ytdl_fallback(link)

    async def title(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[0] if res else "Unknown"

    async def track(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        if not res: return None, None
        title, d_min, _, thumb, vidid = res
        track_details = {"title": title, "link": self.base + vidid, "vidid": vidid, "duration_min": d_min, "thumb": thumb}
        return track_details, vidid

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        opts = ["yt-dlp", "-g", "-f", "best[height<=?480][ext=mp4]/best", "--no-playlist", "--geo-bypass", f"{link}"]
        if cookie_txt_file:
            opts.extend(["--cookies", cookie_txt_file])
        proc = await asyncio.create_subprocess_exec(*opts, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return (1, stdout.decode().split("\n")[0]) if stdout else (0, stderr.decode())

    async def download(self, link: str, mystic, video=None, videoid=None, songaudio=None, songvideo=None, format_id=None, title=None) -> str:
        if videoid: link = self.base + link
        loop = asyncio.get_running_loop()
        common_opts = {"geo_bypass": True, "quiet": True, "no_warnings": True}
        if cookie_txt_file: common_opts["cookiefile"] = cookie_txt_file

        def dl():
            if songvideo:
                ydl_opts = {**common_opts, "format": f"{format_id}+140", "outtmpl": f"downloads/{title}", "merge_output_format": "mp4"}
            elif songaudio:
                ydl_opts = {**common_opts, "format": format_id, "outtmpl": f"downloads/{title}.%(ext)s", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}
            else:
                ydl_opts = {**common_opts, "format": "bestaudio/best", "outtmpl": "downloads/%(id)s.%(ext)s"}
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return os.path.join("downloads", f"{info.get('id', title)}.{info.get('ext', 'mp3')}")

        path = await loop.run_in_executor(None, dl)
        return path
