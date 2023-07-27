FROM alpine:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV JASMIN_HOME=/jasmin
ENV PATH="${PATH}:/jasmin"

# RUN mkdir /jasmin
RUN addgroup -S jasmin && adduser -S jasmin -G jasmin -h $JASMIN_HOME

#RUN apk del busybox-extras
RUN apk --update --no-cache upgrade
RUN apk add python3 --repository=http://dl-cdn.alpinelinux.org/alpine/v3.11/main && ln -sf python3 /usr/bin/python
# RUN apk search busybox-extras
RUN apk add busybox-extras
# RUN busybox --list
# RUN apk add --no-cache bash curl nmap apache2-utils bind-tools tcpdump mtr iperf3 strace tree busybox-extras netcat-openbsd
RUN echo alias telnet='busybox-extras telnet' >> .bashrc
RUN telnet google.com 80

RUN apk add --update build-base git gcc cmake py3-setuptools py3-pip python3-dev bash

# RUN apk add --no-cache bash

WORKDIR $JASMIN_HOME

USER jasmin

RUN mkdir -p $JASMIN_HOME/public/media
RUN mkdir -p $JASMIN_HOME/public/static

# RUN chown -R jasmin:jasmin $JASMIN_HOME/

COPY --chown=jasmin:jasmin ./requirements.txt $JASMIN_HOME/requirements.txt

ENV PATH="${PATH}:/jasmin/.local/bin"

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

COPY --chown=jasmin:jasmin . $JASMIN_HOME

COPY --chown=jasmin:jasmin ./docker-entrypoint.sh docker-entrypoint.sh

# RUN chown -R jasmin:jasmin $JASMIN_HOME/

# USER root

ENTRYPOINT ["docker-entrypoint.sh"]