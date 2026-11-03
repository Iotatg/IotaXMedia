# IotaXMedia — Deployment Guide (All Hosting Platforms)

This guide covers how to deploy the IotaXMedia music bot on every supported
free/paid platform. The bot is a long-running Telegram bot with an optional
health web server used for platform keep-alive.

---

## 0. What the bot needs (applies to ALL platforms)

| Requirement | Why | How it's provided |
|---|---|---|
| **Python 3.11** | `pyrogram==2.0.106` breaks on Python 3.12+ | `runtime.txt`, Nix `python311`, Docker `python:3.11-slim` |
| **deno** (JS runtime) | `yt-dlp` must solve YouTube signature challenges or downloads fail with *"Requested format is not available"* | Auto-installed at build (Docker/build.sh/Replit Nix) **and** at runtime into `/tmp` by `downloader.py` |
| **ffmpeg** | Merging `bestvideo+bestaudio` for `/video` downloads | Installed via apt / Nix / Dockerfile |
| **Writable storage** | Downloads/thumbnails/cache | Uses `/tmp/...` on read-only slugs (Render); fully writable on Replit/Railway/Fly |
| **`$PORT` health server** | Platform health checks & free-tier keep-alive | `keep_alive` binds `$PORT` (default `10000`); serves `/` and `/health` |

### Mandatory environment variables / secrets

Set these on **every** platform (as env vars or secret files):

| Var | Description |
|---|---|
| `API_ID` | Telegram API ID (my.telegram.org) |
| `API_HASH` | Telegram API hash |
| `BOT_TOKEN` | @BotFather bot token |
| `OWNER_ID` | Your Telegram user ID |
| `MONGO_DB_URI` | MongoDB connection string |
| `STRING_SESSION` | (optional) Pyrogram user session for VC music |
| `LOGGER_ID` | (optional) channel/group ID for logs |
| `YTPROXY_URL` | (optional) YouTube proxy |
| `COOKIES_FILE` / `COOKIE_FILE` | (optional) path to Netscape cookie file |

**Cookies (age-restricted/premium content):** upload your `cookies.txt` as a
**Secret File** mounted at `/etc/secrets/cookies.txt`. The bot auto-detects it,
copies it to a writable temp file (the mount is read-only), and passes that to
`yt-dlp`.

---

## 1. Replit

**Config files:** `.replit`, `replit.nix`

1. Import the GitHub repo into Replit.
2. Replit reads `replit.nix` and installs `python311`, `deno`, `ffmpeg`, `nodejs_20`.
3. Press **Run** (runs `bash start.sh` → bot with auto-restart loop).
4. For a public deployment: **Deploy** → Replit uses `.replit`'s run command
   and binds `$PORT` (set to `10000` in `.replit`).

**Free-tier note:** Replit workspace runs while the tab/session is active.
Deployments may require a paid plan; for 24/7 use a paid Replit plan or another
host below.

**Keep-alive:** set `KEEPALIVE_URL` = your `.replit.app` URL so the external
self-ping keeps it awake (localhost ping alone won't prevent sleep).

---

## 2. Render

**Config files:** `render.yaml`, `build.sh`, `runtime.txt`

**Option A — via Dashboard (recommended):**
1. New → **Web Service** (or **Background Worker** for 24/7 without a URL).
2. Connect the GitHub repo.
3. **Build Command:** `bash build.sh`  (installs deps + deno + ffmpeg)
4. **Start Command:** `bash start.sh`
5. **Python Version:** `3.11` (also pinned in `runtime.txt`).
6. Add the env vars from section 0.
7. Deploy.

**Option B — via `render.yaml` (Infrastructure as Code):** push the file;
Render reads `type: worker`, `buildCommand: bash build.sh`,
`startCommand: bash start.sh`, and the listed env vars.

**Keep-alive:** Render auto-injects `RENDER_EXTERNAL_URL`; `keep_alive` pings it
every 5 min → free Web Services never spin down.

**Troubleshooting:** if a deploy shows *"Failed to build"*, ensure Build Command
is `bash build.sh` (not just `pip install`), and Python is 3.11.

---

## 3. Railway

**Config files:** `railway.json`, `nixpacks.toml`, `Dockerfile`, `build.sh`

Railway can build two ways — pick one in the dashboard (**Settings → Service →
Builder**):

**A) Docker (default if a Dockerfile exists):**
- Builder: **Dockerfile**. Railway runs `docker build` (now includes `gcc` for
  `tgcrypto`, `libgl` for opencv, `ffmpeg`). Start command: `bash start.sh`.
- If the build fails with *"Failed to build an image"*, it's almost always the
  missing C compiler for `tgcrypto` — already fixed in the Dockerfile.

**B) Nixpacks (uses `railway.json` + `build.sh`):**
- Builder: **Nixpacks**. `nixpacks.toml` adds `gcc`, `ffmpeg`, `deno`;
  `build.sh` installs Python deps + deno + ffmpeg; start `bash start.sh`.
- Set **Healthcheck Path** `/health` (bot serves it on `$PORT`).

**Keep-alive:** set `KEEPALIVE_URL` = your `*.railway.app` URL (Railway does not
inject `RENDER_EXTERNAL_URL`).

**Free-tier note:** ~$5 trial credit; watch egress (downloads count).

---

## 4. Fly.io

**Config files:** `fly.toml`, `Dockerfile`

1. `fly auth login` then `fly launch` (uses `fly.toml` + `Dockerfile`).
2. Set secrets: `fly secrets set API_ID=... API_HASH=... BOT_TOKEN=... ...`.
3. `fly deploy`.

