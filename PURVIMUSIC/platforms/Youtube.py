import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIG IMPORT ---
import config 
from PURVIMUSIC.utils.formatters import time_to_seconds

# API Keys setup
API_KEYS = [k for k in [config.YT_API_KEY_1, config.YT_API_KEY_2, config.YT_API_KEY_3] if k]
current_key_index = 0

def get_youtube_client():
    global current_key_index
    if current_key_index >= len(API_KEYS):
        current_key_index = 0 
    return build("youtube", "v3", developerKey=API_KEYS[current_key_index])

cookies_file = getattr(config, "COOKIES_FILE_PATH", "PURVIMUSIC/cookies.txt")
if not os.path.exists(cookies_file):
    cookies_file = None

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    def parse_duration(self, duration):
        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        total_seconds = hours * 3600 + minutes * 60 + seconds
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
        return duration_str, total_seconds

    # --- YE FUNCTION ERROR FIX KAREGA ---
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
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        return False

    async def fetch_with_quota_check(self, service_type, **kwargs):
        global current_key_index
        while current_key_index < len(API_KEYS):
            try:
                youtube = get_youtube_client()
                if service_type == "search":
                    return await asyncio.to_thread(youtube.search().list(**kwargs).execute)
                elif service_type == "videos":
                    return await asyncio.to_thread(youtube.videos().list(**kwargs).execute)
            except HttpError as e:
                if e.resp.status == 403 and "quotaExceeded" in str(e):
                    current_key_index += 1
                    if current_key_index >= len(API_KEYS):
                        raise e
                else:
                    raise e
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            vidid = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
            vidid = match.group(1) if match else None

        if not vidid:
            search_res = await self.fetch_with_quota_check("search", q=link, part="id", maxResults=1, type="video")
            if not search_res or not search_res.get("items"): return None
            vidid = search_res["items"][0]["id"]["videoId"]

        video_res = await self.fetch_with_quota_check("videos", part="snippet,contentDetails", id=vidid)
        if not video_res or not video_res.get("items"): return None

        video_data = video_res["items"][0]
        duration_min, _ = self.parse_duration(video_data["contentDetails"]["duration"])
        return (
            video_data["snippet"]["title"],
            duration_min,
            None,
            video_data["snippet"]["thumbnails"]["high"]["url"],
            vidid
        )

    async def title(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[0] if res else "Unknown"

    async def track(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        if not res: return None, None
        title, duration_min, _, thumbnail, vidid = res
        return {"title": title, "link": self.base + vidid, "vidid": vidid, "duration_min": duration_min, "thumb": thumbnail}, vidid

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        opts = ["yt-dlp", "-g", "-f", "best[height<=?720][width<=?1280]", f"{link}"]
        if cookies_file:
            opts.extend(["--cookies", cookies_file])
        proc = await asyncio.create_subprocess_exec(*opts, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return (1, stdout.decode().split("\n")[0]) if stdout else (0, stderr.decode())

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

        if songvideo:
            fpath = f"downloads/{title}.mp4"
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL({**common_opts, "format": f"{format_id}+140", "outtmpl": f"downloads/{title}", "merge_output_format": "mp4"}).download([link]))
            return fpath
        elif songaudio:
            fpath = f"downloads/{title}.mp3"
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL({**common_opts, "format": format_id, "outtmpl": f"downloads/{title}.%(ext)s", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}).download([link]))
            return fpath

        return await loop.run_in_executor(None, audio_dl)
