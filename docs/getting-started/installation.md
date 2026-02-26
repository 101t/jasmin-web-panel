# Installation & Development Guide

This guide covers setting up the Jasmin Web Panel for local development or direct installation on a server.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL
- Redis
- RabbitMQ
- Jasmin SMS Gateway (running and accessible)

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
virtualenv -p python3.11 env/
source env/bin/activate
pip install --upgrade pip wheel uv
uv pip install -r pyproject.toml --extra dev
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

Update your `.env` file to set `PRODB_URL` to match the credentials above.

### 5. Database Setup

Initialize the database schema:

```bash
make migrate
# OR
python manage.py migrate
```

### 6. Create Admin User

```bash
python manage.py createsuperuser
```

### 7. Run the Server

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
