from contextlib import asynccontextmanager
from fastapi import FastAPI, Header , BackgroundTasks, HTTPException , Depends
from fastapi.responses import FileResponse
from fastapi.responses import FileResponse
import uuid, json, os

from downloader import fetch_metadata, download_audio

from utils import new_token , url_hash
from redis_client import redis_client
from downloader import fetch_metadata
from cleanup import start_cleanup_cron_job
from token_generator import gen_token_32
import asyncio , time
import secrets

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not await redis_client.hgetall("API_KEYS"):
        gen_key = await gen_token_32()
        ADMIN_KEY = os.getenv("ADMIN_KEY",gen_key)
        await redis_client.hset(
            "API_KEYS",
            mapping={ADMIN_KEY : "ADMIN"}
        ) ; print("ADMIN KEY SET TO : ",ADMIN_KEY)
    await start_cleanup_cron_job()
    print("starting cron...")
    yield

app = FastAPI(lifespan=lifespan)

# JOBS_FILE = "storage/jobs.json"
DOWNLOAD_DIR = "storage/downloads"

os.chmod("notify.sh", 0o755)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def verify_key(x_api_key: str = Header(...)):
    if x_api_key not in await redis_client.hgetall("API_KEYS"):
        raise HTTPException(403)
    return x_api_key

@app.post("/api/v1/jobs")
async def create_job(url: str, x_api_key:str=Depends(verify_key) , no_cache:bool=False):
    token = new_token()
    now = int(time.time())

    try:
        #TODO: start download
        # starts through fetch_audio
        info = await fetch_metadata(url)
        hashed_url = url_hash(url)
        # check for cached:
        if not no_cache and (existing_token := await redis_client.hgetall(hashed_url)):
            _ = await redis_client.hgetall(f"job:{existing_token.get('token')}")
            return {
            "token": existing_token.get("token"),
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "status": _.get("status"),
            "download_url": f"/download/{existing_token.get('token')}"
        }

        await redis_client.hset(
            f"job:{token}",
            mapping={
                "url": url,
                "status": "pending",
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "created_at": now,
            }
        )
        await redis_client.expire(f"job:{token}", 86400)

        await redis_client.hset(
            hashed_url,
            mapping={
                "token": token,
            }
        )
        await redis_client.expire(hashed_url, 86400)

        return {
            "token": token,
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "status": "pending",
            "download_url": f"/download/{token}"
        }

    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/fetch_audio/{token}")
async def fetch_audio(token: str, bg: BackgroundTasks):
    key = f"job:{token}" ; print("keyyyy: ",key)
    job = await redis_client.hgetall(key)   ## thread blocking { blocks for a while }
    print("keyyyy done")

    if not job:
        return {"error": "invalid token"}

    status = job["status"]

    if status == "pending":
        bg.add_task(download_audio, token)
        return {"status": "queued"}

    if status == "downloading":
        return {"status": "downloading"}

    if status == "completed":
        return {
            "status": "completed",
            "download_url": f"/download/{token}"
        }

    if status == "error":
        return {"status": "error", "message": job.get("error")}



@app.get("/api/v1/download/{token}")
async def download(token: str):
    job = await redis_client.hgetall(f"job:{token}")
    if not job or job["status"] != "completed":
        return {"error": "not ready"}

    return FileResponse(job["audio_path"], media_type="audio/mpeg")

