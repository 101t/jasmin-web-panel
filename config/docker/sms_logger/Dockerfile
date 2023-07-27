FROM python:3.11-slim

# disable debian interactive
ARG DEBIAN_FRONTEND=noninteractive
# suppress pip upgrade warning
ARG PIP_DISABLE_PIP_VERSION_CHECK=1
# disable cache directory, image size 2.1GB to 1.9GB
ARG PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get -y upgrade

RUN apt-get install --no-install-recommends -y  \
    python3-dev python3-wheel python3-setuptools virtualenv \
    build-essential gcc curl \
    libpq-dev libpq5 telnet

RUN apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

# --------------------------------------
ENV APP_DIR=/app
ENV APP_USER=app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

RUN useradd -m -d ${APP_DIR} -U -r -s /bin/bash ${APP_USER}

USER ${APP_USER}

WORKDIR ${APP_DIR}

# Create the virtual environment
RUN python -m venv /app/env
# Activate the virtual environment
ENV PATH="$APP_DIR/env/bin:$PATH"

COPY config/docker/sms_logger/requirements.txt requirements.txt

RUN pip install -U pip wheel

RUN pip install -r requirements.txt

COPY --chown=$APP_USER config/docker/sms_logger/*.py .
COPY --chown=$APP_USER config/docker/sms_logger/docker-entrypoint.sh docker-entrypoint.sh

RUN mkdir -p $APP_DIR/resource

ENTRYPOINT ["bash", "docker-entrypoint.sh"]

