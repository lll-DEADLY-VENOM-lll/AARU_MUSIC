import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from ytmusicapi import YTMusic

# Global instance for YT Music
yt_music = YTMusic()

def time_to_seconds(time):
    try:
        string_format = sum(60**i * int(x) for i, x in enumerate(reversed(time.split(':'))))
        return string_format
    except:
        return 0

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be|music\.youtube\.com)"
        self.cookies = "PURVIMUSIC/cookies.txt"

    # --- Telegram Message se URL nikalne ke liye (Fixed AttributeError) ---
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
                        
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def exists(self, link: str):
        if re.search(self.regex, link):
            return True
        return False

    # --- Gaane ki details (SABR Fix ke saath) ---
    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        # SABR error bypass settings
        ydl_opts = {
            "quiet": True,
            "cookiefile": self.cookies if os.path.exists(self.cookies) else None,
            "geo_bypass": True,
            "extractor_args": {"youtube": {"player_client": ["android", "web"], "player_skip": ["webpage"]}},
            "user_agent": "Mozilla/5.0 (Android 14; Mobile; rv:128.0) Gecko/128.0 Firefox/128.0"
        }

        if await self.exists(link):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, link, download=False)
                title = info['title']
                duration_sec = info.get('duration', 0)
                duration_min = f"{duration_sec // 60:02d}:{duration_sec % 60:02d}"
                thumbnail = info.get('thumbnail')
                vidid = info['id']
                return title, duration_min, duration_sec, thumbnail, vidid
        else:
            # YouTube Music Search
            search = await asyncio.to_thread(yt_music.search, link, filter="songs", limit=1)
            if not search:
                return None
            result = search[0]
            title = result["title"]
            duration_min = result.get("duration", "04:00")
            thumbnail = result["thumbnails"][-1]["url"].split("?")[0]
            vidid = result["videoId"]
            duration_sec = int(time_to_seconds(duration_min))
            return title, duration_min, duration_sec, thumbnail, vidid

    # --- Direct Stream Link (SABR Fix & Android Client Force) ---
    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.replace("music.youtube.com", "youtube.com")

        opts = [
            "yt-dlp",
            "-g",
            "--force-ipv4",
            "--no-warnings",
            # SABR aur 'missing url' error ko bypass karne ke liye android client force karein
            "--extractor-args", "youtube:player_client=android,web;player_skip=webpage",
            "-f", "bestaudio/best",
            f"{link}"
        ]

        if os.path.exists(self.cookies):
            opts.insert(1, "--cookies")
            opts.insert(2, self.cookies)

        proc = await asyncio.create_subprocess_exec(
            *opts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if stdout:
            return 1, stdout.decode().split("\n")[0].strip()
        else:
            error_msg = stderr.decode()
            print(f"YT-DLP ERROR: {error_msg}")
            return 0, error_msg

    # --- Playlist extraction ---
    async def playlist(self, link, limit):
        cookie_cmd = f"--cookies {self.cookies}" if os.path.exists(self.cookies) else ""
        # Flat playlist optimization
        command = f"yt-dlp {cookie_cmd} -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return [k for k in stdout.decode().split("\n") if k]
        return []

    # --- Track info getter ---
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

    # --- Download method ---
    async def download(self, link: str, title: str, songaudio=False):
        if "&" in link:
            link = link.split("&")[0]
        
        loop = asyncio.get_running_loop()
        fpath = os.path.join("downloads", f"{title}.mp3")

        def dl():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"downloads/{title}.%(ext)s",
                "cookiefile": self.cookies if os.path.exists(self.cookies) else None,
                "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "quiet": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            return fpath

        return await loop.run_in_executor(None, dl)
