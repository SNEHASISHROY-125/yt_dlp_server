FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y \
    ffmpeg \
    ca-certificates \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# deno binary
# RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux \
#     -o /usr/local/bin/yt-dlp \
#     && chmod +x /usr/local/bin/yt-dlp
RUN cd /tmp \
 && curl -Lo "deno.zip" "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip" \
 && unzip -d /usr/local/bin /tmp/deno.zip

RUN apt-get update \
 && apt-get install -y --no-install-recommends redis-tools \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

RUN mkdir -p /app/storage

RUN chmod +x /app/yt-dlp_linux

EXPOSE 8890

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8890"]
