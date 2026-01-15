import re
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()

# --- BASIC BOT CONFIGURATION ---
API_ID = int(getenv("API_ID", "")) 
API_HASH = getenv("API_HASH", "") 
BOT_TOKEN = getenv("BOT_TOKEN") 
MONGO_DB_URI = getenv("MONGO_DB_URI", None)

# -----------------------------------------------------------------
# YOUTUBE API KEYS (MULTI-KEY SUPPORT)
# -----------------------------------------------------------------
API_KEY = getenv("API_KEY", "AIzaSyC_yPuJD0S75qMQFg-WobboAEPRjHXpl1M, AIzaSyB5ofI6tA5S-fX1cCKvXuompJKnJRiv1SE")
# -----------------------------------------------------------------

# --- BOT & OWNER DETAILS ---
BOT_NAME = getenv("BOT_NAME", "PURVI MUSIC")
BOT_USERNAME = getenv("BOT_USERNAME", "NIKKU_ROBOT") 
OWNER_ID = int(getenv("OWNER_ID", "7967418569"))
OWNER_USERNAME = getenv("OWNER_USERNAME", "VNI0X")
ASSUSERNAME = getenv("ASSUSERNAME", "PURVI_ASSISTANT") 

# --- LIMITS & TIMEOUTS ---
DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 300))
SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION", "999999")) 
SONG_DOWNLOAD_DURATION_LIMIT = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "999999"))
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", 25))

# --- LOGGING ---
LOGGER_ID = int(getenv("LOGGER_ID", "-1001511253627"))

# --- HEROKU & REPO ---
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")
UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com/VNI0X/VNI0XAPIBASE")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN", None)

# --- SUPPORT ---
SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/about_deadly_venom")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/NOBITA_SUPPORT")

# --- ASSISTANT SETTINGS ---
AUTO_LEAVING_ASSISTANT = bool(getenv("AUTO_LEAVING_ASSISTANT", True))
ASSISTANT_LEAVE_TIME = int(getenv("ASSISTANT_LEAVE_TIME", 5400))

# --- SPOTIFY ---
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "1c21247d714244ddbb09925dac565aed")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "709e1a2969664491b58200860623ef19")

# --- FILE SIZE LIMITS ---
TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", 204857600))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", 2073741824))

# --- SESSIONS ---
STRING1 = getenv("STRING_SESSION", None)
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)

# --- IMAGES (SABHI MISSING LINKS ADDED) ---
START_IMG_URL = getenv("START_IMG_URL", "https://graph.org/file/9e3513de206670417d884-6529b8b9f8f6748812.jpg")
PING_IMG_URL = getenv("PING_IMG_URL", "https://graph.org/file/062f851978de03808885f-eb92d34cde8511a7d6.jpg")
PLAYLIST_IMG_URL = "https://graph.org/file/df60a4160209a6ca58eb2-6473d069fe73f4f397.jpg"
STATS_IMG_URL = "https://telegra.ph/file/edd388a42dd2c499fd868.jpg"
TELEGRAM_AUDIO_URL = "https://telegra.ph/file/492a3bb2e880d19750b79.jpg"
TELEGRAM_VIDEO_URL = "https://telegra.ph/file/492a3bb2e880d19750b79.jpg"
STREAM_IMG_URL = "https://graph.org/file/ff2af8d4d10afa1baf49e.jpg"
SOUNCLOUD_IMG_URL = "https://graph.org/file/c95a687e777b55be1c792.jpg" # Ye missing tha
YOUTUBE_IMG_URL = "https://graph.org/file/e8730fdece86a1166f608.jpg"
SPOTIFY_ARTIST_IMG_URL = "https://graph.org/file/0bb6f36796d496b4254ff.jpg"
SPOTIFY_ALBUM_IMG_URL = "https://graph.org/file/0bb6f36796d496b4254ff.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://graph.org/file/0bb6f36796d496b4254ff.jpg"

# --- INTERNAL VARS ---
BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

# --- HELPERS ---
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))

DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))

# Validation
if SUPPORT_CHANNEL and not re.match("(?:http|https)://", SUPPORT_CHANNEL):
    raise SystemExit("[ERROR] - Your SUPPORT_CHANNEL url is wrong.")
if SUPPORT_CHAT and not re.match("(?:http|https)://", SUPPORT_CHAT):
    raise SystemExit("[ERROR] - Your SUPPORT_CHAT url is wrong.")
