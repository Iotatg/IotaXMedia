# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import re
from os import getenv
from dotenv import load_dotenv

load_dotenv()


def _int_env(key, default=0):
    try:
        return int(getenv(key, str(default)))
    except (ValueError, TypeError):
        return default



API_ID = _int_env("API_ID")
API_HASH = getenv("API_HASH", "")


CLONE_MODE = bool(int(getenv("CLONE_MODE", "0")))


if CLONE_MODE:
    BOT_TOKEN = getenv("CLONE_TOKEN", getenv("BOT_TOKEN", ""))
else:
    BOT_TOKEN = getenv("BOT_TOKEN", "")
BOT_ID = getenv("BOT_ID", "")


OWNER_ID = _int_env("OWNER_ID")
OWNER_USERNAME = getenv("OWNER_USERNAME", "@im_ntg")
BOT_USERNAME = getenv("BOT_USERNAME", "Iotamusicbot")
BOT_NAME = getenv("BOT_NAME", "IotaX Media")
ASSUSERNAME = getenv("ASSUSERNAME", "")


BOT_AGE = getenv("BOT_AGE", "19")
BOT_FROM = getenv("BOT_FROM", "Mumbai, India")
BOT_DOB = getenv("BOT_DOB", "9 March 2007")


GIPHY_API_KEY = getenv("GIPHY_API_KEY", "")


BOT_LINK = getenv("BOT_LINK", "https://t.me/Iotamusicbot?start=clone")


MONGO_DB_URI = getenv("MONGO_DB_URI", "")






YTPROXY_URL = getenv("YTPROXY_URL", "")
YT_API_KEY = getenv("YT_API_KEY", "")





NUB_API_URL = getenv("NUB_API_URL", "https://api.nubcoders.com")
NUB_API_KEY = getenv("NUB_API_KEY", "")


SHRUTI_API_URL = getenv("SHRUTI_API_URL", "https://api.shrutibots.site")
SHRUTI_API_KEY = getenv("SHRUTI_API_KEY", "ShrutiBotsgBDkKisTQy4dawsleMKu")
YUKI_API_URL = getenv("YUKI_API_URL", "https://music.yukiapi.site")
YUKI_API_KEY = getenv("YUKI_API_KEY", "")





LITTERBOX_ENABLED = bool(int(getenv("LITTERBOX_ENABLED", "0")))
LITTERBOX_TTL = getenv("LITTERBOX_TTL", "12h")
LITTERBOX_TIMEOUT = int(getenv("LITTERBOX_TIMEOUT", "180"))
LITTERBOX_MAX_BYTES = int(getenv("LITTERBOX_MAX_BYTES", "100")) * 1024 * 1024
LITTERBOX_API_URL = getenv(
    "LITTERBOX_API_URL", "https://litterbox.catbox.moe/resources/internals/api.php"
)


DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", "17000"))


LOGGER_ID = _int_env("LOGGER_ID")
CLONE_LOGGER = LOGGER_ID
DEBUG_IGNORE_LOG = False


OBSERVABILITY = bool(int(getenv("OBSERVABILITY", "1")))
ERROR_HISTORY_FILE = getenv("ERROR_HISTORY_FILE", "logs/errors.jsonl")
ERROR_BUFFER_SIZE = _int_env("ERROR_BUFFER_SIZE", 500)
ERROR_RATE_ALERT_THRESHOLD = _int_env("ERROR_RATE_ALERT_THRESHOLD", 10)



ADD_MANAGER = bool(int(getenv("ADD_MANAGER", "1")))


HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")


UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/ZXCVBNMASDFGHJKLQWERTYUIOP0786/SilentCloneBot",
)
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN", "")
COOKIE_URL = getenv("COOKIE_URL", "")


SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/IotaUpdates")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/samvadacha_chat")
GITHUB = getenv("GITHUB", "https://t.me/IotaUpdates")


AUTO_LEAVING_ASSISTANT = False
AUTO_LEAVE_ASSISTANT_TIME = int(getenv("ASSISTANT_LEAVE_TIME", "9000"))


SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION", "9999999"))
SONG_DOWNLOAD_DURATION_LIMIT = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "9999999"))


SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "")


PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", "25"))
PLAYLIST_ID = -1001980154960


TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", "5242880000"))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", "5242880000"))


STRING1 = getenv("STRING_SESSION", "")
STRING2 = getenv("STRING_SESSION2", "")
STRING3 = getenv("STRING_SESSION3", "")
STRING4 = getenv("STRING_SESSION4", "")
STRING5 = getenv("STRING_SESSION5", "")


