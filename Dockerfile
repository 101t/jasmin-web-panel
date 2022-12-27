FROM python:3.11

RUN apt-get update && apt-get install telnet

RUN apt-get install -y libpq-dev postgresql-client python3-psycopg2

RUN adduser --home /jasmin --system --group jasmin

ENV JASMIN_HOME=/jasmin
ENV JASMIN_PORT=8000

WORKDIR $JASMIN_HOME

# USER jasmin

RUN mkdir -p $JASMIN_HOME/public/media && \
    mkdir -p $JASMIN_HOME/public/static

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . .

# ENTRYPOINT [ "./docker-entrypoint.sh" ]

CMD ["./docker-entrypoint.sh"]
