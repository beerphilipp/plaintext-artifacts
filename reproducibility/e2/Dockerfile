FROM alpine:3.20

RUN apk add --no-cache rsync openssh-client bash coreutils

WORKDIR /work

COPY docker_download_apks.sh /usr/local/bin/download_apks.sh
RUN chmod +x /usr/local/bin/download_apks.sh

ENTRYPOINT ["/usr/local/bin/download_apks.sh"]