BANNED_USERS = set()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}


_GH = "https://raw.githubusercontent.com/Iotatg/Iota/main"

GITHUB_AVATAR_URL = getenv("GITHUB_AVATAR_URL", "https://github.com/Iotatg.png")

IOTA_HERO_URL = getenv("IOTA_HERO_URL", f"{_GH}/IotaHero.jpg")
START_IMG_URL = getenv("START_IMG_URL", IOTA_HERO_URL)
HELP_IMG_URL = getenv("HELP_IMG_URL", IOTA_HERO_URL)
PING_IMG_URL = getenv("PING_IMG_URL", IOTA_HERO_URL)

PLAYLIST_IMG_URL = getenv("PLAYLIST_IMG_URL", f"{_GH}/playlist.jpg")
STATS_IMG_URL = getenv("STATS_IMG_URL", f"{_GH}/stream.jpg")
TELEGRAM_AUDIO_URL = getenv("TELEGRAM_AUDIO_URL", f"{_GH}/telegram.jpg")
TELEGRAM_VIDEO_URL = getenv("TELEGRAM_VIDEO_URL", f"{_GH}/telegram%20video%20play.jpg")
STREAM_IMG_URL = getenv("STREAM_IMG_URL", f"{_GH}/stream.jpg")
SOUNCLOUD_IMG_URL = getenv("SOUNCLOUD_IMG_URL", f"{_GH}/soundcloud.jpg")
YOUTUBE_IMG_URL = getenv("YOUTUBE_IMG_URL", f"{_GH}/YouTube.jpeg")
SPOTIFY_ARTIST_IMG_URL = getenv("SPOTIFY_ARTIST_IMG_URL", f"{_GH}/Spotify%20artist.jpg")
SPOTIFY_ALBUM_IMG_URL = getenv("SPOTIFY_ALBUM_IMG_URL", f"{_GH}/spotify%20album.jpg")
SPOTIFY_PLAYLIST_IMG_URL = getenv("SPOTIFY_PLAYLIST_IMG_URL", f"{_GH}/Spotify%20playlist.webp")

REPO_IMG_URL = getenv("REPO_IMG_URL", GITHUB_AVATAR_URL)


def time_to_seconds(time):
    return sum(int(x) * 60**i for i, x in enumerate(reversed(str(time).split(":"))))


DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))

if SUPPORT_CHANNEL and not re.match("(?:http|https)://", SUPPORT_CHANNEL):
    raise SystemExit("[ERROR] - SUPPORT_CHANNEL url must start with https://")

if SUPPORT_CHAT and not re.match("(?:http|https)://", SUPPORT_CHAT):
    raise SystemExit("[ERROR] - SUPPORT_CHAT url must start with https://")


DEFAULT_VOLUME = 50
MIN_VOLUME = 0
MAX_VOLUME = 100
VOLUME_STEP = 15


