from redis import Redis, ConnectionPool

from settings import redis_config

pool = ConnectionPool(host=redis_config['host'], port=redis_config['port'], db=0)


def get_client() -> Redis:
    global pool
    return Redis(connection_pool=pool)
