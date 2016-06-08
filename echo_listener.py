from multiprocessing import Pool
import echo_listener_settings as settings
from boto import sqs
from boto.sqs.message import RawMessage, MHMessage
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import json
import os.path

class AgnosticMessage(MHMessage):
	"""
	A message might originate from SNS or SQS. If from SNS then it will have a wrapper on it.
	"""
	
	def get_effective_message(self):
		if 'Type' in self and self['Type'] == "Notification":
			return json.loads(str(self['Message']))
		return self

def main():
	global s3Connection
	s3Connection = S3Connection()
	
	input_queue = get_input_queue()

	input_queue.set_message_class(AgnosticMessage)
	
	num_pool_workers = settings.NUM_POOL_WORKERS
	messages_per_fetch = settings.MESSAGES_PER_FETCH

	pool = Pool(num_pool_workers, initargs=())

	try:
		while True:
			messages = input_queue.get_messages(num_messages=messages_per_fetch, visibility_timeout=120, wait_time_seconds=20)
			if len(messages) > 0:
				pool.map(process_message, messages)
	except:
		print "Error getting messages"

def process_message(message):
	message_body = json.loads(str(message.get_effective_message()))

	if '_type' in message_body and 'message' in message_body and 'params' in message_body:
		if message_body['message'] == "echo::cache-item":
			cache_item(message_body['params'])

	message.delete()

def cache_item(payload):
	# "source": "s3://my-bucket/key"
	# "target": "/my-path/key.maybe-extension-too
	# "bucket": "my-bucket"
	# "key": "key"
	
	print "received request to cache " + payload['bucket'] + '/' + payload['key'] + ' to ' + payload['target']

	k = Key(payload['bucket'])
	k.key = payload['key']
	
	target = settings.CACHE_ROOT + payload['target']
	
	if os.path.exists(target):
		print "already exists in cache"
	else:
		print "downloading from s3"
		k.get_contents_to_filename(target)

def get_input_queue():
	conn = sqs.connect_to_region(settings.SQS_REGION)
	queue = conn.get_queue(settings.INPUT_QUEUE)
	return queue

if __name__ == "__main__":
	main()