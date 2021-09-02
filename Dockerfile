FROM alpine:3.14

RUN apk add --update --no-cache --virtual=run-deps \
  python3 \
  py3-pip \
  ca-certificates \
  curl \
  && rm -rf /var/cache/apk/*

RUN mkdir -p /opt/echo-fs
WORKDIR /opt/echo-fs

COPY requirements.txt /opt/echo-fs/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY run_with_local_redis_on_ec2.sh /opt/echo-fs
RUN chmod +x /opt/echo-fs/run_with_local_redis_on_ec2.sh

COPY app /opt/echo-fs