The Dockerfile installs Python 3.11, deno, ffmpeg, build tools. `fly.toml`
exposes port `10000` (the health server) and keeps the machine running
(`min_machines_running = 1`).

**Free-tier note:** limited hours/GB-month; fine for light use.

---

## 5. Koyeb (and any Docker host)

**Config files:** `Dockerfile`

1. New Service → **Build from GitHub** → use the **Dockerfile**.
2. Run command: `bash start.sh`.
3. Expose / map port `10000`.
4. Add env vars / secret files (cookies at `/etc/secrets/cookies.txt`).

Koyeb runs the container; the Dockerfile provisions everything. For 24/7 set the
instance to always-on (paid) or use the free tier's limits.

---

## 6. Heroku (legacy)

**Config file:** `Procfile` (`worker: bash start.sh`)

Heroku's free tier is discontinued, but paid dynos work:
```
heroku create
heroku config:set API_ID=... API_HASH=... BOT_TOKEN=... OWNER_ID=... MONGO_DB_URI=...
git push heroku main
heroku ps:scale worker=1
```

---

## 7. Any VPS / self-host (Docker)

```bash
docker build -t iotaxmedia .
docker run -d --name iota \
  -e API_ID=... -e API_HASH=... -e BOT_TOKEN=... \
  -e OWNER_ID=... -e MONGO_DB_URI=... \
  -v $(pwd)/cookies.txt:/etc/secrets/cookies.txt:ro \
  -p 10000:10000 iotaxmedia
```
Or without Docker: `pip install -r requirements.txt && bash start.sh`
(ensure `deno` + `ffmpeg` are installed; `start.sh` loops on crash).

---

## 8. 24/7 keep-alive (free tiers)

The bot self-pings to avoid idle spin-downs:

- **Local ping:** `127.0.0.1:$PORT/health` every 120s (proves liveness).
- **External ping:** your **public URL** `/health` every 300s — *this* is what
  actually prevents sleep.
  - Render: automatic via `RENDER_EXTERNAL_URL`.
  - **Railway / Fly / Koyeb / Replit:** set env `KEEPALIVE_URL=https://your-app.url`.
    (`WEBAPP_BASE_URL` / `PUBLIC_URL` also accepted.)
- You can ALSO point an external monitor (UptimeRobot) at `/health`.

---

## 8.5 deployctl — manage every hoster from your terminal

`deployctl` (repo root) drives Railway / Render / Fly / Koyeb through their
**official CLIs / REST APIs** with your own tokens — deploy, status, logs,
restart, env vars and console from one place. No tunnels, no backdoors.

```bash
./deployctl.sh init              # creates deployctl/config.env (gitignored)
./deployctl.sh doctor            # shows which CLIs/tokens are ready
./deployctl.sh deploy railway --from=main   # rebuild main (fixes stale builds)
./deployctl.sh status render     # recent deploys
./deployctl.sh logs render       # tail recent logs
./deployctl.sh restart fly       # restart a service
./deployctl.sh env koyeb set MONGO_DB_URI=... 
./deployctl.sh all status        # run a command on every platform
./deployctl.sh watch logs railway --every=15
```

Tokens needed in `deployctl/config.env`:
`RAILWAY_TOKEN` (`railway login && railway token`), `RENDER_API_KEY`
(Dashboard → Account → API keys), `FLY_API_TOKEN` (fly.io → Personal Access
Tokens), `KOYEB_TOKEN` (app.koyeb.com → Account → API). Render also needs
`RENDER_SERVICE_ID` (the `srv-...` uuid). See `deployctl/README.md`.

---

## 9. Troubleshooting quick reference

| Symptom | Cause | Fix |
|---|---|---|
| Build fails: *"Failed to build an image"* (Docker) | `python:3.11-slim` lacks `gcc`; `tgcrypto` can't compile | Use updated Dockerfile (adds `build-essential`, `python3-dev`) |
| `ImportError` / opencv crash at runtime | missing `libgl1` | Dockerfile now installs `libgl1 libglib2.0-0` |
| `FAILED to download song — Requested format is not available` | no JS runtime → YouTube signature solving fails | deno auto-installs (build + runtime); check logs for `Auto-installing deno` |
| `Permission denied: '/workspace'` | hardcoded read-only path | fixed: runtime dirs → `/tmp`; `yt_api_server` → writable dir |
| `Signature solving failed` warnings | deno not present | ensure deno installed (see above); verify `deno --version` |
| Bot sleeps / stops on free tier | idle spin-down | set `KEEPALIVE_URL`; use external monitor |
| `PyTgCalls ... InputGroupCallSlug` | pyrogram/pytgcalls version mismatch (VC only) | unrelated to downloads; VC music may be limited |

---

## 10. File map

| File | Platform(s) |
|---|---|
| `.replit`, `replit.nix` | Replit |
| `render.yaml`, `build.sh`, `runtime.txt` | Render |
| `railway.json`, `nixpacks.toml` | Railway |
| `fly.toml` | Fly.io |
| `Dockerfile` | Koyeb / Fly / Railway-Docker / VPS |
| `Procfile` | Heroku |
| `start.sh`, `runner.sh`, `wrapper.py` | entrypoints (all) |
| `IotaXMedia/utils/keep_alive.py` | health server + self-ping (all) |
| `IotaXMedia/utils/downloader.py` | deno auto-install + yt-dlp (all) |
