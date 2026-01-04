import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from ytmusicapi import YTMusic

from PURVIMUSIC.utils.formatters import time_to_seconds

# Global instance
yt_music = YTMusic()

def sanitize_filename(title: str):
    return re.sub(r'[\\/*?:"<>|]', "", str(title))

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        loop = asyncio.get_running_loop()
        
        def get_info():
            opts = {
                "quiet": True, 
                "no_warnings": True, 
                "format": "bestaudio/best",
                "skip_download": True,
                "nocheckcertificate": True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(link, download=False)

        try:
            info = await loop.run_in_executor(None, get_info)
            if not info:
                raise Exception("No info")
                
            return {
                "title": str(info.get('title', 'Unknown Title')),
                "duration_min": f"{int(info.get('duration', 0)) // 60:02d}:{int(info.get('duration', 0)) % 60:02d}",
                "duration_sec": int(info.get('duration', 0)),
                "thumb": str(info.get('thumbnail', "")),
                "vidid": str(info.get('id', "None"))
            }
        except Exception:
            try:
                search = await asyncio.to_thread(yt_music.search, link, filter="songs", limit=1)
                if search:
                    res = search[0]
                    return {
                        "title": str(res.get("title", "Unknown Title")),
                        "duration_min": str(res.get("duration", "04:00")),
                        "duration_sec": int(time_to_seconds(res.get("duration", "04:00"))),
                        "thumb": str(res["thumbnails"][-1]["url"] if "thumbnails" in res else ""),
                        "vidid": str(res.get("videoId", "None"))
                    }
            except:
                pass
            
            # Agar sab fail ho jaye toh default data bhejo taaki AttributeError na aaye
            return {
                "title": "Unknown Title",
                "duration_min": "00:00",
                "duration_sec": 0,
                "thumb": "",
                "vidid": "None"
            }

    async def title(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res["duration_min"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res["thumb"]

    async def track(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        # Track function expects a dict and the video ID
        track_details = {
            "title": res["title"],
            "link": self.base + res["vidid"],
            "vidid": res["vidid"],
            "duration_min": res["duration_min"],
            "thumb": res["thumb"],
        }
        return track_details, res["vidid"]

    async def download(
        self, link: str, mystic, video=None, videoid=None, songaudio=None, songvideo=None, format_id=None, title=None
    ) -> str:
        if videoid:
            link = self.base + link
        
        # Title ko safe banayein taaki file save ho sake
        safe_title = sanitize_filename(title) if title else "track"
        loop = asyncio.get_running_loop()
        common_opts = {"quiet": True, "no_warnings": True, "geo_bypass": True, "nocheckcertificate": True}

        if songaudio:
            fpath = f"downloads/{safe_title}.mp3"
            def sa_dl():
                opts = {
                    **common_opts, 
                    "format": format_id if format_id else "bestaudio/best", 
                    "outtmpl": f"downloads/{safe_title}.%(ext)s",
                    "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
                }
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([link])
            await loop.run_in_executor(None, sa_dl)
            return fpath

        def dl():
            opts = {**common_opts, "format": "bestaudio/best", "outtmpl": "downloads/%(id)s.%(ext)s"}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return ydl.prepare_filename(info)

        downloaded_file = await loop.run_in_executor(None, dl)
        return downloaded_file, True
