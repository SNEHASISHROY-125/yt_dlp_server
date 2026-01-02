import os,\
    time,\
    threading
import asyncio
import datetime
from redis_client import redis_client


async def cleanup():
    print("CRON-JOB DAILY CHECK RUNNING")
    cleanup_table = await redis_client.hgetall("FILE-CLEAN-UP")
    ## check for today's clean-up jobs
    for file in cleanup_table.keys():
        expiry = cleanup_table.get(file)
        # check date-match
        today = datetime.datetime.now().strftime("%d%m%Y")
        if today == expiry: 
            os.remove(file) if os.path.exists(file) else print("CRON-JOB:FILE-DELETE FILE DOESNT EXIST: " , file)



async def start_cleanup_cron_job():
    def _cron_worker():
        while True:
            time.sleep(10)
            CRON_TIME = os.getenv("CRON_TIME","0230")   # 02:30 AM
            if datetime.datetime.now().strftime("%H%M") == CRON_TIME :
                asyncio.run(cleanup())

    threading.Thread(target=_cron_worker,daemon=True).start()
