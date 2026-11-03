FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# - build-essential/gcc/python3-dev : needed to compile tgcrypto (C extension)
# - libgl1/libglib2.0-0            : required by opencv-python-headless at runtime
# - ffmpeg/unzip/curl/git/bash     : media tooling + deno bootstrap
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates git bash unzip \
        build-essential gcc g++ python3-dev \
        ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# deno (yt-dlp YouTube signature solving): install at build if reachable,
# but do NOT fail the build if deno.land is blocked — downloader.py also
# auto-installs deno at runtime into /tmp.
RUN curl -fsSL https://deno.land/install.sh | sh -s -- -y || \
    echo "deno build-time install skipped; runtime will fetch it"

ENV PATH="/root/.deno/bin:${PATH}"

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x runner.sh start.sh

CMD ["bash", "start.sh"]
