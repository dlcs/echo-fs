import os

# See: https://github.com/python/cpython/blob/v3.11.2/Lib/distutils/util.py#L308
def strtobool(val) -> bool:
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))

DEBUG = strtobool(os.environ.get("DEBUG", default="False"))

REDIS_HOST = os.environ.get('ECHO_REDIS_HOST')
REDIS_PORT = int(os.environ.get('ECHO_REDIS_PORT'))
REDIS_DB = int(os.environ.get('ECHO_REDIS_DB'))
CACHE_ROOT = os.environ.get('ECHO_CACHE_ROOT')

CACHE_FREE = int(os.environ.get('ECHO_SCAVENGER_CACHE_THRESHOLD', default="50"))
CHUNK_SIZE = int(os.environ.get('ECHO_SCAVENGER_CHUNK_SIZE', default="10"))

NUM_POOL_WORKERS = 5
MESSAGES_PER_FETCH = 10
LOCK_TIMEOUT = 5

QUEUE_REGION = os.environ.get('ECHO_QUEUE_REGION')
INPUT_QUEUE = os.environ.get('ECHO_INPUT_QUEUE')
ERROR_QUEUE = os.environ.get('ECHO_ERROR_QUEUE')
SCAVENGER_SLEEP_SECONDS = int(os.environ.get('ECHO_SCAVENGER_SLEEP_SECONDS', default="30"))
SCAVENGER_MIN_AGE_SECONDS = int(os.environ.get('ECHO_SCAVENGER_MIN_AGE_SECONDS', default="0"))

POPULATE_CACHE_FREE = int(os.environ.get('ECHO_POPULATE_CACHE_THRESHOLD', default="60"))
POPULATE_LOOP = strtobool(os.environ.get("ECHO_POPULATE_LOOP", default="False"))
POPULATE_SLEEP_SECONDS = int(os.environ.get("ECHO_POPULATE_SLEEP_SECONDS", default="300"))
