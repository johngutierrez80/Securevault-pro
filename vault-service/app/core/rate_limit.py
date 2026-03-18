from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared limiter instance used by app and route decorators.
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://redis:6379")
