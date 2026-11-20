#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/jasmin-web-panel"
ENV_DIR="/etc/jasmin-web-panel"
ENV_FILE="${ENV_DIR}/env"
SERVICE_USER="jasminpanel"

# Create dedicated system user if missing
if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
    useradd --system --home-dir "${APP_DIR}" --shell /usr/sbin/nologin --user-group "${SERVICE_USER}"
fi

# Generate initial /etc/jasmin-web-panel/env with random secrets if not present
if [[ ! -f "${ENV_FILE}" ]]; then
    SECRET_KEY="$(openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 50)"
    FIELD_KEY="$(openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 50)"
    cp "${ENV_DIR}/env.example" "${ENV_FILE}"
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" "${ENV_FILE}"
    sed -i "s|^FIELD_ENCRYPTION_KEY=.*|FIELD_ENCRYPTION_KEY=${FIELD_KEY}|" "${ENV_FILE}"
    sed -i "s|^REDIS_HOST=.*|REDIS_HOST=127.0.0.1|" "${ENV_FILE}"
    chmod 600 "${ENV_FILE}"
fi

ln -sfn "${ENV_FILE}" "${APP_DIR}/.env"

# Provision Python virtualenv and install dependencies if not present
if [[ ! -x "${APP_DIR}/env/bin/gunicorn" ]]; then
    # Distro python3 may be too old (RHEL/Rocky 9 ship 3.9); take the first interpreter >= 3.11
    PYTHON=""
    for candidate in python3.13 python3.12 python3.11 python3; do
        if command -v "${candidate}" >/dev/null 2>&1 \
            && "${candidate}" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
            PYTHON="${candidate}"
            break
        fi
    done
    [[ -n "${PYTHON}" ]] || { echo "Python >= 3.11 is required" >&2; exit 1; }
    "${PYTHON}" -m venv "${APP_DIR}/env"
    "${APP_DIR}/env/bin/pip" install --quiet --upgrade pip wheel uv
    "${APP_DIR}/env/bin/uv" pip install --python "${APP_DIR}/env/bin/python" -r "${APP_DIR}/pyproject.toml" --extra prod
fi

mkdir -p "${APP_DIR}/logs" "${APP_DIR}/public/static" "${APP_DIR}/public/media" \
         /var/log/jasmin-web-panel /var/lib/jasmin-web-panel
chown -R "${SERVICE_USER}:${SERVICE_USER}" "${APP_DIR}" "${ENV_DIR}" \
         /var/log/jasmin-web-panel /var/lib/jasmin-web-panel
chmod 600 "${ENV_FILE}"

# Collect static assets (DB migration runs once operator configures PRODB_URL)
su -s /bin/bash "${SERVICE_USER}" -c "
    cd '${APP_DIR}'
    set -a; source '${ENV_FILE}'; set +a
    '${APP_DIR}/env/bin/python' manage.py collectstatic --noinput --clear
" || true

if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    systemctl daemon-reload
fi

cat <<'EOF'

======================================================================
 Jasmin Web Panel package installed!
======================================================================
 Next steps:
   1. Edit /etc/jasmin-web-panel/env (set PRODB_URL, ALLOWED_HOSTS, TELNET_*).
   2. Initialize the database:
        sudo -u jasminpanel /opt/jasmin-web-panel/env/bin/python /opt/jasmin-web-panel/manage.py migrate
        sudo -u jasminpanel /opt/jasmin-web-panel/env/bin/python /opt/jasmin-web-panel/manage.py createsuperuser
   3. Start services:
        sudo systemctl enable --now jasmin-web jasmin-celery
   4. Optional Nginx config template: /etc/jasmin-web-panel/nginx.conf.example
======================================================================
EOF
