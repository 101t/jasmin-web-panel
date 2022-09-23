FROM python:3.8-slim-buster

RUN apt update && apt install telnet

RUN apt install -y git build-essential libpq-dev postgresql-client postgresql-client-common python3-psycopg2

RUN adduser --home /jasmin --system --group jasmin

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV JASMIN_HOME=/jasmin
#ENV PATH=$PATH:/usr/local/bin

WORKDIR $JASMIN_HOME

RUN mkdir -p $JASMIN_HOME/public/media && \
    mkdir -p $JASMIN_HOME/public/static

COPY --chown=jasmin:jasmin ./requirements.txt $JASMIN_HOME/requirements.txt

USER jasmin

RUN pip install -U pip && pip install -r requirements.txt

COPY --chown=jasmin:jasmin . $JASMIN_HOME

COPY --chown=jasmin:jasmin ./docker-entrypoint.sh $JASMIN_HOME
COPY --chown=jasmin:jasmin ./docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
#RUN ln -s docker-entrypoint.sh /usr/local/bin
#RUN chmod +x docker-entrypoint.sh
# RUN chown -R jasmin:jasmin $JASMIN_HOME/

