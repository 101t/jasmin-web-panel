#!/usr/bin/env bash
# ==============================================================================
# Jasmin Web Panel — Universal Linux Installer
# ==============================================================================
# Usage (recommended):
#   curl -fsSL https://raw.githubusercontent.com/101t/jasmin-web-panel/master/scripts/install.sh | sudo bash
#
# Non-interactive examples:
#   # Full Docker Compose stack (panel + Jasmin + Postgres + Redis + RabbitMQ + sms_logger)
#   curl -fsSL .../scripts/install.sh | sudo bash -s -- --mode docker --domain sms.example.com --non-interactive
#
#   # Native Linux server (systemd + Gunicorn + Celery + PostgreSQL + Redis + Nginx + Let's Encrypt SSL)
#   curl -fsSL .../scripts/install.sh | sudo bash -s -- --mode systemd --domain sms.example.com --with-ssl --email admin@example.com --non-interactive
#
#   # Uninstall
#   curl -fsSL .../scripts/install.sh | sudo bash -s -- --uninstall
# ==============================================================================

set -euo pipefail

REPO_OWNER="${REPO_OWNER:-101t}"
REPO_NAME="${REPO_NAME:-jasmin-web-panel}"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}"
INSTALL_DIR="${INSTALL_DIR:-/opt/jasmin-web-panel}"
ENV_DIR="/etc/jasmin-web-panel"
SERVICE_USER="jasminpanel"

MODE=""
VERSION="latest"
DOMAIN=""
PORT="8999"
WITH_SSL="false"
SSL_EMAIL=""
NON_INTERACTIVE="false"
UNINSTALL="false"
TELNET_HOST="127.0.0.1"
TELNET_PORT="8990"
TELNET_USERNAME="jcliadmin"
TELNET_PW="jclipwd"

# ---------- Colors & Logging ----------
if [[ -t 1 ]]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; BOLD=''; NC=''
fi

info()    { printf "${BLUE}[INFO]${NC} %s\n" "$*"; }
ok()      { printf "${GREEN}[ OK ]${NC} %s\n" "$*"; }
warn()    { printf "${YELLOW}[WARN]${NC} %s\n" "$*"; }
die()     { printf "${RED}[ERR ]${NC} %s\n" "$*" >&2; exit 1; }

usage() {
    cat <<EOF
Jasmin Web Panel Installer

Options:
  --mode <docker|systemd>     Installation mode (default: prompts interactively, or docker in --non-interactive)
  --version <tag|master>      Release tag or 'latest' (default: latest)
  --dir <path>                Install directory (default: /opt/jasmin-web-panel)
  --domain <fqdn>             Domain name (e.g. sms.example.com) for ALLOWED_HOSTS and Nginx
  --port <port>               Host HTTP port in docker mode (default: 8999)
  --with-ssl                  Provision Let's Encrypt HTTPS certificate via Certbot (systemd mode + --domain)
  --email <email>             Email for Let's Encrypt registration (required with --with-ssl)
  --telnet-host <host>        Jasmin jcli host in systemd mode (default: 127.0.0.1)
  --telnet-port <port>        Jasmin jcli port in systemd mode (default: 8990)
  --non-interactive           Run without prompts (suitable for CI / cloud-init)
  --uninstall                 Stop services and remove Jasmin Web Panel (preserves DB data)
  -h, --help                  Show this help
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --mode)            MODE="${2:-}"; shift 2 ;;
            --version)         VERSION="${2:-}"; shift 2 ;;
            --dir)             INSTALL_DIR="${2:-}"; shift 2 ;;
            --domain)          DOMAIN="${2:-}"; shift 2 ;;
            --port)            PORT="${2:-}"; shift 2 ;;
            --with-ssl)        WITH_SSL="true"; shift ;;
            --email)           SSL_EMAIL="${2:-}"; shift 2 ;;
            --telnet-host)     TELNET_HOST="${2:-}"; shift 2 ;;
            --telnet-port)     TELNET_PORT="${2:-}"; shift 2 ;;
            --non-interactive) NON_INTERACTIVE="true"; shift ;;
            --uninstall)       UNINSTALL="true"; shift ;;
            -h|--help)         usage; exit 0 ;;
            *)                 die "Unknown option: $1 (use --help)" ;;
        esac
    done
}

require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        die "Please run as root (e.g. curl -fsSL ... | sudo bash)."
    fi
}

