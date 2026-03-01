# Installation & Development Guide

This guide covers setting up the Jasmin Web Panel for local development or direct installation on a server.

## Prerequisites

- **Python 3.11** (required – Python 3.12+ may have compatibility issues with some dependencies)
- PostgreSQL 14 or higher
- Redis 6 or higher
- RabbitMQ 3.x (optional – can use Redis as Celery broker)
- Jasmin SMS Gateway (running and accessible)

!!! warning "Python Version"
    The project requires **Python 3.11**. Using Python 3.10 or earlier is not supported. Python 3.12+ may work but is not officially tested. Always verify with `python3 --version` before proceeding.

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/101t/jasmin-web-panel.git
cd jasmin-web-panel
```

### 2. Environment Setup

We recommend using a virtual environment. The project includes a `Makefile` to automate this.

```bash
# Create virtual environment and install dependencies
make install
```

Or manually:

```bash
python3.11 -m venv env/
source env/bin/activate
pip install --upgrade pip wheel uv
uv pip install -r pyproject.toml --extra dev
```

!!! tip "Using the correct Python version"
    If your system has multiple Python versions installed, specify the version explicitly:
    ```bash
    python3.11 -m venv env/
    # macOS with pyenv or Homebrew
    pyenv local 3.11
    python -m venv env/
    ```

### 3. Configuration

Create a `.env` file from the sample:

```bash
cp sample.env .env
```

Edit the `.env` file to match your local services (Database, Redis, Jasmin Telnet ports).

### 4. PostgreSQL Database Setup

> **Note**: PostgreSQL 15 and newer revoke the `CREATE` privilege on the `public` schema from all users by default. You must explicitly grant it to the application user.

Connect to PostgreSQL as a superuser and run:

```sql
-- Replace these placeholders with the same values you will set in PRODB_URL in your .env file
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
CREATE DATABASE your_db_name OWNER your_db_user;
\c your_db_name
GRANT USAGE, CREATE ON SCHEMA public TO your_db_user;
```

Update your `.env` file to set `PRODB_URL`:

```dotenv
PRODB_URL=postgres://your_db_user:your_db_password@localhost:5432/your_db_name
```

#### Troubleshooting PostgreSQL Migrations

If you encounter errors like `permission denied for schema public` or `relation does not exist` when running migrations, follow these steps:

```sql
-- Connect as superuser (postgres)
psql -U postgres -d your_db_name

-- Grant all necessary privileges
GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;
GRANT ALL ON SCHEMA public TO your_db_user;
ALTER SCHEMA public OWNER TO your_db_user;
```

If you see `django.db.utils.ProgrammingError: permission denied` errors, ensure you are using the correct `PRODB_URL` format and that the user owns the database. Also confirm the `pg_hba.conf` allows `md5` or `scram-sha-256` authentication for local connections.

### 5. Database Migrations

Initialize the database schema:

```bash
make migrate
# OR
python manage.py migrate
```

After migrations complete, verify the tables were created:

```bash
python manage.py showmigrations
```

If any migration is listed as `[ ]` (not applied), re-run:

```bash
python manage.py migrate --run-syncdb
```

### 6. Create Admin User

```bash
python manage.py createsuperuser
```

### 7. Collect Static Files (Production)

```bash
python manage.py collectstatic --noinput
```

### 8. Run the Server

```bash
make run
# OR
python manage.py runserver 0.0.0.0:8000
```

Access the panel at `http://localhost:8000`.

## Running Background Tasks

The panel uses Celery for background processing. You need to run a worker:

```bash
make run_celery
# OR
celery -A config worker --max-tasks-per-child 1 -l info
```

## Running with Docker (Development)

For a complete dev environment including dependencies:

```bash
make run_docker
```

This will build the containers and start the stack defined in `docker-compose.yml`.
