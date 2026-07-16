"""
Token-Bucket Rate Limiter. Uses a Lua script so the read-check-write cycle
is atomic on the Redis server - safe under concurrent requests from many
workers, unlike a naive GET-then-SET counter.
"""
import time
from functools import lru_cache
import redis
from fastapi import Request, HTTPException
from config.settings import settings

_TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call("HMGET", key, "tokens", "timestamp")
local tokens = tonumber(bucket[1])
local timestamp = tonumber(bucket[2])

if tokens == nil then
    tokens = capacity
    timestamp = now
end

local delta = math.max(0, now - timestamp)
tokens = math.min(capacity, tokens + delta * refill_rate)

local allowed = 0
if tokens >= 1 then
    tokens = tokens - 1
    allowed = 1
end

redis.call("HMSET", key, "tokens", tokens, "timestamp", now)
redis.call("EXPIRE", key, 3600)

return allowed
"""


@lru_cache(maxsize=1)
def _get_redis_client():
    return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)


@lru_cache(maxsize=1)
def _get_script():
    return _get_redis_client().register_script(_TOKEN_BUCKET_LUA)


def check_rate_limit(identifier: str) -> None:
    capacity = settings.RATE_LIMIT_REQUESTS
    refill_rate = capacity / settings.RATE_LIMIT_WINDOW_SECONDS
    allowed = _get_script()(keys=[f"ratelimit:{identifier}"], args=[capacity, refill_rate, time.time()])
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please slow down.")


async def rate_limit_dependency(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)