detect_os() {
    [[ -f /etc/os-release ]] || die "Cannot detect Linux distribution (/etc/os-release missing)."
    # shellcheck disable=SC1091
    source /etc/os-release
    OS_ID="${ID:-unknown}"
    OS_ID_LIKE="${ID_LIKE:-}"
    OS_VERSION="${VERSION_ID:-}"
    ARCH="$(uname -m)"

    case "${OS_ID}" in
        ubuntu|debian)
            PKG_MGR="apt"
            ;;
        rhel|centos|rocky|almalinux|fedora)
            PKG_MGR="dnf"
            command -v dnf >/dev/null 2>&1 || PKG_MGR="yum"
            ;;
        *)
            if [[ "${OS_ID_LIKE}" == *"debian"* ]]; then
                PKG_MGR="apt"
            elif [[ "${OS_ID_LIKE}" == *"rhel"* || "${OS_ID_LIKE}" == *"fedora"* ]]; then
                PKG_MGR="dnf"
                command -v dnf >/dev/null 2>&1 || PKG_MGR="yum"
            else
                die "Unsupported Linux distribution: ${OS_ID}. Use Docker Compose manually."
            fi
            ;;
    esac
    info "Detected OS: ${PRETTY_NAME:-${OS_ID}} (${ARCH}, package manager: ${PKG_MGR})"
}

gen_secret() {
    local bytes="${1:-36}"
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -base64 "${bytes}" | tr -dc 'A-Za-z0-9' | head -c 50
    else
        head -c 64 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 50
    fi
}

resolve_version() {
    if [[ "${VERSION}" == "latest" ]]; then
        local api_url="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest"
        local tag=""
        tag="$(curl -fsSL "${api_url}" 2>/dev/null | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1 || true)"
        if [[ -n "${tag}" ]]; then
            VERSION="${tag}"
        else
            warn "Could not resolve latest GitHub release tag; falling back to master."
            VERSION="master"
        fi
    fi
    info "Target version: ${VERSION}"
}

prompt_options() {
    if [[ "${NON_INTERACTIVE}" == "true" ]]; then
        MODE="${MODE:-docker}"
        return
    fi

    if [[ -z "${MODE}" ]]; then
        printf "\n${BOLD}Select installation mode:${NC}\n"
        printf "  1) Docker Compose (recommended — full stack with Jasmin, Postgres, Redis, RabbitMQ)\n"
        printf "  2) Systemd + Nginx (native Linux service, connects to existing or local Jasmin)\n"
        read -rp "Enter choice [1-2] (default: 1): " choice </dev/tty || choice="1"
        case "${choice:-1}" in
            1) MODE="docker" ;;
            2) MODE="systemd" ;;
            *) die "Invalid selection: ${choice}" ;;
        esac
    fi

    if [[ -z "${DOMAIN}" ]]; then
        read -rp "Domain name for ALLOWED_HOSTS / Nginx (leave blank for IP/localhost): " DOMAIN </dev/tty || DOMAIN=""
    fi

    if [[ "${MODE}" == "systemd" && -n "${DOMAIN}" && "${WITH_SSL}" != "true" ]]; then
        read -rp "Enable free Let's Encrypt HTTPS via Certbot? [y/N]: " ans </dev/tty || ans="n"
        if [[ "${ans,,}" == "y" ]]; then
            WITH_SSL="true"
            read -rp "Email for Let's Encrypt renewal notices: " SSL_EMAIL </dev/tty || SSL_EMAIL=""
        fi
    fi
}

uninstall_panel() {
    warn "Uninstalling Jasmin Web Panel..."
    if systemctl list-unit-files 2>/dev/null | grep -q '^jasmin-web\.service'; then
        systemctl disable --now jasmin-web.service jasmin-celery.service 2>/dev/null || true
        rm -f /etc/systemd/system/jasmin-web.service /etc/systemd/system/jasmin-celery.service
        systemctl daemon-reload
    fi
    if [[ -f "${INSTALL_DIR}/docker-compose.yml" ]] && command -v docker >/dev/null 2>&1; then
        (cd "${INSTALL_DIR}" && docker compose down) || true
    fi
    rm -f /etc/nginx/sites-enabled/jasmin-web-panel /etc/nginx/sites-available/jasmin-web-panel /etc/nginx/conf.d/jasmin-web-panel.conf
    if command -v nginx >/dev/null 2>&1; then
        nginx -t 2>/dev/null && systemctl reload nginx 2>/dev/null || true
    fi
    rm -rf "${INSTALL_DIR}"
    ok "Jasmin Web Panel removed. Database data and ${ENV_DIR} (if present) were preserved."
    exit 0
}

