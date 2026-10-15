# Variables definitions
# -----------------------------------------------------------------------------

TIMEOUT ?= 60

# Determine the OS platform (Windows or Linux)
ifeq ($(OS),Windows_NT)
	SHELL := cmd.exe
	RM := del /Q
	EXE := .exe
else
	SHELL := /bin/bash
	RM := rm -rf
	EXE :=
endif


# Target section and Global definitions
# -----------------------------------------------------------------------------
.PHONY: all clean test test_integration docs install run deploy down

all: clean test install run deploy down

test:
	PYTHONPATH=. python -m pytest tests -vv --show-capture=all

# Runs the jcli tests against a disposable Jasmin gateway in Docker.
test_integration:
	docker compose -f tests/integration/docker-compose.yml up -d --wait
	JASMIN_INTEGRATION=1 TELNET_PORT=18990 PYTHONPATH=. python -m pytest tests/integration -v; \
	status=$$?; docker compose -f tests/integration/docker-compose.yml down -v; exit $$status

docs:
	mkdocs serve

install:
	@echo "Installing dependencies"
	python3 -m venv env/
	env/bin/pip install --upgrade pip wheel uv
	env/bin/uv pip install --python env/bin/python -r pyproject.toml --extra dev --extra docs
	@echo "Now run: source env/bin/activate"

run:
	PYTHONPATH=. python manage.py runserver 0.0.0.0:8000

run_gunicorn:
	PYTHONPATH=. gunicorn -b 0.0.0.0:8000 config.wsgi:application

run_celery:
	PYTHONPATH=. celery -A config worker --max-tasks-per-child 1 -l info

run_docker: generate_dot_env
	docker compose up -d

generate_dot_env:
	@echo "Creating .env file"
	@if [ ! -e .env ]; then \
		cp sample.env .env; \
	fi

make_migrations:
	PYTHONPATH=. python manage.py makemigrations

migrate:
	PYTHONPATH=. python manage.py migrate

samples:
	PYTHONPATH=. python manage.py samples

clean:
	$(RM) *.pyc
	$(RM) -r __pycache__
	$(RM) Thumbs.db
	$(RM) *~
	$(RM) .cache
	$(RM) build
	$(RM) dist
	$(RM) *.egg-info
	$(RM) htmlcov
	$(RM) .tox/
	$(RM) -r docs/_build
	$(RM) .env