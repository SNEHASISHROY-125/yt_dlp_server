import subprocess, json, os
# from jobs import load_jobs, save_jobs
from utils import url_hash
import asyncio
import datetime as dt

DOWNLOAD_DIR = "storage/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

DELETE_FILE_AFTER_DAYS = os.getenv("DELETE_FILE_AFTER_DAYS", 7)

from redis_client import redis_client

async def fetch_metadata(url):
    cmd = [
        "./yt-dlp_linux",
        "--dump-json",
        "--skip-download",
        "--no-playlist",
        url
    ]
    proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    stdout, stderr = await proc.communicate()
    # print(stdout.decode(), stderr.decode())
    if proc.returncode != 0:
        raise Exception(f"yt-dlp failed: {stderr.decode()}")
    
    data = json.loads(stdout)

    return {
        "title": data.get("title"),
        "duration": data.get("duration"),
        "thumbnail": data.get("thumbnail")
    }

async def download_audio(token:str):
    key = f"job:{token}"
    job = await redis_client.hgetall(key)
    if not job: return
    # change status
    await redis_client.hset(key, "status", "downloading")

    url = job["url"]
    ## HASH
    url_hashed = url_hash(url)

    ## File Expiry | 7 Days
    expiry = (dt.datetime.now() + dt.timedelta(days=int(DELETE_FILE_AFTER_DAYS))).strftime("%d%m%Y")
    outtmpl = os.path.join(DOWNLOAD_DIR, f"%(title)s.%(ext)s")

    cmd = [
        "./yt-dlp_linux",
        "-f", "ba",
        "-q",
        "-x", "--audio-quality", "0",
        "--embed-thumbnail", 
        # "--extract-audio",
        # "--audio-format", "m4a",
        "--embed-metadata",
        "--convert-thumbnails", "jpg",
        # "--remote-components", "ejs:github",
        # "--list-formats",
        "--restrict-filenames",
        "-N", "8",
        "-o", outtmpl,
        "--exec", f"after_move:/bin/bash notify.sh {token} {url_hashed} %(filepath)q {expiry}",
        # job["url"]
        url,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        print(stdout.decode(), stderr.decode())
        if proc.returncode != 0:
            raise Exception(f"yt-dlp failed: {stderr.decode()}")

    except Exception as e: 
        print(e)
        await redis_client.hset(
            key,
            mapping={
                "status": "error",
                "error": str(e)
            }
        )

