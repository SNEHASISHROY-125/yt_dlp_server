from contextlib import asynccontextmanager
from redis_client import redis_client
from secrets import token_hex

@asynccontextmanager
async def gen(token_length:int):
    yield token_hex(token_length)


async def gen_token_32():
    async with gen(32) as token:
        return token
