import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from ytmusicapi import YTMusic

from PURVIMUSIC.utils.database import is_on_off
from PURVIMUSIC.utils.formatters import time_to_seconds

# Global instance
yt_music = YTMusic()

# Filename se special characters hatane ke liye function
def sanitize_filename(title: str):
    return re.sub(r'[\\/*?:"<>|]', "", title)

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

cookies_file = "PURVIMUSIC/cookies.txt"
if not os.path.exists(cookies_file):
    cookies_file = None

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset is None:
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        # Agar link direct YouTube ka hai toh yt-dlp use karein (zyada reliable hai)
        if re.search(self.regex, link):
            loop = asyncio.get_running_loop()
            def get_info():
                with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                    return ydl.extract_info(link, download=False)
            try:
                info = await loop.run_in_executor(None, get_info)
                title = info.get('title', 'Unknown Title')
                duration_sec = info.get('duration', 0)
                duration_min = f"{duration_sec // 60:02d}:{duration_sec % 60:02d}"
                thumbnail = info.get('thumbnail')
                vidid = info.get('id')
                return title, duration_min, duration_sec, thumbnail, vidid
            except Exception:
                return None

        # Agar search query hai toh YTMusic search karein
        try:
            search = await asyncio.to_thread(yt_music.search, link, filter="songs", limit=1)
            if not search:
                return None
            result = search[0]
            title = result.get("title", "Unknown")
            duration_min = result.get("duration", "04:00")
            thumbnail = result["thumbnails"][-1]["url"].split("?")[0] if "thumbnails" in result else None
            vidid = result.get("videoId")
            duration_sec = int(time_to_seconds(duration_min))
            return title, duration_min, duration_sec, thumbnail, vidid
        except Exception:
            return None

    async def title(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[0] if res else "Unknown"

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[1] if res else "00:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[3] if res else None

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        opts = ["yt-dlp", "-g", "-f", "best[height<=?720][width<=?1280]", f"{link}"]
        if cookies_file:
            opts.insert(1, "--cookies")
            opts.insert(2, cookies_file)

        proc = await asyncio.create_subprocess_exec(
            *opts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        
        cookie_cmd = f"--cookies {cookies_file}" if cookies_file else ""
        playlist = await shell_cmd(
            f"yt-dlp {cookie_cmd} -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = [k for k in playlist.split("\n") if k != ""]
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        if not res:
            return None, None
        
        title, duration_min, duration_sec, thumbnail, vidid = res
        track_details = {
            "title": title,
            "link": self.base + vidid,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        try:
            search = await asyncio.to_thread(yt_music.search, link, filter="songs", limit=10)
            if not search or len(search) <= query_type:
                return None
            result = search[query_type]
            title = result.get("title", "Unknown")
            duration_min = result.get("duration", "00:00")
            vidid = result.get("videoId")
            thumbnail = result["thumbnails"][-1]["url"].split("?")[0] if "thumbnails" in result else None
            return title, duration_min, thumbnail, vidid
        except Exception:
            return None

    async def download(
        self, link: str, mystic, video=None, videoid=None, songaudio=None, songvideo=None, format_id=None, title=None
    ) -> str:
        if videoid:
            link = self.base + link
        
        # Title ko safe banayein (Special characters hatayein)
        safe_title = sanitize_filename(title) if title else "track"
        loop = asyncio.get_running_loop()

        common_opts = {
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
        }
        if cookies_file:
            common_opts["cookiefile"] = cookies_file

        if songvideo:
            fpath = f"downloads/{safe_title}.mp4"
            def sv_dl():
                with yt_dlp.YoutubeDL({**common_opts, "format": f"{format_id}+140", "outtmpl": f"downloads/{safe_title}", "merge_output_format": "mp4"}) as ydl:
                    ydl.download([link])
            await loop.run_in_executor(None, sv_dl)
            return fpath

        elif songaudio:
            fpath = f"downloads/{safe_title}.mp3"
            def sa_dl():
                with yt_dlp.YoutubeDL({**common_opts, "format": format_id if format_id else "bestaudio/best", "outtmpl": f"downloads/{safe_title}.%(ext)s", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}) as ydl:
                    ydl.download([link])
            await loop.run_in_executor(None, sa_dl)
            return fpath

        # Best Audio/Video default download
        def default_dl(is_video):
            format_opt = "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])" if is_video else "bestaudio/best"
            ydl_opts = {**common_opts, "format": format_opt, "outtmpl": "downloads/%(id)s.%(ext)s"}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return ydl.prepare_filename(info)

        downloaded_file = await loop.run_in_executor(None, default_dl, video)
        return downloaded_file, True