API_KEY = getenv("API_KEY", "ShrutiBotsOKChMnKPT8mJA5xKDo1e")
API_URL = getenv("API_URL", "https://teaminflex.xyz")
VIDEO_API_URL = getenv("VIDEO_API_URL", "https://teaminflex.xyz")
AYU = [
    "🔎 sᴇᴀʀᴄʜɪɴɢ...\n\nᴘʟᴇᴀsᴇ ᴡᴀɪᴛ",
    "⏳ ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ǫᴜᴇʀʏ...\n\nᴀʟᴍᴏsᴛ ᴛʜᴇʀᴇ",
    "🎵 ғɪɴᴅɪɴɢ ᴛʜᴇ ʙᴇsᴛ ᴍᴀᴛᴄʜ...\n\nᴘʟᴇᴀsᴇ ᴡᴀɪᴛ",
]
AYUV = [
    (
        "<blockquote expandable>"
        "✦ <b>Ꭲʜᴧηᴋ Yσυ {0}, Fσꝛ Σηᴛєꝛɪηɢ Iη 𐌉σᴛᴧ Rєᴧʟϻ.</b>\n"
        "➻ Pꝛєsєηᴛɪηɢ {1} ツ — Λη Iϻϻєꝛsɪᴠє δσηɪᴄ Σxᴘєꝛɪєηᴄє.\n\n"
        "➤ Eηɢɪηєєꝛєᴅ Fσꝛ Fʟυɪᴅ Vσɪᴄє δᴛꝛєᴧϻɪηɢ Ληᴅ Uηɪηᴛєꝛꝛυᴘᴛєᴅ Pʟᴧʏʙᴧᴄᴋ.\n"
        "➤ Rєᴘʟɪᴄᴧᴛє Ꭲʜє Σηᴛɪꝛє Σᴄσsʏsᴛєϻ Iηᴛσ Yσυꝛ Oᴡη Iᴅєηᴛɪᴛʏ Wɪᴛʜ Jυsᴛ Λ Fєᴡ Ꭲᴧᴘs.\n"
        "•── ⋅ ⋅ ⋅ ──────── ⋅ • ⋅ ──────── ⋅ ⋅ ⋅ ──•\n"
        "➤ Oᴘєη Ꭲʜє Hєʟᴘ Pᴧηєʟ Ꭲσ Uηᴄσᴠєꝛ Σᴠєʀʏ Cᴧᴘᴧʙɪʟɪᴛʏ."
        "</blockquote>\n\n"
        "<b>✫ υρϯɪᴍє :</b> {2}\n"
        "<b>✫ ᴅɪsᴋ :</b> {3}%  |  <b>ᴄᴘᴜ :</b> {4}%  |  <b>ʀᴀᴍ :</b> {5}%\n"
        "<b>✫ υѕєʀѕ :</b> {6}  |  <b>ᴄнαᴛѕ :</b> {7}\n\n"
        "<blockquote><b>🫧 ᴅєνєlσᴩєʀ 🪽 ➪ <a href=\"https://t.me/im_ntg\">ησϯнɪηɢ ✔︎</a></b></blockquote>"
    )
]
STICKERS = []
DEEP_API = ""
POST_GROUP_ID = ""
youtube_thumb = lambda vid, quality="hqdefault": f"https://img.youtube.com/vi/{vid}/{quality}.jpg"


AI_PROVIDER = "openai"
AI_API_KEY = ""
AI_API_URL = "https://api.openai.com/v1/chat/completions"
AI_MODEL = "gpt-4o-mini"
AI_MAX_TOKENS = 1024
AI_SYSTEM_PROMPT = "You are Iota, a helpful, friendly AI assistant inside the Iota Music Bot."


APINEX_API_KEY = getenv("APINEX_API_KEY", "")
APINEX_MODEL = getenv("APINEX_MODEL", "free/glm-5.3-flash")
APINEX_FALLBACK_MODEL = getenv("APINEX_FALLBACK_MODEL", "free/deepseek-v4-flash-0731")
APINEX_MEDIA_FALLBACK_MODEL = getenv("APINEX_MEDIA_FALLBACK_MODEL", "free/gemini-3.8-flash")
APINEX_API_URL = "https://api.apinex.bond/v1/chat/completions"


GROQ_API_KEY = getenv("GROQ_API_KEY", "")
GROQ_MODEL = getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MAX_TOKENS = 1024
GROQ_CHATBOT_SYSTEM_PROMPT = "You are Iota, a helpful, friendly AI assistant inside the Iota Music Bot. Answer concisely in the same language the user writes in."


OPENROUTER_API_KEY = getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = getenv("OPENROUTER_MODEL", "dots-studio/dots-3-note-preview:free")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"



SEARXNG_URL = getenv("SEARXNG_URL", "")
SEARXNG_MAX_RESULTS = _int_env("SEARXNG_MAX_RESULTS", 100)
SEARXNG_TIMEOUT = _int_env("SEARXNG_TIMEOUT", 10)


COOKIE_FILE = ""
COOKIES_FILE = ""


PRIVATE_BOT_MODE = False
PROTECTED_CHAT_IDS = set()
STATS_VID_URL = IOTA_HERO_URL

CMBOT = [
    "💞", "🥂", "🔍", "🧪", "⚡️", "🔥", "🦋", "🎩", "🌈", "🍷",
    "🥃", "🥤", "🕊️", "💌", "🧨", "✨", "💥", "💯", "🌟", "⚡️",
    "❤️", "😍", "🥰", "😘", "😂", "🤣", "😱", "😡", "👏", "🙏",
    "🎉", "🎊", "🎶", "🎵", "🎧", "🎸", "🎹", "🥁", "🎺", "🎷",
    "🔥", "⚡️", "💫", "🌙", "☀️", "🌈", "❄️", "🌸", "🌺", "🌹",
    "🦋", "🕊️", "🐍", "🐯", "🦁", "🐺", "🐉", "🦅", "🦄", "🐎"
]

EFFECT_ID = [
    5046509860389126442,
    5107584321108051014,
    5104841245755180586,
    5159385139981059251,
]
