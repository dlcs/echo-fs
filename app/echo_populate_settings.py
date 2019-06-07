import os
import distutils.util

DEBUG = bool(distutils.util.strtobool(os.environ.get("DEBUG", default="False")))

REDIS_HOST = os.environ.get('ECHO_REDIS_HOST')
REDIS_PORT = int(os.environ.get('ECHO_REDIS_PORT'))
REDIS_DB = int(os.environ.get('ECHO_REDIS_DB'))
CACHE_ROOT = os.environ.get('ECHO_CACHE_ROOT')
