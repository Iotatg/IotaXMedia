# IotaXMedia

Repository: https://github.com/Iotatg/IotaXMedia

A Telegram music and video streaming bot for group voice chats. IotaXMedia is a
fork of LotaXMedia that adds clone-bot support and cookieless YouTube downloads
through `yt-dlp` and Deno.

- Streaming engine: Pyrogram + PyTgCalls
- Downloads: `yt-dlp` with Deno JS solving and an external API fallback
- Clone mode: let users spin up their own branded bot instance

## Features

- High-quality audio and video playback in group voice chats
- Cookieless YouTube downloads (no cookie file required)
- Clone bot support with per-clone customization
- Inline play-button controls for playback, seek, loop and autoplay
- Queue management, playlists, shuffle and skip
- Admin controls, authorization, broadcast and activity logging
- Multi-language user interface
- Deploy on Docker, Heroku, Render, Koyeb, Railway or any VPS

## Requirements

- Python 3.11 or newer
- MongoDB database
- `API_ID` and `API_HASH` from https://my.telegram.org
- A bot token from [@BotFather](https://t.me/BotFather)
- Optional: a Pyrogram `STRING_SESSION` for the assistant account used for
  voice chat playback
- FFmpeg available on `PATH`

## Quick start (local)

```bash
# Clone the repository
git clone https://github.com/Iotatg/IotaXMedia.git
cd IotaXMedia

# Install Python dependencies
pip install -r requirements.txt

# Create your environment file
cp .env.example .env

# Edit .env and set at least API_ID, API_HASH, BOT_TOKEN and MONGO_DB_URI

# Start the bot
bash start.sh
```

## Environment variables

All variables live in `.env` and are documented in `.env.example`. The most
important ones:

| Variable | Required | Description |
| --- | --- | --- |
| `API_ID` | Yes | Telegram API ID from https://my.telegram.org |
| `API_HASH` | Yes | Telegram API hash from https://my.telegram.org |
| `BOT_TOKEN` | Yes | Bot token from @BotFather |
| `MONGO_DB_URI` | Yes | MongoDB connection string |
| `OWNER_ID` | Yes | Numeric Telegram user ID of the owner |
| `STRING_SESSION` | No | Assistant session used for voice chat playback |
| `LOGGER_ID` | No | Group/channel ID for activity logs |
| `CLONE_MODE` | No | `1` to enable clone bots, `0` to disable |
| `COOKIE_URL` / `COOKIE_B64` | No | Optional YouTube cookies for blocked videos |
| `API_URL` | No | Local YouTube download API endpoint |

See `.env.example` for the complete, commented list.

## Deployment

- **Docker / VPS**: `docker build -t iotaxmedia . && docker run --env-file .env iotaxmedia`
- **Heroku**: uses the container stack via `heroku.yml` and `Dockerfile`
- **Render**: deploy the `render.yaml` blueprint
- **Koyeb / Railway / Fly.io**: choose the Dockerfile build and run `bash runner.sh`

See `Deploy.md` for detailed per-platform instructions.

## Commands

| Command | Description |
| --- | --- |
| `/play <query>` | Play a requested song or video |
| `/song <query>` | Download a song as an audio file |
| `/pause` | Pause the current stream |
| `/resume` | Resume the paused stream |
| `/skip` | Skip to the next track in the queue |
| `/stop` | Stop playback and clear the queue |
| `/queue` | Show the current queue |
| `/ping` | Check bot latency and system stats |
| `/settings` | Open the group settings panel |
| `/lang` | Change the interface language |
| `/clone` | Create your own clone bot |
| `/help` | Show the full command help |

Some commands require the bot to be an administrator in the chat.

## Project layout

```text
IotaXMedia/        Python package with all bot code
config.py          Configuration loader (reads .env)
wrapper.py         Entry point: `python wrapper.py`
runner.sh/start.sh Local and Heroku-style launchers
Dockerfile         Container image (runs wrapper.py)
Procfile           Heroku process definition
requirements.txt   Python dependencies
.env.example       Environment variable template
```

`wrapper.py` inserts the repository root into `sys.path` and then imports the
`IotaXMedia` package, so a flat `python wrapper.py` works from the repo root.

## License

Released under the MIT License. See `LICENSE`.

Copyright (c) 2025-2026 Iota Coders.

## Credits

Maintained by Iota Coders. Based on LotaXMedia and the Pyrogram / PyTgCalls
ecosystem.
