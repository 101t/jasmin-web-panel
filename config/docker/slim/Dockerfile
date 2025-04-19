FROM python:3.12-slim

# disable debian interactive
ARG DEBIAN_FRONTEND=noninteractive
# suppress pip upgrade warning
ARG PIP_DISABLE_PIP_VERSION_CHECK=1
# disable cache directory, image size 2.1GB to 1.9GB
ARG PIP_NO_CACHE_DIR=1
ARG UV_NO_CACHE_DIR=1

RUN apt-get update && apt-get -y upgrade && apt-get install --no-install-recommends -y  \
    python3-dev python3-wheel python3-setuptools virtualenv \
    build-essential gcc curl \
    libpq-dev libpq5 telnet \
    # Run python with jemalloc
    # More on this:
    # - https://zapier.com/engineering/celery-python-jemalloc/
    # - https://paste.pics/581cc286226407ab0be400b94951a7d9
    libjemalloc2

# Pillow dependencies
RUN apt-get install --no-install-recommends -y \
    libtiff5-dev libjpeg-dev libopenjp2-7-dev zlib1g-dev  \
    libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev  \
    tk8.6-dev python3-tk libharfbuzz-dev libfribidi-dev libxcb1-dev

RUN apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

# --------------------------------------
ENV APP_DIR=/app
ENV APP_USER=app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1
# Run python with jemalloc
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

RUN useradd -m -d ${APP_DIR} -U -r -s /bin/bash ${APP_USER}

USER ${APP_USER}

WORKDIR ${APP_DIR}

# Create the virtual environment
RUN python -m venv /app/env
# Activate the virtual environment
ENV PATH="$APP_DIR/env/bin:$PATH"

COPY --chown=$APP_USER pyproject.toml .

RUN pip install -U pip uv wheel && uv pip install -r pyproject.toml --extra prod

# copy code to image
COPY --chown=$APP_USER . .

COPY --chown=$APP_USER config/docker/slim/*.sh .

RUN mkdir -p public/static && mkdir -p public/media && mkdir -p logs/

EXPOSE 8000

ENTRYPOINT ["bash", "docker-entrypoint.sh"]

HEALTHCHECK --interval=10s --timeout=10s --retries=30 \
    CMD curl -L http://127.0.0.1:8000/api/health_check > /dev/null

