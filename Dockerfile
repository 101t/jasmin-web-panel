FROM python:3.8-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/jasmin:${PATH}"
ENV JASMIN_HOME=/jasmin

# RUN mkdir /jasmin

RUN addgroup -S jasmin && adduser -S jasmin -G jasmin -h $JASMIN_HOME

#RUN apk del busybox-extras
RUN apk update && apk add busybox-extras
RUN apk add build-base git gcc cmake py3-setuptools
RUN busybox-extras --list
RUN apk add --no-cache bash



WORKDIR $JASMIN_HOME

RUN mkdir -p $JASMIN_HOME/public/media
RUN mkdir -p $JASMIN_HOME/public/static

# RUN chown -R jasmin:jasmin $JASMIN_HOME/

COPY ./requirements.txt $JASMIN_HOME/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# RUN export PATH="/usr/local/bin:$HOME/.local/bin::$PATH"

COPY . $JASMIN_HOME

COPY ./docker-entrypoint.sh docker-entrypoint.sh

#RUN chmod -R u+x ${JASMIN_HOME} && \
#    chgrp -R 0 ${JASMIN_HOME} && \
#    chmod -R g=u ${JASMIN_HOME}

RUN chown -R jasmin:jasmin $JASMIN_HOME/

USER jasmin

ENTRYPOINT ["docker-entrypoint.sh"]