install_base_packages() {
    info "Installing base packages..."
    if [[ "${PKG_MGR}" == "apt" ]]; then
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -qq
        apt-get install -y -qq curl ca-certificates git openssl gnupg lsb-release
    else
        "${PKG_MGR}" install -y -q curl ca-certificates git openssl
    fi
}

install_docker_if_missing() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        ok "Docker and Docker Compose plugin are already installed."
        return
    fi
    info "Installing Docker Engine and Compose plugin..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
    ok "Docker installed."
}

download_source() {
    mkdir -p "${INSTALL_DIR}"
    if [[ -d "${INSTALL_DIR}/.git" ]]; then
        info "Updating existing repository in ${INSTALL_DIR}..."
        git -C "${INSTALL_DIR}" fetch --tags --quiet
        git -C "${INSTALL_DIR}" checkout --quiet "${VERSION}"
        if [[ "${VERSION}" == "master" ]]; then
            git -C "${INSTALL_DIR}" pull --ff-only --quiet
        fi
    else
        info "Downloading Jasmin Web Panel (${VERSION}) into ${INSTALL_DIR}..."
        git clone --quiet --depth 1 --branch "${VERSION}" "${REPO_URL}.git" "${INSTALL_DIR}"
    fi
}

write_secure_env() {
    local env_file="$1"
    local db_url="$2"
    local redis_host="$3"
    local telnet_host="$4"
    local pg_pass="$5"
    local submit_log="$6"

    if [[ -f "${env_file}" ]]; then
        warn "Existing ${env_file} found — preserving it (backing up to ${env_file}.bak)."
        cp -p "${env_file}" "${env_file}.bak"
        return
    fi

    local secret_key field_key allowed_hosts csrf_origins https_only
    secret_key="$(gen_secret 48)"
    field_key="$(gen_secret 48)"
    https_only="False"
    csrf_origins=""
    if [[ -n "${DOMAIN}" ]]; then
        allowed_hosts="${DOMAIN},localhost,127.0.0.1"
        if [[ "${WITH_SSL}" == "true" ]]; then
            https_only="True"
            csrf_origins="https://${DOMAIN}"
        else
            csrf_origins="http://${DOMAIN}"
        fi
    else
        allowed_hosts="*"
    fi

    install -d -m 750 "$(dirname "${env_file}")"
    cat > "${env_file}" <<EOF
# Generated by Jasmin Web Panel installer on $(date -u +"%Y-%m-%dT%H:%M:%SZ")
DEBUG=False
SECRET_KEY=${secret_key}
FIELD_ENCRYPTION_KEY=${field_key}
DJANGO_SETTINGS_MODULE=config.settings.pro

ALLOWED_HOSTS=${allowed_hosts}
CSRF_TRUSTED_ORIGINS=${csrf_origins}
HTTPS_ONLY=${https_only}

TIME_ZONE=UTC
LANGUAGE_CODE=en
ADMIN_URL=admin/
SITE_ID=1

POSTGRES_DB=jasmin
POSTGRES_USER=jasmin
POSTGRES_PASSWORD=${pg_pass}
PRODB_URL=${db_url}

REDIS_HOST=${redis_host}
REDIS_PORT=6379
REDIS_DB=0

TELNET_HOST=${telnet_host}
TELNET_PORT=${TELNET_PORT}
TELNET_USERNAME=${TELNET_USERNAME}
TELNET_PW=${TELNET_PW}
TELNET_TIMEOUT=10

HTTP_HOST=http://${telnet_host}
HTTP_PORT=1401
HTTP_USERNAME=foo
HTTP_PASSWORD=bar

SMPP_HOST=${telnet_host}
SMPP_PORT=2775
SMPP_SYSTEM_ID=foo
SMPP_PASSWORD=bar

SUBMIT_LOG=${submit_log}
JASMIN_WEB_PORT=${PORT}

API_THROTTLE_ANON=20/minute
API_THROTTLE_USER=120/minute
EOF
    chmod 600 "${env_file}"
    ok "Generated secure configuration at ${env_file} (chmod 600)."
}

