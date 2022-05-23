import boto3
from concurrent.futures.thread import ThreadPoolExecutor
import json
import os.path
import sys
import redis
import time
import random
import string
import datetime
import signal
import logging
from logzero import logger
import logzero
import settings

requested_to_quit = False


def get_effective_message(message):
    """
    A message might originate from SNS or SQS. If from SNS then it will have a wrapper on it.
    """
    b = json.loads(str(message.body))
    if "Type" in b and b["Type"] == "Notification":
        return json.loads(b["Message"])
    return b

def main():

    logger.info("starting")

    setup_signal_handling()

    global s3
    s3 = boto3.client("s3")

    global sqs
    sqs = boto3.resource("sqs", settings.QUEUE_REGION)

    global redisClient
    redisClient = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB)

    input_queue = sqs.get_queue_by_name(QueueName=settings.INPUT_QUEUE)

    global errorQueue
    errorQueue = sqs.get_queue_by_name(QueueName=settings.ERROR_QUEUE)

    while lifecycle_continues():
        logger.debug("checking for messages")
        messages = input_queue.receive_messages(
            WaitTimeSeconds=10,
            MaxNumberOfMessages=settings.MESSAGES_PER_FETCH)

        if len(messages) > 0:
            logger.info(f"received {len(messages)} messages")
            for message in messages:
                process_message(message)


def lifecycle_continues():
    return not requested_to_quit


def signal_handler(signum, frame):
    logger.info("Caught signal %s" % signum)
    global requested_to_quit
    requested_to_quit = True


def setup_signal_handling():
    logger.debug("setting up signal handling")
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


def process_message(message):
    message_body = message.body
    message_body = get_effective_message(message)

    logger.debug("message type=" + message_body["_type"])

    try:

        if "_type" in message_body and "message" in message_body and "params" in message_body:
            if message_body["message"] == "echo::cache-item":
                cache_item(message_body["params"])
            elif message_body["message"] == "echo::item-access":
                item_access(message_body["params"])
    except Exception as e:
        handle_error(e, message)

    message.delete()


def handle_error(e, message):

    logger.error(f"exception: {e}")

    message_body = get_effective_message(message)
    message_body["exception"] = str(e)

    message.body = str(json.dumps(message_body))
    errorQueue.write(message)


def item_access(payload):
    target = payload["target"]
    logger.info(f"item_access: {target}")
    record_access(target)


def cache_item(payload):
    # "source": "s3://my-bucket/key"
    # "target": "/my-path/key.maybe-extension-too
    # "bucket": "my-bucket"
    # "key": "key"

    bucket = payload["bucket"]
    key = payload["key"]
    target = payload["target"]

    logger.debug(f"cache_item: s3://{bucket}/{key} -> {target}")

    target = settings.CACHE_ROOT + target.decode("utf-8")

    target_path = "/".join(target.split("/")[0:-1])

    try:
        if not os.path.isdir(target_path):
            os.makedirs(target_path)
    except Exception as e:
        pass

    if os.path.exists(target):
        logger.debug("already exists in cache")
    else:
        # synchronisation lock
        # this uses a key in redis, based on the target name
        # if key exists then it will wait for it to be removed up to a timeout
        # then the existence of the file on disk will be checked

        timeout_start = time.time()
        timeout = settings.LOCK_TIMEOUT

        timeout_occurred = True

        # if the flag exists, then loop until timeout for the flag to disappear
        if redisClient.exists(target):
            while time.time() < timeout_start + timeout:
                if redisClient.exists(target):
                    # currently an operation happening for this file
                    time.sleep(0.02)
                else:
                    timeout_occurred = False
                    break

            if timeout_occurred:
                logger.info(f"lock timeout for {target}")

        if not os.path.exists(target):
            # set synchronisation key
            redisClient.setex(target, target, settings.LOCK_TIMEOUT * 2)

            try:
                with open(f"{target}.moving", "wb") as target_output:
                    s3.download_fileobj(bucket, key, target_output)
                logger.debug(f"downloaded {key} -> {target}.moving")
                os.rename(f"{target}.moving", target)
                logger.debug(f"renamed to {target}")
                record_access(target)

            except Exception as e:
                logger.error(f"hit a problem while trying to download {key}: {e}")
                return

            # remove synchronisation key
            redisClient.delete(target)


def record_access(item):
    #print "record_access for " + item
    access_time = int(time.time())
    mapping = {
        item: access_time
    }
    redisClient.zadd("access", mapping)


if __name__ == "__main__":
    if settings.DEBUG:
        logzero.loglevel(logging.DEBUG)
    else:
        logzero.loglevel(logging.INFO)

    main()
