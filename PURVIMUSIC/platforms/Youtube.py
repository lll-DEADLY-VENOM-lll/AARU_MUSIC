import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from ytmusicapi import YTMusic

# Global instance
yt_music = YTMusic()

# Time converter helper
def time_to_seconds(time):
    string_format = sum(60**i * int(x) for i, x in enumerate(reversed(time.split(':'))))
    return string_format

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be|music\.youtube\.com)"
        self.cookies = "PURVIMUSIC/cookies.txt" # Aapka cookie path

    async def exists(self, link: str):
        if re.search(self.regex, link):
            return True
        return False

    # 1. Gaane ki details nikalne ke liye
    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        
        if "&" in link:
            link = link.split("&")[0]

        # Agar direct link hai
        if await self.exists(link):
            opts = {
                "quiet": True,
                "cookiefile": self.cookies if os.path.exists(self.cookies) else None,
                "geo_bypass": True
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, link, download=False)
                title = info['title']
                duration_sec = info['duration']
                duration_min = f"{duration_sec // 60:02d}:{duration_sec % 60:02d}"
                thumbnail = info['thumbnail']
                vidid = info['id']
                return title, duration_min, duration_sec, thumbnail, vidid
        
        # Agar search query hai (YT Music se)
        else:
            search = await asyncio.to_thread(yt_music.search, link, filter="songs", limit=1)
            if not search:
                return None
            result = search[0]
            title = result["title"]
            duration_min = result.get("duration", "04:00")
            # High quality thumbnail fix
            thumbnail = result["thumbnails"][-1]["url"].split("?")[0]
            vidid = result["videoId"]
            duration_sec = int(time_to_seconds(duration_min))
            return title, duration_min, duration_sec, thumbnail, vidid

    # 2. Direct Streaming Link nikalne ke liye (Cookies fix yahan hai)
    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        
        # music.youtube.com ko normal youtube mein convert karein for better compatibility
        link = link.replace("music.youtube.com", "youtube.com")

        # Command line arguments for yt-dlp
        opts = [
            "yt-dlp",
            "-g", 
            "--force-ipv4", # Server blocks se bachne ke liye
            "--no-warnings",
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
            error = stderr.decode()
            print(f"YT-DLP ERROR: {error}")
            return 0, error

    # 3. Download function (for playing downloaded files)
    async def download(self, link: str, title: str):
        if "&" in link:
            link = link.split("&")[0]
            
        loop = asyncio.get_running_loop()
        fpath = f"downloads/{title}.mp3"

        def dl():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"downloads/{title}.%(ext)s",
                "cookiefile": self.cookies if os.path.exists(self.cookies) else None,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            return fpath

        return await loop.run_in_executor(None, dl)

# --- Usage in Telegram Bot Command ---
# Example logic for your Play command:
#
# async def play_cmd(client, message):
#     query = message.text.split(None, 1)[1]
#     yt = YouTubeAPI()
#     
#     # 1. Details lein
#     title, duration_min, duration_sec, thumb, vidid = await yt.details(query)
#     
#     # 2. Direct link nikalen
#     status, stream_link = await yt.video(f"https://www.youtube.com/watch?v={vidid}")
#     
#     if status == 1:
#         # Play in PyTgCalls using stream_link
#         pass
#     else:
#         await message.reply(f"Error: {stream_link}")