install_docker_mode() {
    install_docker_if_missing
    download_source

    local pg_pass
    pg_pass="$(gen_secret 24)"
    write_secure_env "${INSTALL_DIR}/.env" \
        "postgres://jasmin:${pg_pass}@db:5432/jasmin" \
        "redis" \
        "jasmin" \
        "${pg_pass}" \
        "True"

    # Security hardening override: keep Jasmin jcli (8990) bound to localhost only by default
    cat > "${INSTALL_DIR}/docker-compose.override.yml" <<EOF
services:
  jasmin:
    ports: !override
      - "\${JASMIN_SMS_PORT:-2775}:2775"
      - "127.0.0.1:\${JASMIN_DASHBOARD_PORT:-8990}:8990"
      - "\${JASMIN_HTTP_API_PORT:-1401}:1401"
EOF

    info "Pulling images and starting Jasmin Web Panel stack..."
    (cd "${INSTALL_DIR}" && docker compose pull && docker compose up -d)

    info "Waiting for web panel health check on http://127.0.0.1:${PORT}/api/health_check ..."
    for _ in $(seq 1 30); do
        if curl -fsS "http://127.0.0.1:${PORT}/api/health_check" >/dev/null 2>&1; then
            ok "Jasmin Web Panel is healthy!"
            break
        fi
        sleep 2
    done

    local host_display="${DOMAIN:-$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost')}"
    printf "\n${GREEN}${BOLD}======================================================================${NC}\n"
    printf "${GREEN}${BOLD} Jasmin Web Panel (Docker) installed successfully!${NC}\n"
    printf "${GREEN}${BOLD}======================================================================${NC}\n"
    printf "  Web UI:          http://%s:%s\n" "${host_display}" "${PORT}"
    printf "  Default Login:   admin / secret  ${YELLOW}(CHANGE IMMEDIATELY!)${NC}\n"
    printf "  Config file:     %s/.env\n" "${INSTALL_DIR}"
    printf "  Manage stack:    cd %s && docker compose ps | logs -f\n" "${INSTALL_DIR}"
    printf "  Security note:   Jasmin jcli (8990) is bound to 127.0.0.1 only.\n\n"
}

install_systemd_mode() {
    info "Installing system dependencies (PostgreSQL, Redis, Nginx, telnet)..."
    local pg_service="postgresql" redis_service="redis-server"
    if [[ "${PKG_MGR}" == "apt" ]]; then
        apt-get install -y -qq postgresql postgresql-contrib redis-server nginx telnet \
            libpq-dev build-essential libjpeg-dev zlib1g-dev libfreetype6-dev
    else
        "${PKG_MGR}" install -y -q postgresql-server postgresql-contrib redis nginx telnet \
            postgresql-devel gcc libjpeg-turbo-devel zlib-devel freetype-devel
        redis_service="redis"
        if [[ ! -d /var/lib/pgsql/data/base ]]; then
            postgresql-setup --initdb || true
        fi
    fi

    systemctl enable --now "${pg_service}" "${redis_service}" nginx

    # Create dedicated system user
    if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
        useradd --system --home-dir "${INSTALL_DIR}" --shell /usr/sbin/nologin --user-group "${SERVICE_USER}"
    fi

    download_source

    # Install uv & managed Python 3.12 (works cleanly on every Ubuntu/Debian/RHEL without PPAs or compiling)
    if ! command -v uv >/dev/null 2>&1; then
        info "Installing uv (fast Python & package manager)..."
        curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
    fi

    info "Provisioning Python 3.12 virtual environment and installing dependencies..."
    /usr/local/bin/uv python install 3.12
    /usr/local/bin/uv venv --python 3.12 "${INSTALL_DIR}/env"
    /usr/local/bin/uv pip install --python "${INSTALL_DIR}/env/bin/python" -r "${INSTALL_DIR}/pyproject.toml" --extra prod

    # Setup PostgreSQL database and user (PostgreSQL 15+ schema grants included)
    local pg_pass
    pg_pass="$(gen_secret 24)"
    if [[ ! -f "${ENV_DIR}/env" ]]; then
        info "Creating PostgreSQL database 'jasmin_web' and user 'jasmin_web'..."
        su - postgres -c "psql -v ON_ERROR_STOP=1" <<SQL
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'jasmin_web') THEN
      CREATE ROLE jasmin_web LOGIN PASSWORD '${pg_pass}';
   END IF;
