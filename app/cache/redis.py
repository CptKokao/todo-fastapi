from redis import Redis
import json

class RedisCache:
	def __init__(self, redis_url: str, cache_ttl: int | None = None):
		self.redis = Redis.from_url(redis_url ) 
		self.cache_ttl_seconds = cache_ttl

	def set(self, key: str, value: dict | list) -> None:
		self.redis.set(key, json.dumps(value, ensure_ascii=False), ex=self.cache_ttl_seconds)
	
	def get(self, key: str) -> dict | list | None:
		raw = self.redis.get(key)
		return json.loads(raw) if raw is not None else None

	def delete(self, key: str) -> None:
		self.redis.delete(key)
	
