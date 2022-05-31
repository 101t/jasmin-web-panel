FROM python:3.8

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/web:${PATH}"
ENV JASMIN_HOME=/web

RUN mkdir /web

WORKDIR $JASMIN_HOME

RUN mkdir -p $JASMIN_HOME/public/media
RUN mkdir -p $JASMIN_HOME/public/static

COPY ./requirements.txt $JASMIN_HOME/requirements.txt

RUN pip install -r requirements.txt

COPY . $JASMIN_HOME

COPY ./docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]