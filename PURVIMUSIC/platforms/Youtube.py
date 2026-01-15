import asyncio
import os
import re
import logging
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIG IMPORT ---
import config 
from PURVIMUSIC.utils.formatters import time_to_seconds

# Logging setup (Error dekhne ke liye)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Keys setup
API_KEYS = [k for k in [config.YT_API_KEY_1, config.YT_API_KEY_2, config.YT_API_KEY_3] if k]
current_key_index = 0

def get_youtube_client():
    global current_key_index
    if not API_KEYS:
        return None
    if current_key_index >= len(API_KEYS):
        current_key_index = 0 
    # static_discovery=False lagane se 'discovery_cache' wala error khatam ho jayega
    return build("youtube", "v3", developerKey=API_KEYS[current_key_index], static_discovery=False)

cookies_file = getattr(config, "COOKIES_FILE_PATH", "PURVIMUSIC/cookies.txt")
if not os.path.exists(cookies_file):
    cookies_file = None

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    def parse_duration(self, duration):
        if not duration: return "00:00", 0
        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        total_seconds = hours * 3600 + minutes * 60 + seconds
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
        return duration_str, total_seconds

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset : entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if re.search(self.regex, link): return True
        return False

    async def fetch_with_quota_check(self, service_type, **kwargs):
        global current_key_index
        while current_key_index < len(API_KEYS):
            try:
                youtube = get_youtube_client()
                if not youtube: return None
                if service_type == "search":
                    return await asyncio.to_thread(youtube.search().list(**kwargs).execute)
                elif service_type == "videos":
                    return await asyncio.to_thread(youtube.videos().list(**kwargs).execute)
            except HttpError as e:
                if e.resp.status == 403: # Quota limit
                    logger.warning(f"API Key {current_key_index + 1} exhausted. Switching...")
                    current_key_index += 1
                else:
                    logger.error(f"YouTube API Error: {e}")
                    break
        return None

    # --- FALLBACK METHOD (Agar API Keys fail ho jayein) ---
    async def ytdl_fallback(self, query):
        loop = asyncio.get_running_loop()
        ydl_opts = {"quiet": True, "no_warnings": True, "format": "bestaudio/best"}
        if cookies_file: ydl_opts["cookiefile"] = cookies_file
        
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Agar query link nahi hai toh search karein
                search_query = f"ytsearch:{query}" if not re.search(self.regex, query) else query
                return ydl.extract_info(search_query, download=False)["entries"][0] if "entries" in search_query else ydl.extract_info(search_query, download=False)

        try:
            info = await loop.run_in_executor(None, extract)
            return (
                info["title"],
                f"{info['duration'] // 60:02d}:{info['duration'] % 60:02d}",
                None,
                info["thumbnail"],
                info["id"]
            )
        except Exception as e:
            logger.error(f"YT-DLP Fallback Error: {e}")
            return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        # 1. Pehle API Keys se koshish karein
        res = None
        if API_KEYS:
            if videoid:
                vidid = link
            else:
                match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
                vidid = match.group(1) if match else None

            if not vidid:
                search_res = await self.fetch_with_quota_check("search", q=link, part="id", maxResults=1, type="video")
                if search_res and search_res.get("items"):
                    vidid = search_res["items"][0]["id"]["videoId"]

            if vidid:
                video_res = await self.fetch_with_quota_check("videos", part="snippet,contentDetails", id=vidid)
                if video_res and video_res.get("items"):
                    video_data = video_res["items"][0]
                    duration_min, _ = self.parse_duration(video_data["contentDetails"]["duration"])
                    return (
                        video_data["snippet"]["title"],
                        duration_min,
                        None,
                        video_data["snippet"]["thumbnails"]["high"]["url"],
                        vidid
                    )

        # 2. Agar API fail hui toh YT-DLP use karein
        logger.info("Using YT-DLP Fallback for details...")
        return await self.ytdl_fallback(link)

    async def title(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[0] if res else "Unknown"

    async def track(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        if not res: return None, None
        title, duration_min, _, thumbnail, vidid = res
        return {"title": title, "link": self.base + vidid, "vidid": vidid, "duration_min": duration_min, "thumb": thumbnail}, vidid

    async def download(self, link: str, mystic, video=None, videoid=None, songaudio=None, songvideo=None, format_id=None, title=None) -> str:
        if videoid: link = self.base + link
        loop = asyncio.get_running_loop()
        common_opts = {"geo_bypass": True, "nocheckcertificate": True, "quiet": True, "no_warnings": True}
        if cookies_file: common_opts["cookiefile"] = cookies_file

        def audio_dl():
            ydl_opts = {**common_opts, "format": "bestaudio/best", "outtmpl": "downloads/%(id)s.%(ext)s"}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, False)
                path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                if not os.path.exists(path): ydl.download([link])
                return path

        return await loop.run_in_executor(None, audio_dl)