END
\$\$;
SELECT 'CREATE DATABASE jasmin_web OWNER jasmin_web'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'jasmin_web')\gexec
\c jasmin_web
GRANT USAGE, CREATE ON SCHEMA public TO jasmin_web;
SQL
    fi

    write_secure_env "${ENV_DIR}/env" \
        "postgres://jasmin_web:${pg_pass}@127.0.0.1:5432/jasmin_web" \
        "127.0.0.1" \
        "${TELNET_HOST}" \
        "${pg_pass}" \
        "False"

    ln -sfn "${ENV_DIR}/env" "${INSTALL_DIR}/.env"
    mkdir -p "${INSTALL_DIR}/logs" "${INSTALL_DIR}/public/static" "${INSTALL_DIR}/public/media"
    chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}" "${ENV_DIR}"
    chmod 600 "${ENV_DIR}/env"

    info "Running Django migrations, initial seed, and collectstatic..."
    su -s /bin/bash "${SERVICE_USER}" -c "
        cd '${INSTALL_DIR}'
        set -a; source '${ENV_DIR}/env'; set +a
        '${INSTALL_DIR}/env/bin/python' manage.py migrate --noinput
        '${INSTALL_DIR}/env/bin/python' manage.py samples
        '${INSTALL_DIR}/env/bin/python' manage.py collectstatic --noinput --clear
    "

    info "Installing hardened systemd units..."
    cp "${INSTALL_DIR}/packaging/systemd/jasmin-web.service" /etc/systemd/system/jasmin-web.service
    cp "${INSTALL_DIR}/packaging/systemd/jasmin-celery.service" /etc/systemd/system/jasmin-celery.service
    # Adjust redis service unit name for RHEL/Fedora
    if [[ "${redis_service}" != "redis-server" ]]; then
        sed -i "s/redis-server\.service/${redis_service}.service/g" /etc/systemd/system/jasmin-*.service
    fi
    systemctl daemon-reload
    systemctl enable --now jasmin-web.service jasmin-celery.service

    info "Configuring Nginx reverse proxy..."
    local server_name="${DOMAIN:-_}"
    local nginx_conf="/etc/nginx/sites-available/jasmin-web-panel"
    if [[ -d /etc/nginx/sites-available ]]; then
        sed "s|__SERVER_NAME__|${server_name}|g; s|__INSTALL_DIR__|${INSTALL_DIR}|g" \
            "${INSTALL_DIR}/packaging/nginx/jasmin-web-panel.conf" > "${nginx_conf}"
        ln -sfn "${nginx_conf}" /etc/nginx/sites-enabled/jasmin-web-panel
        rm -f /etc/nginx/sites-enabled/default
    else
        sed "s|__SERVER_NAME__|${server_name}|g; s|__INSTALL_DIR__|${INSTALL_DIR}|g" \
            "${INSTALL_DIR}/packaging/nginx/jasmin-web-panel.conf" > /etc/nginx/conf.d/jasmin-web-panel.conf
    fi
    nginx -t && systemctl reload nginx

    if [[ "${WITH_SSL}" == "true" && -n "${DOMAIN}" ]]; then
        info "Provisioning Let's Encrypt TLS certificate for ${DOMAIN}..."
        if [[ "${PKG_MGR}" == "apt" ]]; then
            apt-get install -y -qq certbot python3-certbot-nginx
        else
            "${PKG_MGR}" install -y -q certbot python3-certbot-nginx
        fi
        local certbot_email_arg="--register-unsafely-without-email"
        [[ -n "${SSL_EMAIL}" ]] && certbot_email_arg="--email ${SSL_EMAIL}"
        # shellcheck disable=SC2086
        certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos ${certbot_email_arg} --redirect
    fi

    sleep 2
    if curl -fsS "http://127.0.0.1:8000/api/health_check" >/dev/null 2>&1; then
        ok "Jasmin Web Panel is responding on http://127.0.0.1:8000/api/health_check"
    else
        warn "Health check did not respond yet; inspect logs with: journalctl -u jasmin-web -n 50"
    fi

    local scheme="http"
    [[ "${WITH_SSL}" == "true" ]] && scheme="https"
    local host_display="${DOMAIN:-$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost')}"
    printf "\n${GREEN}${BOLD}======================================================================${NC}\n"
    printf "${GREEN}${BOLD} Jasmin Web Panel (systemd + Nginx) installed successfully!${NC}\n"
    printf "${GREEN}${BOLD}======================================================================${NC}\n"
    printf "  Web UI:          %s://%s\n" "${scheme}" "${host_display}"
    printf "  Default Login:   admin / secret  ${YELLOW}(CHANGE IMMEDIATELY!)${NC}\n"
    printf "  Config file:     %s/env\n" "${ENV_DIR}"
    printf "  Services:        systemctl status jasmin-web jasmin-celery\n"
    printf "  Logs:            journalctl -u jasmin-web -f\n\n"
}

main() {
    parse_args "$@"
    require_root
    if [[ "${UNINSTALL}" == "true" ]]; then
        uninstall_panel
    fi
    detect_os
    install_base_packages
    resolve_version
    prompt_options

    case "${MODE}" in
        docker)  install_docker_mode ;;
        systemd) install_systemd_mode ;;
        *)       die "Unsupported --mode '${MODE}'. Expected 'docker' or 'systemd'." ;;
    esac
}

main "$@"
