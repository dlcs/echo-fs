# echo-fs

Echo is a highly available NFS rig for Amazon Web Services.

It uses Redis as a backing store to maintain a [Sorted Set](https://redis.io/topics/data-types#sorted-sets) maintaining last accessed time for a given file.

## Scripts

There are 3 different 'modes' that echo-fs can be run in, corresponding to the 3 different entry points:

* Listen - `echo_listener.py`: listens for messages from SNS or SQS. Sets SortedSet score, or copies file from S3->Nas depending on message.
* Populate - `echo_populate.py`: starting from folder walks repo and updates SortedSet to record path and set score = last access time (`atime`).
* Scavenger - `echo_scavenger.py`: if diskspace below threshold get a % of items from SortedSet and delete corresponding file if older than threshold.

## Initially populating Echo

If you want to run Echo on a volume that already has files in it, i.e. that Echo hasn't been made aware of during normal operations, you can populate Echo's Redis with the `echo-populate.py` script.

The following example assumes that you are considering a volume called `scratch`.

Create a Redis instance:

```bash
docker run -d --name echo-redis redis:latest
```

Build the Echo image:

```bash
docker build -t echo-fs .
```

Populate Echo with contents of volume `/scratch`:

```bash
docker run -t -i --name echo-populate --rm \
  -e ECHO_REDIS_HOST="echo-redis" \
  -e ECHO_REDIS_PORT="6379" \
  -e ECHO_REDIS_DB="0" \
  -e ECHO_CACHE_ROOT="/scratch" \
  --link echo-redis:echo-redis \
  -v /scratch:/scratch \
  echo-fs \
  python -u echo_populate.py
```

You can then see if that is working by running the Scavenger in isolation:

```bash
docker run -t -i --name echo-scavenger --rm \
  -e ECHO_REDIS_HOST="echo-redis" \
  -e ECHO_REDIS_PORT="6379" \
  -e ECHO_REDIS_DB="0" \
  -e ECHO_CACHE_ROOT="/scratch" \
  -e ECHO_SCAVENGER_CACHE_THRESHOLD="50" \
  -e ECHO_SCAVENGER_CHUNK_SIZE="2" \
  -e ECHO_SCAVENGER_SLEEP_SECONDS="1" \
  --link echo-redis:echo-redis \
  -v /scratch:/scratch \
  echo-fs \
  python -u echo_scavenger.py
```

### Docker Compose

For ease of running locally the included `docker-compose.yaml` file will run 3 services:

* `echo-redis` latest Redis image. The 2 services below have a dependency on this starting successfully.
* `echo-populate` - Will iterate over `./scratch` and populate redis. Every 60 seconds the populate loop will run.
* `echo-scavenger` - Runs every 10 seconds, will delete anything older than 180seconds when the overall disk has < 50% free space

This can be run via

```bash
docker compose up
```


> [!NOTE]
> This is intended for familiarisation / testing purposes only!