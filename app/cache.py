import os
import time
import json
import logging
from typing import Any, Optional, Dict

logger = logging.getLogger("cop31.cache")

# Redis bağlantısı (opsiyonel - .env içinde tanımlanırsa kullanılır)
REDIS_URL = os.getenv("REDIS_URL")
_redis_client = None

if REDIS_URL:
    try:
        import redis
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        _redis_client.ping()
        logger.info("Redis önbellek servisi başarıyla bağlandı.")
    except Exception as e:
        logger.warning(f"Redis bağlantısı kurulamadı, In-Memory önbelleğe geçiliyor: {e}")
        _redis_client = None

# Bellek içi (In-Memory) önbellek deposu
_memory_cache: Dict[str, Dict[str, Any]] = {}

class CacheManager:
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Önbellekten veri okur, süresi dolmuşsa temizler."""
        if _redis_client:
            try:
                val = _redis_client.get(key)
                if val is not None:
                    return json.loads(val)
                return None
            except Exception:
                pass
        
        item = _memory_cache.get(key)
        if not item:
            return None
        if time.time() > item["expires_at"]:
            _memory_cache.pop(key, None)
            return None
        return item["data"]

    @staticmethod
    def set(key: str, value: Any, ttl_seconds: int = 60):
        """Veriyi belirtilen TTL (saniye) süresince önbelleğe kaydeder."""
        if _redis_client:
            try:
                _redis_client.setex(key, ttl_seconds, json.dumps(value, default=str))
                return
            except Exception:
                pass

        _memory_cache[key] = {
            "data": value,
            "expires_at": time.time() + ttl_seconds
        }

    @staticmethod
    def delete(key: str):
        """Tek bir anahtarı önbellekten siler."""
        if _redis_client:
            try:
                _redis_client.delete(key)
            except Exception:
                pass
        _memory_cache.pop(key, None)

    @staticmethod
    def clear_prefix(prefix: str):
        """Belirli bir önek ile başlayan tüm önbellek kayıtlarını geçersiz kılar (invalidation)."""
        if _redis_client:
            try:
                keys = _redis_client.keys(f"{prefix}*")
                if keys:
                    _redis_client.delete(*keys)
            except Exception:
                pass

        keys_to_del = [k for k in _memory_cache if k.startswith(prefix)]
        for k in keys_to_del:
            _memory_cache.pop(k, None)

cache = CacheManager()
