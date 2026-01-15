import re
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters

# .env file load karne ke liye
load_dotenv()

# -----------------------------------------------------------------
# --- BASIC BOT CONFIGURATION ---
# -----------------------------------------------------------------
API_ID = int(getenv("API_ID", "123456")) # Telegram API ID
API_HASH = getenv("API_HASH", "abcdef1234567890") # Telegram API HASH
BOT_TOKEN = getenv("BOT_TOKEN", None) # @BotFather se mila hua token

# -----------------------------------------------------------------
# --- YOUTUBE API KEYS (3 KEYS SYSTEM) ---
# --- Pehle Key 1 use hogi, quota khatam hone par Key 2, phir Key 3 ---
# -----------------------------------------------------------------
YT_API_KEY = getenv("YT_API_KEY", "AIzaSyC_yPuJD0S75qMQFg-WobboAEPRjHXpl1M")
YT_API_KEY_2 = getenv("YT_API_KEY_2", "AIzaSyB5ofI6tA5S-fX1cCKvXuompJKnJRiv1SE")
YT_API_KEY_3 = getenv("YT_API_KEY_3", "")

# Cookies Path (YouTube block se bachne ke liye)
# Is file ko PURVIMUSIC folder ke andar hona chahiye
COOKIES_FILE_PATH = getenv("COOKIES_FILE_PATH", "PURVIMUSIC/cookies.txt")

# -----------------------------------------------------------------
# --- OWNER & LOGGING ---
# -----------------------------------------------------------------
OWNER_ID = int(getenv("OWNER_ID", "8520496440")) # Aapki Telegram ID
OWNER_USERNAME = getenv("OWNER_USERNAME", "VNI0X") # Aapka Username
LOGGER_ID = int(getenv("LOGGER_ID", "-1002223516578")) # Log group ID

# -----------------------------------------------------------------
# --- DATABASE ---
# -----------------------------------------------------------------
MONGO_DB_URI = getenv("MONGO_DB_URI", None)

# -----------------------------------------------------------------
# --- BOT DETAILS ---
# -----------------------------------------------------------------
BOT_NAME = getenv("BOT_NAME", "PURVI MUSIC")
BOT_USERNAME = getenv("BOT_USERNAME", "NIKKU_ROBOT")
ASSUSERNAME = getenv("ASSUSERNAME", None) # Assistant ID

# -----------------------------------------------------------------
# --- SESSIONS (STRING SESSIONS) ---
# -----------------------------------------------------------------
STRING1 = getenv("STRING_SESSION", None)
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)

# -----------------------------------------------------------------
# --- LIMITS & TIMEOUTS ---
# -----------------------------------------------------------------
# Playback limit in minutes
DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 17000))
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", 25))
SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION", "9999999"))
SONG_DOWNLOAD_DURATION_LIMIT = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "9999999"))

# Assistant Settings
AUTO_LEAVING_ASSISTANT = getenv("AUTO_LEAVING_ASSISTANT", "False")
AUTO_LEAVE_ASSISTANT_TIME = int(getenv("ASSISTANT_LEAVE_TIME", "9000"))

# -----------------------------------------------------------------
# --- SPOTIFY SETTINGS ---
# -----------------------------------------------------------------
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "1c21247d714244ddbb09925dac565aed")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "709e1a2969664491b58200860623ef19")

# -----------------------------------------------------------------
# --- IMAGES & LINKS ---
# -----------------------------------------------------------------
START_IMG_URL = getenv("START_IMG_URL", "https://graph.org/file/48031a9f0a99c6bf85490-033ed12793a22cbc12.jpg")
PING_IMG_URL = getenv("PING_IMG_URL", "https://graph.org/file/ede104b2b2bdadd060801-ce59d5add4472ecd84.jpg")
PLAYLIST_IMG_URL = "https://graph.org/file/cc0b24d87880ffd2c9174-10d3e3c8a5b407eb15.jpg"
STATS_IMG_URL = "https://files.catbox.moe/l58zhm.jpg"
TELEGRAM_AUDIO_URL = "https://files.catbox.moe/l58zhm.jpg"
TELEGRAM_VIDEO_URL = "https://files.catbox.moe/l58zhm.jpg"
STREAM_IMG_URL = "https://files.catbox.moe/l58zhm.jpg"
YOUTUBE_IMG_URL = "https://files.catbox.moe/l58zhm.jpg"

# Support Links
SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/about_deadly_venom")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/NOBITA_SUPPORT")

# -----------------------------------------------------------------
# --- OTHERS (HEROKU/REPO) ---
# -----------------------------------------------------------------
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com/lll-DEADLY-VENOM-lll/AARU_MUSIC")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN", None)

# --- INTERNAL VARS (Don't touch) ---
BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

# -----------------------------------------------------------------
# --- HELPER FUNCTIONS ---
# -----------------------------------------------------------------
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))

DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))

# Validation Checks
if SUPPORT_CHANNEL:
    if not re.match("(?:http|https)://", SUPPORT_CHANNEL):
        raise SystemExit("[ERROR] - Your SUPPORT_CHANNEL url is wrong.")

if SUPPORT_CHAT:
    if not re.match("(?:http|https)://", SUPPORT_CHAT):
        raise SystemExit("[ERROR] - Your SUPPORT_CHAT url is wrong.")
