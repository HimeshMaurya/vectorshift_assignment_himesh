import os
# import redis.asyncio as redis
# from kombu.utils.url import safequote

# redis_host = safequote(os.environ.get('REDIS_HOST', 'localhost'))
# redis_client = redis.Redis(host=redis_host, port=6379, db=0)

# async def add_key_value_redis(key, value, expire=None):
#     await redis_client.set(key, value)
#     if expire:
#         await redis_client.expire(key, expire)

# async def get_value_redis(key):
#     return await redis_client.get(key)

# async def delete_key_redis(key):
#     await redis_client.delete(key)
import json

# A simple in-memory store to replace Redis for testing on Windows
MOCK_REDIS_DB = {}

async def add_key_value_redis(key, value, expire=None):
    MOCK_REDIS_DB[key] = value
    return True

async def get_value_redis(key):
    return MOCK_REDIS_DB.get(key)

async def delete_key_redis(key):
    if key in MOCK_REDIS_DB:
        del MOCK_REDIS_DB[key]
    return True