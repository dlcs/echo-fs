import os.path
import sys
import redis
import time
import string
import datetime
import signal
import logging
from logzero import logger
import logzero
import settings

requested_to_quit = False


def main():
    logger.info("starting")

    setup_signal_handling()

    keep_running = True

    while keep_running:
        global redisClient
        logger.info(f"redis client will connect to {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
        redisClient = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

        for path, _, files in os.walk(settings.CACHE_ROOT):
            if not lifecycle_continues():
                break

            for filename in files:
                if not lifecycle_continues():
                    break

                full_path_name = os.path.join(path, filename)
                unix_timestamp = os.path.getmtime(full_path_name)

                access_time = int(unix_timestamp)
                adding_name = full_path_name[len(settings.CACHE_ROOT):]

                # if redisClient.zscore("access", adding_name) is None:
                logger.info(f"adding {full_path_name} as {adding_name}: {access_time}")
                mapping = {
                    adding_name: access_time
                }
                redisClient.zadd("access", mapping)

        redisClient.close()

        keep_running = settings.POPULATE_LOOP
        if keep_running:
            logger.info(f"sleeping for {settings.POPULATE_SLEEP_SECONDS} second(s)")
            time.sleep(int(settings.POPULATE_SLEEP_SECONDS))

    logger.info("finished")

    exit(0)


def lifecycle_continues():
    return not requested_to_quit


def signal_handler(signum, frame):
    logger.info("Caught signal %s" % signum)
    global requested_to_quit
    requested_to_quit = True


def setup_signal_handling():
    logger.info("setting up signal handling")
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    if settings.DEBUG:
        logzero.loglevel(logging.DEBUG)
    else:
        logzero.loglevel(logging.INFO)

    main()
