#!/usr/bin/env python3
"""
Jasmin Web Panel — complete installation & deployment video tutorial generator.

Produces a YouTube-ready, narrated Full HD (1920x1080 @ 30fps) tutorial plus every
asset needed to publish it:

  media/jasmin-web-panel-install-guide.mp4   the video (H.264 + AAC, faststart)
  media/youtube/thumbnail.png                1280x720 YouTube thumbnail
  media/youtube/captions.en.srt              English subtitles, word-timed (upload to YouTube)
  media/youtube/description.md               title, description, chapter timestamps, tags
  media/previews/*.png                       stills for review
  docs/assets/images/video-thumbnail.png     thumbnail used by README and docs
  docs/video-tutorial.md                     chapter table refreshed between markers

Direction: an expressive female narrator ("Ava", Microsoft neural voice via edge-tts) whose
emotion follows [mood] tags in the script (pitch/rate/volume per phrase), animated chapter
title cards, camera punch-ins that follow the typing, karaoke captions synced word by word,
reaction stickers, highlighted warnings, a voice-reactive narrator badge, an animated
"Star on GitHub" end screen, and a generated ambient soundtrack that ducks under the voice,
with keyboard, whoosh, pop and chime sound effects.

Usage (no system ffmpeg needed):
  uv run --no-project --with pillow --with imageio-ffmpeg --with edge-tts --with numpy \
      python scripts/generate_install_video.py

  # Fast layout check: preview stills with estimated timings (no TTS, no video)
  uv run --no-project --with pillow --with imageio-ffmpeg --with edge-tts --with numpy \
      python scripts/generate_install_video.py --frames-only

  # Other voices: --voice en-US-EmmaMultilingualNeural (cheerful) / en-US-JennyNeural (warm)
"""

from __future__ import annotations

import argparse
import asyncio
import math
import multiprocessing
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT = 1920, 1080
FPS = 30
SR = 48000                       # audio sample rate; SR / FPS = 1600 samples per frame
VOICE = "en-US-AvaMultilingualNeural"
NARRATOR = "Ava"
HOLD = 2.2                       # silent hold after each step's narration, time to read the terminal (seconds)
CHAPTER_EXTRA = 1.0              # extra hold at the end of each chapter
GAP = 0.32                       # pause between phrases of different moods
LEAD = {"intro": 1.8, "card": 0.55, "step": 0.5, "outro": 0.7}

# edge-tts accepts no SSML speaking styles, so emotion = per-phrase prosody + the script's wording.
MOODS = {                        # (rate, pitch, volume)
    "calm": ("-5%", "+0Hz", "+0%"),
    "happy": ("-1%", "+5Hz", "+0%"),
    "excited": ("+5%", "+10Hz", "+5%"),
    "serious": ("-11%", "-5Hz", "+0%"),
    "soft": ("-9%", "+2Hz", "-6%"),
}

REPO = "https://github.com/101t/jasmin-web-panel"
DOCS = "https://about.supernovasoft.com/jasmin-web-panel/"
TELEGRAM = "https://t.me/jasminwebpanel"

# Palette (dark developer theme)
BG = (11, 17, 32)
PANEL = (17, 24, 39)
PANEL_BORDER = (31, 41, 55)
TERM_BG = (2, 6, 23)
TERM_TOP = (15, 23, 42)
TEXT = (248, 250, 252)
MUTED = (148, 163, 184)
DIM = (100, 116, 139)
CYAN = (56, 189, 248)
EMERALD = (16, 185, 129)
AMBER = (245, 158, 11)
VIOLET = (167, 139, 250)
ROSE = (251, 113, 133)
GOLD = (250, 204, 21)

FONT_DIR = "/usr/share/fonts/truetype"
SANS_BOLD = [f"{FONT_DIR}/ubuntu/Ubuntu-B.ttf", f"{FONT_DIR}/dejavu/DejaVuSans-Bold.ttf",
             f"{FONT_DIR}/liberation/LiberationSans-Bold.ttf"]
SANS_MED = [f"{FONT_DIR}/ubuntu/Ubuntu-M.ttf"] + SANS_BOLD
SANS_REG = [f"{FONT_DIR}/ubuntu/Ubuntu-R.ttf", f"{FONT_DIR}/dejavu/DejaVuSans.ttf",
            f"{FONT_DIR}/liberation/LiberationSans-Regular.ttf"]
MONO_BOLD = [f"{FONT_DIR}/dejavu/DejaVuSansMono-Bold.ttf", f"{FONT_DIR}/ubuntu/UbuntuMono-B.ttf"]
MONO_REG = [f"{FONT_DIR}/dejavu/DejaVuSansMono.ttf", f"{FONT_DIR}/ubuntu/UbuntuMono-R.ttf"]
EMOJI_FONT = f"{FONT_DIR}/noto/NotoColorEmoji.ttf"


def load_font(candidates: List[str], size: int):
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# --------------------------------------------------------------------------------------
# Script content. Narration may start sentences with [calm] [happy] [excited] [serious] [soft].
# --------------------------------------------------------------------------------------
Line = Tuple[str, str]  # (kind: cmd|comment|out|ok|warn|blank, text)
React = Tuple[str, str, Tuple[int, int, int]]  # (emoji, sticker text, color) shown when the terminal finishes


@dataclass
class Step:
    title: str
    terminal_title: str
    lines: List[Line]
    narration: str
    diagram: bool = False
    react: Optional[React] = None


@dataclass
class Chapter:
    nav: str
    blurb: str
    accent: Tuple[int, int, int]
    badge: str
    title: str
    subtitle: str
    bullets: List[str]
    steps: List[Step]
    emoji: str = "✨"
    hook: str = ""             # spoken on the chapter title card


B: Line = ("blank", "")
RAW = "https://raw.githubusercontent.com/101t/jasmin-web-panel/\\"

INTRO_NARRATION = (
    "[excited] Hey there, and welcome! [happy] I'm Ava, and in this guide I'll show you, step by "
    "step, how to install and run Jasmin Web Panel, the free and open source control center for "
    "Jasmin SMS Gateway. [calm] First, we'll see how it all works. Then we'll install it five "
    "different ways: with one single command, with Docker Compose, as native systemd services behind "
    "Nginx, on Kubernetes, and from Debian and RPM packages. After that, we'll create a first "
    "customer, connect a carrier, send a real test message, and lock everything down for production. "
    "[excited] So grab a coffee, and let's dive in!"
)

OUTRO_NARRATION = (
    "[excited] And that's a wrap! [happy] You now have Jasmin Web Panel installed, secured, and "
    "sending messages. Honestly, great job. [calm] The full documentation, with every configuration "
    "option and the REST API reference, is linked in the description. Jasmin Web Panel is free and "
    "open source, under the MIT license. [happy] If it helps you, please star the repository on "
    "GitHub, it really means a lot. And come say hi in our Telegram community. [calm] And if your "
    "business needs an enterprise grade platform with professional support, take a look at SMPP "
    "Forge, at smppforge dot com. [soft] Thanks so much for watching, and happy messaging!"
)

CHAPTERS: List[Chapter] = [
    # ------------------------------------------------------------------ 1. Overview
    Chapter(
        nav="Overview", blurb="How it works & prerequisites", accent=CYAN,
        emoji="🧩",
        hook=(
            "[happy] Chapter one! Let's see how it all works, and what you need before we start."
        ),
        badge="OPEN SOURCE  •  MIT LICENSE  •  v3.1",
        title="How Jasmin Web\nPanel Works",
        subtitle="A modern web UI and REST API that manages Jasmin SMS Gateway.",
        bullets=[
            "Every action becomes a jcli command, then persist",
            "SMS traffic never passes through the panel",
            "PostgreSQL, Redis and Celery power logs & exports",
            "Five install paths: curl, Docker, systemd, K8s, packages",
        ],
        steps=[
            Step(
                title="Architecture", terminal_title="architecture — how jasmin-web-panel works",
                diagram=True,
                lines=[
                    ("comment", "# Every click in the panel becomes a jcli command"),
                    ("out", "  Browser / REST API  ──▶  Jasmin Web Panel (:8000)"),
                    ("out", "  Panel  ──▶  jcli :8990  ──▶  user -a, mtrouter -a, persist"),
                    ("ok", "  Jasmin  ──▶  OK or error message  ──▶  shown in the UI"),
                    B,
                    ("comment", "# Delivery results flow back for the Submit Log"),
                    ("ok", "  Jasmin ──▶ RabbitMQ ──▶ sms_logger ──▶ PostgreSQL ──▶ Panel"),
                ],
                narration=(
                    "[calm] So, what exactly is Jasmin Web Panel? It's a Django application that manages Jasmin SMS "
                    "Gateway for you. Every action you take, in the browser or through the REST API, becomes a jcli "
                    "command, sent to Jasmin's management console on port 8990, and followed by persist, so your "
                    "changes survive restarts. [happy] And here's the part I love: your SMS traffic never flows "
                    "through the panel. It stays inside Jasmin, so the panel adds zero latency to message delivery."
                ),
                react=("⚡", "Zero added latency", EMERALD),
            ),
            Step(
                title="Prerequisites", terminal_title="root@sms-server: ~",
                lines=[
                    ("comment", "# Check your server"),
                    ("cmd", "grep PRETTY_NAME /etc/os-release"),
                    ("out", 'PRETTY_NAME="Ubuntu 24.04.1 LTS"'),
                    ("cmd", "nproc && free -h | grep Mem"),
                    ("out", "2"),
                    ("out", "Mem:           3.8Gi       612Mi       2.9Gi"),
                    B,
                    ("comment", "# Components"),
                    ("out", "  • Python 3.11 / 3.12        • PostgreSQL 14+ (or MySQL 8)"),
                    ("out", "  • Redis 6+                  • RabbitMQ 3.10+ (used by Jasmin)"),
                    ("out", "  • Jasmin SMS Gateway 0.9+ with jcli reachable on port 8990"),
                    B,
                    ("ok", "  Docker Compose mode starts all of the above for you."),
                ],
                narration=(
                    "[calm] Before installing, let's check the environment. You'll need a Linux server, like Ubuntu "
                    "22.04 or newer, Debian 12, or Rocky Linux 9, with at least two gigabytes of memory. The panel "
                    "uses PostgreSQL for its data, Redis for caching and background jobs, and of course, a running "
                    "Jasmin gateway. [happy] Good news: if you choose Docker Compose, all of these are started for "
                    "you automatically."
                ),
                react=("✅", "Server ready", EMERALD),
            ),
            Step(
                title="Choose your path", terminal_title="installation methods",
                lines=[
                    ("comment", "# Pick the method that fits your infrastructure"),
                    ("out", "  METHOD              BEST FOR                          TIME"),
                    ("out", "  ──────────────────────────────────────────────────────────────"),
                    ("ok", "  curl installer      any fresh Linux server            ~3 min"),
                    ("ok", "  Docker Compose      full stack, including Jasmin      ~2 min"),
                    ("ok", "  systemd + Nginx     classic VMs and bare metal        ~15 min"),
                    ("ok", "  Kubernetes          HA clusters and GitOps            ~10 min"),
                    ("ok", "  .deb / .rpm         Ansible, Puppet, server fleets    ~5 min"),
                    B,
                    ("comment", "# Every chapter of this video is self-contained."),
                ],
                narration=(
                    "[calm] There are five ways to install. The one-line installer is the fastest, and works on most "
                    "distributions. Docker Compose gives you the whole stack in containers. Native systemd services "
                    "suit classic servers. Kubernetes manifests are ready for your clusters, and Debian or RPM "
                    "packages fit configuration managed fleets. [happy] Just pick the chapter that matches your "
                    "infrastructure. Each one stands on its own."
                ),
                react=("🧭", "Pick your path", CYAN),
            ),
        ],
    ),
    # ------------------------------------------------------------------ 2. Installer
    Chapter(
        nav="Installer", blurb="One-line curl installer", accent=EMERALD,
        emoji="🚀",
        hook=(
            "[excited] Chapter two. The one-line installer. Honestly, this one is my favorite!"
        ),
        badge="FASTEST SETUP  •  UNIVERSAL LINUX",
        title="One-Line\nInstaller",
        subtitle="Ubuntu, Debian, Rocky, AlmaLinux, RHEL and Fedora, detected automatically.",
        bullets=[
            "Interactive wizard or fully automated flags",
            "Random SECRET_KEY & FIELD_ENCRYPTION_KEY",
            "jcli port 8990 bound to 127.0.0.1 by default",
            "Optional free HTTPS with Let's Encrypt",
        ],
        steps=[
            Step(
                title="Interactive wizard", terminal_title="root@sms-server: ~",
                lines=[
                    ("comment", "# Optional but recommended: read the script first"),
                    ("cmd", "curl -fsSL " + RAW),
                    ("cmd", "  master/scripts/install.sh -o install.sh && less install.sh"),
                    B,
                    ("comment", "# Run the interactive wizard"),
                    ("cmd", "sudo bash install.sh"),
                    ("out", "[INFO] Detected OS: Ubuntu 24.04.1 LTS (x86_64, package manager: apt)"),
                    ("out", "[INFO] Target version: 3.1.0"),
                    ("out", "Select installation mode:"),
                    ("out", "  1) Docker Compose (recommended — full stack with Jasmin)"),
                    ("out", "  2) Systemd + Nginx (native Linux service)"),
                    ("out", "Enter choice [1-2] (default: 1): 1"),
                    ("out", "Domain name for ALLOWED_HOSTS / Nginx: sms.example.com"),
                ],
                narration=(
                    "[happy] Okay! The universal installer is a single script. [calm] It detects your distribution, "
                    "installs the base packages, finds the latest release, and then asks you just two questions: "
                    "Docker or systemd, and your domain name. [serious] One important habit, though. Always review a "
                    "script before piping it to bash. Download it first, and read it, just like this."
                ),
                react=("🔍", "Read before you run", CYAN),
            ),
            Step(
                title="Automated Docker install", terminal_title="root@sms-server: ~",
                lines=[
                    ("comment", "# Fully automated (cloud-init, CI, Terraform user-data)"),
                    ("cmd", "curl -fsSL " + RAW),
                    ("cmd", "  master/scripts/install.sh | sudo bash -s -- \\"),
                    ("cmd", "  --mode docker --domain sms.example.com --non-interactive"),
                    ("out", "[ OK ] Docker and Docker Compose plugin are already installed."),
                    ("out", "[INFO] Downloading Jasmin Web Panel (3.1.0) into /opt/jasmin-web-panel..."),
                    ("ok", "[ OK ] Generated secure configuration at /opt/jasmin-web-panel/.env (chmod 600)"),
                    ("out", "[INFO] Pulling images and starting Jasmin Web Panel stack..."),
                    ("ok", "[ OK ] Jasmin Web Panel is healthy!"),
                    B,
                    ("ok", "  Web UI:         http://sms.example.com:8999"),
                    ("warn", "  Default login:  admin / secret   (CHANGE IMMEDIATELY!)"),
                    ("out", "  Security note:  Jasmin jcli (8990) is bound to 127.0.0.1 only."),
                ],
                narration=(
                    "[calm] For automation, like cloud init or CI pipelines, pass the options as flags, and add non "
                    "interactive. This example installs the full Docker stack for the domain sms dot example dot com. "
                    "[excited] And look at that, it's healthy already! [calm] The installer generated a fifty "
                    "character secret key and a separate field encryption key, saved them to a protected environment "
                    "file, and bound the jcli port to localhost only. [serious] Just remember to change that default "
                    "login right away."
                ),
                react=("🔑", "Secrets auto-generated", EMERALD),
            ),
            Step(
                title="Native install with HTTPS", terminal_title="root@sms-server: ~",
                lines=[
                    ("comment", "# Native systemd install with Let's Encrypt HTTPS"),
                    ("cmd", "curl -fsSL " + RAW),
                    ("cmd", "  master/scripts/install.sh | sudo bash -s -- \\"),
                    ("cmd", "  --mode systemd --domain sms.example.com \\"),
                    ("cmd", "  --with-ssl --email ops@example.com --non-interactive"),
                    ("out", "[INFO] Installing system dependencies (PostgreSQL, Redis, Nginx, telnet)..."),
                    ("out", "[INFO] Provisioning Python 3.12 virtual environment and installing dependencies..."),
                    ("out", "[INFO] Creating PostgreSQL database 'jasmin_web' and user 'jasmin_web'..."),
                    ("out", "[INFO] Installing hardened systemd units..."),
                    ("out", "[INFO] Provisioning Let's Encrypt TLS certificate for sms.example.com..."),
                    ("ok", "[ OK ] Jasmin Web Panel is responding on http://127.0.0.1:8000/api/health_check"),
                    ("ok", "  Web UI:  https://sms.example.com"),
                ],
                narration=(
                    "[calm] Prefer a native install with automatic HTTPS? Choose systemd mode, and add with SSL and "
                    "your email address. The script installs PostgreSQL, Redis and Nginx, creates a dedicated system "
                    "user, provisions Python 3.12 with uv, runs the migrations, installs hardened systemd units, and "
                    "requests a free Let's Encrypt certificate. [happy] All of that, in one command! [soft] Just make "
                    "sure your domain already points to this server."
                ),
                react=("🔒", "Free HTTPS", EMERALD),
            ),
            Step(
                title="Options, upgrades, uninstall", terminal_title="root@sms-server: ~",
                lines=[
                    ("cmd", "sudo bash install.sh --help"),
                    ("out", "  --mode <docker|systemd>   --version <tag|master>   --dir <path>"),
                    ("out", "  --domain <fqdn>           --port <port>            --with-ssl"),
                    ("out", "  --email <email>           --telnet-host <host>     --telnet-port <port>"),
                    ("out", "  --non-interactive         --uninstall"),
                    B,
                    ("comment", "# Pin a release / upgrade in place (configuration is preserved)"),
                    ("cmd", "sudo bash install.sh --mode docker --version 3.1.0 --non-interactive"),
                    B,
                    ("comment", "# Point systemd mode at an existing Jasmin server"),
                    ("cmd", "sudo bash install.sh --mode systemd --telnet-host 10.0.0.12"),
                    B,
                    ("comment", "# Remove the panel (database and env file are kept)"),
                    ("cmd", "sudo bash install.sh --uninstall"),
                ],
                narration=(
                    "[calm] Run the script with help to see every option. You can pin a release with the version "
                    "flag, change the web port, or point systemd mode at an existing Jasmin host. [happy] Running the "
                    "installer again simply upgrades in place, and keeps your configuration. [calm] And the uninstall "
                    "flag removes the application, but carefully preserves your database and your environment file."
                ),
                react=("♻️", "Upgrade in place", CYAN),
            ),
        ],
    ),
    # ------------------------------------------------------------------ 3. Docker
    Chapter(
        nav="Docker", blurb="Docker Compose full stack", accent=CYAN,
        emoji="🐳",
        hook=(
            "[happy] Chapter three. Docker Compose, the complete stack in about two minutes."
        ),
        badge="CONTAINERS  •  AMD64 & ARM64",
        title="Docker\nCompose",
        subtitle="The complete SMS stack on one host, in about two minutes.",
        bullets=[
            "Multi-arch images: tarekaec/jasmin_web_panel",
            "Panel, Celery, Postgres, Redis, RabbitMQ, Jasmin",
            "Migrations run automatically on every start",
            "Named volumes keep data and Jasmin config",
        ],
        steps=[
            Step(
                title="Clone & configure", terminal_title="ops@docker-host: ~",
                lines=[
                    ("cmd", "git clone https://github.com/101t/jasmin-web-panel.git"),
                    ("cmd", "cd jasmin-web-panel && cp sample.env .env"),
                    B,
                    ("comment", "# Generate strong secrets (run twice: SECRET_KEY + FIELD_ENCRYPTION_KEY)"),
                    ("cmd", "python3 -c 'import secrets; print(secrets.token_urlsafe(50))'"),
                    ("out", "q8Zp1x-7JfLk0w3yV9bTn2RmE5cHs6aGd4uQiOoXrW_eYtNvBk3sLp9aZx"),
                    ("cmd", "nano .env"),
                    ("out", "  SECRET_KEY=q8Zp1x-7JfLk0w3yV9bTn2RmE5cHs6aGd4uQiOoXrW_eYtNvBk3sLp9aZx"),
                    ("out", "  FIELD_ENCRYPTION_KEY=<another random value>"),
                    ("out", "  ALLOWED_HOSTS=sms.example.com,localhost"),
                    ("out", "  POSTGRES_PASSWORD=Str0ng-DB-Pass"),
                    ("out", "  PRODB_URL=postgres://jasmin:Str0ng-DB-Pass@db:5432/jasmin"),
                ],
                narration=(
                    "[calm] Docker Compose is the quickest way to run everything on one host. Clone the repository, "
                    "and copy the sample environment file. Then generate a strong secret key, and a field encryption "
                    "key, with Python's secrets module. [serious] Please, never keep the sample values in production. "
                    "The panel will actually warn you if it detects them."
                ),
                react=("🔑", "Strong secrets", EMERALD),
            ),
            Step(
                title="Start the stack", terminal_title="ops@docker-host: ~/jasmin-web-panel",
                lines=[
                    ("cmd", "docker compose up -d"),
                    ("out", "[+] Running 7/7"),
                    ("ok", " - Container jasmin-web-panel-db-1             Healthy"),
                    ("ok", " - Container jasmin-web-panel-redis-1          Healthy"),
                    ("ok", " - Container jasmin-web-panel-rabbitmq-1       Healthy"),
                    ("ok", " - Container jasmin-web-panel-jasmin-1         Started"),
                    ("ok", " - Container jasmin-web-panel-jasmin-web-1     Started"),
                    ("ok", " - Container jasmin-web-panel-jasmin-celery-1  Started"),
                    ("ok", " - Container jasmin-web-panel-sms_logger-1     Started"),
                    B,
                    ("cmd", "docker compose ps --format 'table {{.Service}}\\t{{.Status}}'"),
                    ("out", "SERVICE         STATUS"),
                    ("ok", "jasmin-web      Up 40 seconds (healthy)"),
                    ("ok", "jasmin          Up 45 seconds"),
                ],
                narration=(
                    "[calm] Now, start the stack with docker compose up, in detached mode. [excited] And boom! Seven "
                    "services, all up and running! [calm] The web panel, a Celery worker for exports, PostgreSQL, "
                    "Redis, RabbitMQ, the Jasmin gateway itself, and the submit log collector. [happy] The panel runs "
                    "its database migrations on every start, so upgrades need no manual steps at all."
                ),
                react=("🎉", "7/7 containers up", EMERALD),
            ),
            Step(
                title="Verify & panel-only mode", terminal_title="ops@docker-host: ~/jasmin-web-panel",
                lines=[
                    ("cmd", "curl -s http://localhost:8999/api/health_check"),
                    ("ok", '{"version": "3.1.0", "status": "ok"}'),
                    ("cmd", "docker compose logs -f --tail 20 jasmin-web"),
                    ("out", "[INFO] Starting gunicorn 23.0.0"),
                    ("out", "[INFO] Listening at: http://0.0.0.0:8000"),
                    B,
                    ("comment", "# Already running Jasmin elsewhere? Run only the panel:"),
                    ("cmd", "docker run -d --name jasmin-web -p 8999:8000 \\"),
                    ("cmd", "  --env-file .env -e TELNET_HOST=10.0.0.12 \\"),
                    ("cmd", "  tarekaec/jasmin_web_panel:3.1.0"),
                ],
                narration=(
                    "[calm] Let's check the health endpoint. It needs no login, and returns the running version. "
                    "[happy] Status, okay. Perfect. [calm] Follow the web logs while you open the panel on port 8999 "
                    "in your browser. And if Jasmin already runs somewhere else, you can start just the panel "
                    "container, and point the telnet host variable at your gateway."
                ),
                react=("🩺", "Healthy!", EMERALD),
            ),
            Step(
                title="Backup & upgrade", terminal_title="ops@docker-host: ~/jasmin-web-panel",
                lines=[
                    ("comment", "# 1) Always back up first"),
                    ("cmd", "docker compose exec -T db pg_dump -U jasmin jasmin | gzip > backup-$(date +%F).sql.gz"),
                    B,
                    ("comment", "# 2) Upgrade: pull new images and recreate containers"),
                    ("cmd", "docker compose pull && docker compose up -d"),
                    ("ok", "Container jasmin-web-panel-jasmin-web-1  Recreated"),
                    B,
                    ("comment", "# Restore, if ever needed"),
                    ("cmd", "gunzip -c backup-2026-11-20.sql.gz | docker compose exec -T db psql -U jasmin jasmin"),
                    B,
                    ("comment", "# Jasmin's own config (users, connectors, routes) lives in a named volume"),
                    ("cmd", "docker volume ls | grep jasmin_config"),
                    ("out", "local     jasmin-web-panel_jasmin_config"),
                ],
                narration=(
                    "[serious] Before any upgrade, always take a database backup with pg dump. [calm] Then, upgrading "
                    "takes just two commands: pull the new images, and recreate the containers. Jasmin's own "
                    "configuration, including users, connectors and routes, lives in the jasmin config named volume. "
                    "[happy] So it safely survives container recreation too."
                ),
                react=("📦", "Backup first, always", AMBER),
            ),
        ],
    ),
    # ------------------------------------------------------------------ 4. systemd
    Chapter(
        nav="Systemd", blurb="Native systemd + Nginx + SSL", accent=EMERALD,
        emoji="🐧",
        hook=(
            "[calm] Chapter four. A classic native install, with systemd, Nginx, and free HTTPS."
        ),
        badge="NATIVE LINUX  •  SYSTEMCTL + NGINX",
        title="systemd, Gunicorn\n& Nginx",
        subtitle="A step-by-step native installation for VMs and bare-metal servers.",
        bullets=[
            "Dedicated, non-login system user",
            "Isolated Python 3.12 environment managed by uv",
            "Hardened units for Gunicorn and Celery",
            "Nginx reverse proxy with Certbot TLS",
        ],
        steps=[
            Step(
                title="Packages & database", terminal_title="root@sms-server: ~",
                lines=[
                    ("cmd", "sudo apt update && sudo apt install -y postgresql redis-server nginx telnet git"),
                    B,
                    ("cmd", "sudo -u postgres psql"),
                    ("out", "postgres=# CREATE USER jasmin_web WITH PASSWORD 'Str0ng-DB-Pass';"),
                    ("ok", "CREATE ROLE"),
                    ("out", "postgres=# CREATE DATABASE jasmin_web OWNER jasmin_web;"),
                    ("ok", "CREATE DATABASE"),
                    ("out", "postgres=# \\c jasmin_web"),
                    ("out", "jasmin_web=# GRANT USAGE, CREATE ON SCHEMA public TO jasmin_web;"),
                    ("ok", "GRANT"),
                    B,
                    ("comment", "# Rocky / Alma / RHEL:  sudo dnf install -y postgresql-server redis nginx telnet git"),
                ],
                narration=(
                    "[calm] For a manual native installation, start with the system packages: PostgreSQL, Redis, "
                    "Nginx, and the telnet client, which the panel uses to talk to jcli. Then create a database, and "
                    "a dedicated database user. [serious] On PostgreSQL 15 and newer, don't forget to grant usage and "
                    "create on the public schema. Otherwise, the migrations will fail."
                ),
                react=("🐘", "Database ready", EMERALD),
            ),
            Step(
                title="Application & Python", terminal_title="root@sms-server: ~",
                lines=[
                    ("cmd", "sudo useradd --system --home-dir /opt/jasmin-web-panel \\"),
                    ("cmd", "  --shell /usr/sbin/nologin --user-group jasminpanel"),
                    ("cmd", "sudo git clone https://github.com/101t/jasmin-web-panel.git /opt/jasmin-web-panel"),
                    ("cmd", "curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin sh"),
                    B,
                    ("cmd", "cd /opt/jasmin-web-panel && sudo uv venv --python 3.12 env"),
                    ("out", "Using CPython 3.12.8"),
                    ("out", "Creating virtual environment at: env"),
                    ("cmd", "sudo uv pip install --python env/bin/python -r pyproject.toml --extra prod"),
                    ("ok", "Installed 48 packages in 1.92s"),
                ],
                narration=(
                    "[calm] Next, create a system user without a login shell, clone the code into opt jasmin web "
                    "panel, and build an isolated Python 3.12 environment with uv. [happy] The nice thing is, uv "
                    "downloads a managed Python for you. No extra repositories, and no compiling from source, even on "
                    "older distributions."
                ),
                react=("🐍", "Python 3.12 via uv", CYAN),
            ),
            Step(
                title="Configure & migrate", terminal_title="root@sms-server: /opt/jasmin-web-panel",
                lines=[
                    ("cmd", "sudo install -d -m 750 /etc/jasmin-web-panel"),
                    ("cmd", "sudo cp sample.env /etc/jasmin-web-panel/env && sudo nano /etc/jasmin-web-panel/env"),
                    ("out", "  PRODB_URL=postgres://jasmin_web:Str0ng-DB-Pass@127.0.0.1:5432/jasmin_web"),
                    ("out", "  REDIS_HOST=127.0.0.1"),
                    ("out", "  TELNET_HOST=127.0.0.1   TELNET_USERNAME=jcliadmin   TELNET_PW=********"),
                    ("cmd", "sudo ln -s /etc/jasmin-web-panel/env .env"),
                    ("cmd", "sudo chown -R jasminpanel: /opt/jasmin-web-panel /etc/jasmin-web-panel"),
                    B,
                    ("cmd", "sudo -u jasminpanel env/bin/python manage.py migrate"),
                    ("cmd", "sudo -u jasminpanel env/bin/python manage.py collectstatic --noinput"),
                    ("cmd", "sudo -u jasminpanel env/bin/python manage.py createsuperuser"),
                    ("ok", "Superuser created successfully."),
                ],
                narration=(
                    "[calm] Keep the configuration outside the code, in etc jasmin web panel env, readable only by "
                    "the service user. Set the secret keys, the database URL, the allowed hosts, and the jcli "
                    "credentials of your gateway. Then run the migrations, collect static files, and create your "
                    "administrator account. [happy] Superuser created. We're getting close!"
                ),
                react=("👤", "Admin created", EMERALD),
            ),
            Step(
                title="systemd services", terminal_title="root@sms-server: /opt/jasmin-web-panel",
                lines=[
                    ("cmd", "sudo cp packaging/systemd/jasmin-web.service \\"),
                    ("cmd", "  packaging/systemd/jasmin-celery.service /etc/systemd/system/"),
                    ("cmd", "sudo systemctl daemon-reload"),
                    ("cmd", "sudo systemctl enable --now jasmin-web jasmin-celery"),
                    B,
                    ("cmd", "systemctl status jasmin-web --no-pager"),
                    ("ok", "● jasmin-web.service - Jasmin Web Panel (Gunicorn WSGI)"),
                    ("ok", "     Active: active (running) since Fri 2026-11-20 18:30:02 UTC"),
                    ("out", "   Main PID: 4242 (gunicorn)"),
                    B,
                    ("cmd", "journalctl -u jasmin-web -f"),
                ],
                narration=(
                    "[calm] The repository ships hardened unit files for Gunicorn and for the Celery worker. They run "
                    "as the dedicated user, load the environment file, and use systemd sandboxing, like protect "
                    "system and private temp. Copy them, reload systemd, and enable both services, so they start at "
                    "boot. [happy] Active, and running. Lovely."
                ),
                react=("🛡️", "Hardened & running", EMERALD),
            ),
            Step(
                title="Nginx & HTTPS", terminal_title="root@sms-server: /opt/jasmin-web-panel",
                lines=[
                    ("cmd", "sed 's|__SERVER_NAME__|sms.example.com|g; s|__INSTALL_DIR__|/opt/jasmin-web-panel|g' \\"),
                    ("cmd", "  packaging/nginx/jasmin-web-panel.conf \\"),
                    ("cmd", "  | sudo tee /etc/nginx/sites-available/jasmin-web-panel"),
                    ("cmd", "sudo ln -s /etc/nginx/sites-available/jasmin-web-panel /etc/nginx/sites-enabled/"),
                    ("cmd", "sudo nginx -t && sudo systemctl reload nginx"),
                    ("ok", "nginx: configuration file /etc/nginx/nginx.conf test is successful"),
                    ("cmd", "sudo certbot --nginx -d sms.example.com --redirect"),
                    ("ok", "Successfully deployed certificate for sms.example.com"),
                    B,
                    ("comment", "# Then, in /etc/jasmin-web-panel/env:"),
                    ("warn", "  HTTPS_ONLY=True"),
                    ("warn", "  CSRF_TRUSTED_ORIGINS=https://sms.example.com"),
                    ("cmd", "sudo systemctl restart jasmin-web"),
                ],
                narration=(
                    "[calm] Finally, let's put Nginx in front. Use the template in the packaging folder, fill in the "
                    "server name and the install directory, enable the site, and test the configuration. Certbot then "
                    "grabs a certificate, and redirects HTTP to HTTPS. [excited] And just like that, you have HTTPS! "
                    "[serious] Last step: set HTTPS only to true, and add your domain to the CSRF trusted origins."
                ),
                react=("🔒", "HTTPS enabled", EMERALD),
            ),
        ],
    ),
    # ------------------------------------------------------------------ 5. Kubernetes
    Chapter(
        nav="Kubernetes", blurb="Kustomize, Ingress & scaling", accent=VIOLET,
        emoji="☸️",
        hook=(
            "[excited] Chapter five. Kubernetes! Let's go cloud native."
        ),
        badge="CLOUD NATIVE  •  HIGH AVAILABILITY",
        title="Kubernetes\nDeployment",
        subtitle="Ready-made Kustomize manifests in deploy/kubernetes.",
        bullets=[
            "initContainer runs migrations before Gunicorn",
            "No privilege escalation, CPU & memory limits",
            "Probes on the health check endpoint",
            "Ingress with cert-manager TLS",
        ],
        steps=[
            Step(
                title="Namespace & secrets", terminal_title="ops@k8s-admin: ~/jasmin-web-panel",
                lines=[
                    ("cmd", "kubectl create namespace jasmin-web"),
                    ("cmd", "SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"),
                    ("cmd", "FKEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"),
                    ("cmd", "kubectl -n jasmin-web create secret generic jasmin-web-secret \\"),
                    ("cmd", '  --from-literal=SECRET_KEY="$SECRET" \\'),
                    ("cmd", '  --from-literal=FIELD_ENCRYPTION_KEY="$FKEY" \\'),
                    ("cmd", '  --from-literal=PRODB_URL="postgres://jasmin:PASS@postgres:5432/jasmin" \\'),
                    ("cmd", '  --from-literal=TELNET_USERNAME="jcliadmin" --from-literal=TELNET_PW="PASS"'),
                    ("ok", "secret/jasmin-web-secret created"),
                    B,
                    ("comment", "# GitOps? Use Sealed Secrets or External Secrets instead of plain YAML."),
                ],
                narration=(
                    "[calm] The repository includes a ready-made Kustomize bundle, in the deploy kubernetes folder. "
                    "Start by creating the namespace, and a secret with your database URL, your jcli credentials, and "
                    "two random keys. [serious] Keep your secrets out of Git. [calm] For GitOps, use a tool like "
                    "Sealed Secrets, or External Secrets."
                ),
                react=("🔑", "Secrets stay out of Git", AMBER),
            ),
            Step(
                title="Configure & apply", terminal_title="ops@k8s-admin: ~/jasmin-web-panel",
                lines=[
                    ("cmd", "nano deploy/kubernetes/configmap.yaml"),
                    ("out", '  ALLOWED_HOSTS: "sms.example.com"'),
                    ("out", '  TELNET_HOST: "jasmin-service"'),
                    ("out", '  REDIS_HOST: "redis-service"'),
                    ("cmd", "kubectl apply -k deploy/kubernetes"),
                    ("out", "configmap/jasmin-web-config created"),
                    ("out", "service/jasmin-web created"),
                    ("out", "deployment.apps/jasmin-web created"),
                    ("out", "deployment.apps/jasmin-celery created"),
                    ("out", "ingress.networking.k8s.io/jasmin-web created"),
                    ("cmd", "kubectl -n jasmin-web rollout status deployment/jasmin-web"),
                    ("ok", 'deployment "jasmin-web" successfully rolled out'),
                ],
                narration=(
                    "[calm] Edit the config map with your domain, and the service names of Jasmin and Redis in your "
                    "cluster. Then apply the whole bundle with kubectl apply, dash k. [happy] A smart detail: an init "
                    "container runs the database migrations once, before the web pods start, so several replicas "
                    "never race each other at boot. [excited] Successfully rolled out!"
                ),
                react=("🚀", "Rolled out", EMERALD),
            ),
            Step(
                title="Ingress, probes & scaling", terminal_title="ops@k8s-admin: ~/jasmin-web-panel",
                lines=[
                    ("cmd", "kubectl -n jasmin-web get pods"),
                    ("out", "NAME                             READY   STATUS    RESTARTS   AGE"),
                    ("ok", "jasmin-web-7c9d8f6b54-2xk8p      1/1     Running   0          2m"),
                    ("ok", "jasmin-web-7c9d8f6b54-q4m7z      1/1     Running   0          2m"),
                    ("ok", "jasmin-celery-5f7b9c8d6-h2n4v    1/1     Running   0          2m"),
                    B,
                    ("cmd", "kubectl -n jasmin-web get ingress"),
                    ("out", "NAME         CLASS   HOSTS             ADDRESS        PORTS     AGE"),
                    ("ok", "jasmin-web   nginx   sms.example.com   203.0.113.10   80, 443   2m"),
                    B,
                    ("cmd", "kubectl -n jasmin-web scale deployment/jasmin-web --replicas=4"),
                    ("ok", "deployment.apps/jasmin-web scaled"),
                ],
                narration=(
                    "[calm] The ingress uses ingress nginx with cert manager, to issue a TLS certificate "
                    "automatically. Liveness and readiness probes call the health check endpoint, and the pods run "
                    "without privilege escalation, with resource limits. [excited] Need more capacity? Scale the web "
                    "tier horizontally, with one command."
                ),
                react=("📈", "Scaled to 4 replicas", EMERALD),
            ),
            Step(
                title="Rolling upgrades", terminal_title="ops@k8s-admin: ~/jasmin-web-panel",
                lines=[
                    ("comment", "# Example: move to a newer release tag"),
                    ("cmd", "kubectl -n jasmin-web set image deployment/jasmin-web \\"),
                    ("cmd", "  web=tarekaec/jasmin_web_panel:3.2.0 migrate=tarekaec/jasmin_web_panel:3.2.0"),
                    ("cmd", "kubectl -n jasmin-web set image deployment/jasmin-celery \\"),
                    ("cmd", "  worker=tarekaec/jasmin_web_panel:3.2.0"),
                    ("cmd", "kubectl -n jasmin-web rollout status deployment/jasmin-web"),
                    ("ok", 'deployment "jasmin-web" successfully rolled out'),
                    B,
                    ("comment", "# Something wrong? Roll back instantly"),
                    ("cmd", "kubectl -n jasmin-web rollout undo deployment/jasmin-web"),
                    ("ok", "deployment.apps/jasmin-web rolled back"),
                ],
                narration=(
                    "[calm] To upgrade, change the image tag, for example with kubectl set image, or with a Kustomize "
                    "image override. Kubernetes then performs a rolling update, with zero downtime. [happy] And if "
                    "anything goes wrong, relax. You can roll back to the previous revision instantly."
                ),
                react=("⏪", "Instant rollback", CYAN),
            ),
        ],
    ),
    # ------------------------------------------------------------------ 6. Packages
    Chapter(
        nav="Packages", blurb="Native .deb & .rpm packages", accent=CYAN,
        emoji="📦",
        hook=(
            "[happy] Chapter six. Native Debian and RPM packages, perfect for server fleets."
        ),
        badge="DEBIAN (.DEB)  •  RHEL / ROCKY (.RPM)",
        title="Native Linux\nPackages",
        subtitle="Built for amd64 and arm64 on every tagged release.",
        bullets=[
            "Install with apt or dnf from GitHub Releases",
            "SHA256SUMS published with every release",
            "Unique SECRET_KEY generated on first install",
            "Config files are never overwritten on upgrade",
        ],
        steps=[
            Step(
                title="Debian & Ubuntu", terminal_title="root@debian-server: ~",
                lines=[
                    ("cmd", "VER=3.2.0   # pick the latest release"),
                    ("cmd", "URL=https://github.com/101t/jasmin-web-panel/releases/download/$VER"),
                    ("cmd", "curl -LO $URL/jasmin-web-panel_${VER}-1_amd64.deb"),
                    ("cmd", "curl -LO $URL/SHA256SUMS.txt"),
                    ("cmd", "sha256sum --ignore-missing -c SHA256SUMS.txt"),
                    ("ok", "jasmin-web-panel_3.2.0-1_amd64.deb: OK"),
                    B,
                    ("cmd", "sudo apt install -y ./jasmin-web-panel_${VER}-1_amd64.deb"),
                    ("out", "Setting up jasmin-web-panel (3.2.0-1) ..."),
                    ("ok", " Jasmin Web Panel package installed!"),
                ],
                narration=(
                    "[calm] Every tagged release also publishes native Debian and RPM packages, for amd64 and arm64, "
                    "together with a checksum file. On Debian or Ubuntu, download the package, and verify its "
                    "checksum. [happy] It says OK, great! [calm] Now install it with apt, which resolves dependencies "
                    "like Python, lib pq and telnet automatically."
                ),
                react=("✅", "Checksum OK", EMERALD),
            ),
            Step(
                title="Rocky, Alma, RHEL & Fedora", terminal_title="root@rocky-server: ~",
                lines=[
                    ("cmd", "curl -LO $URL/jasmin-web-panel-${VER}-1.x86_64.rpm"),
                    ("cmd", "sudo dnf install -y ./jasmin-web-panel-${VER}-1.x86_64.rpm"),
                    ("ok", "Complete!"),
                    B,
                    ("comment", "# What the package set up for you"),
                    ("cmd", "id jasminpanel"),
                    ("out", "uid=995(jasminpanel) gid=992(jasminpanel) groups=992(jasminpanel)"),
                    ("cmd", "ls /lib/systemd/system/jasmin-*"),
                    ("out", "/lib/systemd/system/jasmin-celery.service  /lib/systemd/system/jasmin-web.service"),
                    ("cmd", "sudo grep -c '^SECRET_KEY=change-me' /etc/jasmin-web-panel/env"),
                    ("ok", "0      # a unique random key was generated"),
                ],
                narration=(
                    "[calm] On Rocky Linux, AlmaLinux, RHEL or Fedora, the flow is the same, with dnf. [happy] And "
                    "look at everything the package set up for you: the jasmin panel system user, the systemd units, "
                    "the Python environment, and even a unique secret key, generated on first install. [calm] "
                    "Upgrades never overwrite your existing configuration."
                ),
                react=("📦", "Set up for you", EMERALD),
            ),
            Step(
                title="Configure & start", terminal_title="root@linux-server: ~",
                lines=[
                    ("cmd", "sudo nano /etc/jasmin-web-panel/env"),
                    ("out", "  PRODB_URL=postgres://jasmin_web:Str0ng-DB-Pass@127.0.0.1:5432/jasmin_web"),
                    ("out", "  ALLOWED_HOSTS=sms.example.com"),
                    ("out", "  TELNET_HOST=127.0.0.1   TELNET_PW=********"),
                    B,
                    ("cmd", "cd /opt/jasmin-web-panel"),
                    ("cmd", "sudo -u jasminpanel env/bin/python manage.py migrate"),
                    ("cmd", "sudo -u jasminpanel env/bin/python manage.py createsuperuser"),
                    ("cmd", "sudo systemctl enable --now jasmin-web jasmin-celery"),
                    ("ok", "Created symlink /etc/systemd/system/multi-user.target.wants/jasmin-web.service"),
                    B,
                    ("comment", "# Nginx template: /etc/jasmin-web-panel/nginx.conf.example"),
                ],
                narration=(
                    "[calm] After installing a package, edit the environment file to set your database URL, allowed "
                    "hosts, and jcli credentials. Run the migrations, create an administrator, and enable the "
                    "services. An Nginx template is installed right next to the configuration, so you can publish the "
                    "panel exactly like in the systemd chapter."
                ),
                react=("🚀", "Services enabled", EMERALD),
            ),
        ],
    ),
    # ------------------------------------------------------------------ 7. First run
    Chapter(
        nav="First Run", blurb="Users, connectors, routes & first SMS", accent=EMERALD,
        emoji="✨",
        hook=(
            "[excited] Chapter seven. This is where the magic happens! Let's configure the gateway, and send "
            "our very first message."
        ),
        badge="FIRST RUN  •  UI + REST API",
        title="Configure Your\nGateway",
        subtitle="From empty gateway to your first delivered message.",
        bullets=[
            "Change the bootstrap admin password",
            "Create groups and Jasmin users",
            "Connect a carrier over SMPP",
            "Add routes, then send a test SMS",
        ],
        steps=[
            Step(
                title="Sign in & change password", terminal_title="ops@docker-host: ~/jasmin-web-panel",
                lines=[
                    ("comment", "# Sign in at https://sms.example.com with admin / secret"),
                    ("comment", "# then change the password right away:"),
                    ("cmd", "docker compose exec jasmin-web python manage.py changepassword admin"),
                    ("out", "Changing password for user 'admin'"),
                    ("out", "Password: ************"),
                    ("out", "Password (again): ************"),
                    ("ok", "Password changed successfully for user 'admin'"),
                    B,
                    ("comment", "# systemd and package installs"),
                    ("cmd", "sudo -u jasminpanel /opt/jasmin-web-panel/env/bin/python \\"),
                    ("cmd", "  /opt/jasmin-web-panel/manage.py changepassword admin"),
                ],
                narration=(
                    "[calm] Open the panel, and sign in with the bootstrap account: admin, with the password, secret. "
                    "[serious] Now, change it immediately, either from your profile page, or from the command line. "
                    "[calm] New passwords must pass Django's validators, so short or common passwords are rejected. "
                    "And the default admin is only ever created on an empty database."
                ),
                react=("🔐", "Password changed", EMERALD),
            ),
            Step(
                title="Groups & users", terminal_title="ops@laptop: ~  (REST API)",
                lines=[
                    ("cmd", "export PANEL=https://sms.example.com AUTH='admin:N3w-Adm1n-Pass'"),
                    ("cmd", "export JSON='Content-Type: application/json'"),
                    B,
                    ("cmd", 'curl -u $AUTH -H "$JSON" -d \'{"gid": "customers"}\' $PANEL/api/groups/'),
                    ("ok", '{"name": "customers"}'),
                    B,
                    ("cmd", 'curl -u $AUTH -H "$JSON" $PANEL/api/users/ \\'),
                    ("cmd", '  -d \'{"uid": "acme", "gid": "customers", "username": "acme", "password": "Acme-2026"}\''),
                    ("ok", '{"user": {"uid": "acme", "gid": "customers", "username": "acme", ...}}'),
                    B,
                    ("comment", "# Same actions in the UI: Users -> Groups / Users -> Add"),
                ],
                narration=(
                    "[happy] Everything in the user interface is also available through the REST API, which is "
                    "fantastic for automation. [calm] Only staff accounts can call it. Here, we create a customers "
                    "group, and a Jasmin user named acme. These are gateway users who send SMS, separate from the "
                    "panel's own login accounts."
                ),
                react=("👥", "Customer created", EMERALD),
            ),
            Step(
                title="Connect a carrier (SMPP)", terminal_title="ops@laptop: ~  (REST API)",
                lines=[
                    ("cmd", 'curl -u $AUTH -H "$JSON" $PANEL/api/smppccm/ -d \'{"cid": "carrier1",'),
                    ("cmd", '  "host": "smsc.carrier.net", "port": 2775, "username": "acct", "password": "pw"}\''),
                    ("ok", '{"cid": "carrier1"}'),
                    B,
                    ("cmd", "curl -u $AUTH -X PUT $PANEL/api/smppccm/carrier1/start/"),
                    ("ok", '{"name": "carrier1"}'),
                    B,
                    ("cmd", "curl -u $AUTH $PANEL/api/smppccm/carrier1/"),
                    ("ok", '{"connector": {"cid": "carrier1", "status": "started",'),
                    ("ok", '               "session": "BOUND_TRX", "password": "********", ...}}'),
                ],
                narration=(
                    "[calm] Next, let's connect to your SMS provider. Create an SMPP client connector with the "
                    "carrier's host, port and credentials, and then start it. [excited] Look, the session shows bound "
                    "transceiver. We're connected! [happy] And notice that the carrier password is masked, in every "
                    "API response."
                ),
                react=("📡", "Carrier connected", EMERALD),
            ),
            Step(
                title="Filters & MT routes", terminal_title="ops@laptop: ~  (REST API)",
                lines=[
                    ("comment", "# Default route: all traffic via carrier1 at 0.01 per message"),
                    ("cmd", 'curl -u $AUTH -H "$JSON" $PANEL/api/mtrouter/ \\'),
                    ("cmd", '  -d \'{"type": "DefaultRoute", "smppconnectors": ["carrier1"], "rate": "0.01"}\''),
                    B,
                    ("comment", "# Cheaper route for numbers starting with 971"),
                    ("cmd", 'curl -u $AUTH -H "$JSON" $PANEL/api/filters/ \\'),
                    ("cmd", '  -d \'{"type": "DestinationAddrFilter", "fid": "uae", "parameter": "^971"}\''),
                    ("cmd", 'curl -u $AUTH -H "$JSON" $PANEL/api/mtrouter/ -d \'{"type": "StaticMTRoute",'),
                    ("cmd", '  "order": "10", "smppconnectors": ["carrier1"], "filters": ["uae"], "rate": "0.008"}\''),
                    ("ok", '{"mtrouter": {"order": "10", "type": "StaticMTRoute", "rate": "0.00800", ...}}'),
                ],
                narration=(
                    "[calm] Now, let's tell Jasmin where to send messages. A default MT route sends all traffic "
                    "through carrier one, at a rate of one cent. Then we add a destination filter for numbers "
                    "starting with 971, and a static route with a higher order, so those messages use a cheaper rate. "
                    "[soft] Remember, routes with a higher order are evaluated first."
                ),
                react=("🧭", "Routes ready", EMERALD),
            ),
            Step(
                title="Send a test SMS", terminal_title="ops@laptop: ~",
                lines=[
                    ("comment", "# Through Jasmin's HTTP API (port 1401) as the 'acme' user"),
                    ("cmd", "curl -X POST http://sms.example.com:1401/send \\"),
                    ("cmd", "  -d username=acme -d password=Acme-2026 \\"),
                    ("cmd", "  -d to=971500000000 -d 'content=Hello from Jasmin Web Panel'"),
                    ("ok", 'Success "0b4f7e1c-6a2d-4c3e-9a51-7f2d8e9c1a33"'),
                    B,
                    ("comment", "# Or use the UI: Send SMS -> choose HTTP or SMPP -> pick the user"),
                    ("comment", "# Long messages are split into multipart SMS automatically."),
                ],
                narration=(
                    "[excited] Okay, the moment of truth! [calm] Let's send a real test SMS through Jasmin's HTTP "
                    "API, on port 1401, using the acme credentials. [excited] Success, with a message ID! Our very "
                    "first message is on its way! [happy] You can also use the Send SMS page in the panel, which "
                    "supports both HTTP and SMPP, including long multipart messages."
                ),
                react=("🎉", "First SMS sent!", EMERALD),
            ),
        ],
    ),
    # ------------------------------------------------------------------ 8. Logs
    Chapter(
        nav="Logs", blurb="Submit Log, dashboard & troubleshooting", accent=VIOLET,
        emoji="📊",
        hook=(
            "[calm] Chapter eight. The Submit Log, monitoring, and troubleshooting."
        ),
        badge="OBSERVABILITY  •  SUBMIT LOG",
        title="Submit Log &\nMonitoring",
        subtitle="Track every message, its cost and its delivery receipt.",
        bullets=[
            "Status, rate and DLR for every message",
            "Search, filter and export to CSV / Excel",
            "Timeline charts on the dashboard",
            "Clear error messages when jcli is unreachable",
        ],
        steps=[
            Step(
                title="Enable the Submit Log", terminal_title="ops@docker-host: ~/jasmin-web-panel",
                lines=[
                    ("comment", "# jasmin.cfg"),
                    ("out", "[sm-listener]"),
                    ("out", "publish_submit_sm_resp = True"),
                    ("cmd", "docker compose cp ./jasmin.cfg jasmin:/etc/jasmin/jasmin.cfg"),
                    ("cmd", "docker compose restart jasmin"),
                    B,
                    ("comment", "# panel .env"),
                    ("out", "SUBMIT_LOG=True"),
                    ("cmd", "docker compose logs -f sms_logger"),
                    ("out", "[INFO] Connected to broker, authenticating guest"),
                    ("ok", "[INFO] Ready to receive messages (prefetch=50)"),
                ],
                narration=(
                    "[calm] The submit log records every message, with its status, cost, and delivery report. In "
                    "Jasmin's configuration, enable publish submit sm resp, in the sm listener section, and restart "
                    "Jasmin. Then, in the panel, set submit log to true. [happy] With Docker Compose, the sms logger "
                    "service is already running, and ready to receive messages."
                ),
                react=("📬", "Logger listening", EMERALD),
            ),
            Step(
                title="Dashboard & exports", terminal_title="ops@docker-host: ~/jasmin-web-panel",
                lines=[
                    ("comment", "# The data behind the Submit Log page"),
                    ("cmd", "docker compose exec db psql -U jasmin -c \\"),
                    ("cmd", '  "SELECT status, count(*) FROM submit_log GROUP BY status;"'),
                    ("out", "        status         | count"),
                    ("out", "-----------------------+-------"),
                    ("ok", " ESME_ROK              | 18452"),
                    ("ok", " DELIVRD               | 17930"),
                    ("warn", " ESME_RDELIVERYFAILURE |    41"),
                    B,
                    ("comment", "# In the UI: Submit Logs -> search, filter by status/date, Export CSV / XLSX"),
                    ("comment", "# Exports run in Celery and are private to the requesting user."),
                ],
                narration=(
                    "[happy] Now the fun part, the data! [calm] On the dashboard, you see total, successful and "
                    "failed messages, with a timeline by day, week, month, or year. The submit log page lets you "
                    "search by message ID, address, user, or content, filter by status and date, and export the "
                    "results to CSV or Excel in the background. [soft] And exports stay private, to the user who "
                    "requested them."
                ),
                react=("📊", "Every message tracked", CYAN),
            ),
            Step(
                title="Troubleshooting", terminal_title="root@sms-server: ~",
                lines=[
                    ("cmd", "telnet 127.0.0.1 8990"),
                    ("out", "Authentication required."),
                    ("out", "Username: jcliadmin"),
                    ("out", "Password: ********"),
                    ("ok", "Welcome to Jasmin console"),
                    ("ok", "jcli : "),
                    B,
                    ("cmd", "journalctl -u jasmin-web -n 50 --no-pager        # systemd"),
                    ("cmd", "docker compose logs --tail 50 jasmin-web         # docker"),
                    B,
                    ("comment", "# 'permission denied for schema public' on PostgreSQL 15+"),
                    ("cmd", "sudo -u postgres psql -d jasmin_web -c 'GRANT USAGE, CREATE ON SCHEMA public TO jasmin_web;'"),
                ],
                narration=(
                    "[soft] If something goes wrong, don't panic. [calm] If a page says it cannot connect to jcli, "
                    "check that Jasmin is running, and that port 8990 is reachable from the panel, with telnet. Login "
                    "failures mean the telnet username or password is wrong. Permission denied for schema public "
                    "means the PostgreSQL grant is missing. [happy] And the service logs always include the exact "
                    "reason."
                ),
                react=("🩺", "Check jcli first", CYAN),
            ),
        ],
    ),
    # ------------------------------------------------------------------ 9. Security
    Chapter(
        nav="Security", blurb="Production hardening checklist", accent=AMBER,
        emoji="🛡️",
        hook=(
            "[serious] Chapter nine. Production security. Please, don't skip this one."
        ),
        badge="PRODUCTION CHECKLIST  •  HARDENING",
        title="Production\nSecurity",
        subtitle="Lock down your SMS gateway before inviting operators.",
        bullets=[
            "DEBUG off, strong keys, strict ALLOWED_HOSTS",
            "HTTPS only, HSTS and secure cookies",
            "Never expose jcli port 8990 publicly",
            "Staff-only panel and REST API access",
        ],
        steps=[
            Step(
                title="Application settings", terminal_title="/etc/jasmin-web-panel/env",
                lines=[
                    ("comment", "# Production checklist"),
                    ("warn", "  DEBUG=False"),
                    ("warn", "  SECRET_KEY=<50+ random characters>"),
                    ("warn", "  FIELD_ENCRYPTION_KEY=<a different 50+ random characters>"),
                    ("warn", "  ALLOWED_HOSTS=sms.example.com"),
                    ("warn", "  HTTPS_ONLY=True"),
                    ("warn", "  SECURE_HSTS_SECONDS=31536000"),
                    ("warn", "  CSRF_TRUSTED_ORIGINS=https://sms.example.com"),
                    ("warn", "  ALLOW_EVALPY_FILTER=False        # EvalPy runs Python inside Jasmin"),
                ],
                narration=(
                    "[serious] Before going live, review your application settings carefully. Debug must be false. "
                    "[calm] Use long random secret and encryption keys, and set the field encryption key before you "
                    "ever rotate the secret key. Restrict the allowed hosts to your domain, enable HTTPS only behind "
                    "TLS, and keep the risky EvalPy filter disabled, unless you truly need it."
                ),
                react=("🛡️", "Production checklist", AMBER),
            ),
            Step(
                title="Network & accounts", terminal_title="root@sms-server: ~",
                lines=[
                    ("comment", "# Keep jcli private: plain-text protocol with full gateway control"),
                    ("cmd", "sudo ufw allow 443/tcp && sudo ufw allow 2775/tcp"),
                    ("cmd", "sudo ufw deny 8990/tcp"),
                    ("ok", "Rule added"),
                    B,
                    ("comment", "# docker-compose.override.yml (created by the installer)"),
                    ("out", '  ports: ["127.0.0.1:8990:8990"]'),
                    B,
                    ("comment", "# Change default RabbitMQ / database passwords, then keep updating"),
                    ("cmd", "docker compose pull && docker compose up -d"),
                    B,
                    ("ok", "  Security reports: tarek.it.eng@gmail.com  (see SECURITY.md)"),
                ],
                narration=(
                    "[serious] Next, the network. jcli is a plain text protocol, with full control of your gateway. "
                    "So never, ever expose port 8990 to the internet. [calm] Keep it on localhost, a private network, "
                    "or a VPN. Change the default RabbitMQ and database passwords, give panel access only to staff "
                    "you trust, and keep the panel and its images up to date. [happy] Do this, and you can sleep well "
                    "at night."
                ),
                react=("🚫", "Never expose port 8990", ROSE),
            ),
        ],
    ),
]


# --------------------------------------------------------------------------------------
# Narration parsing & word alignment
# --------------------------------------------------------------------------------------
MOOD_TAG = re.compile(r"\[(" + "|".join(MOODS) + r")\]\s*")


def mood_runs(text: str) -> List[Tuple[str, str]]:
    """Split tagged narration into (mood, text) runs; consecutive runs of the same mood are merged."""
    parts = MOOD_TAG.split(text)
    runs = [("calm", parts[0].strip())] if parts[0].strip() else []
    runs += [(m, t.strip()) for m, t in zip(parts[1::2], parts[2::2]) if t.strip()]
    merged: List[Tuple[str, str]] = []
    for mood, t in runs:
        if merged and merged[-1][0] == mood:
            merged[-1] = (mood, merged[-1][1] + " " + t)
        else:
            merged.append((mood, t))
    return merged


def plain(text: str) -> str:
    return MOOD_TAG.sub("", text).strip()


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def align_words(words: List[str], events: List[Tuple[float, float, str]], dur: float) -> List[Tuple[float, float]]:
    """Map TTS word-boundary events (which may merge tokens, e.g. 'Version 3.12') onto caption words.
    Words without a matching event are interpolated between their neighbours."""
    out: List[Optional[Tuple[float, float]]] = [None] * len(words)
    i = 0
    for t0, t1, txt in events:
        target = _norm(txt)
        if not target:
            continue
        for j in range(i, min(i + 6, len(words))):
            if not _norm(words[j]):  # punctuation-only tokens get interpolated instead
                continue
            acc, k = "", j
            while k < len(words) and len(acc) < len(target):
                acc += _norm(words[k])
                k += 1
            if acc == target:
                n = k - j
                for m in range(j, k):
                    out[m] = (t0 + (t1 - t0) * (m - j) / n, t0 + (t1 - t0) * (m - j + 1) / n)
                i = k
                break
    m = 0
    while m < len(out):
        if out[m] is not None:
            m += 1
            continue
        e = m
        while e < len(out) and out[e] is None:
            e += 1
        a = out[m - 1][1] if m > 0 else 0.0
        b = max(a, out[e][0] if e < len(out) else dur)
        for q in range(m, e):
            out[q] = (a + (b - a) * (q - m) / (e - m), a + (b - a) * (q - m + 1) / (e - m))
        m = e
    return out  # type: ignore[return-value]


def build_phrases(words: List[Tuple[float, float, str]]) -> List[Tuple[int, int]]:
    """Group words into one-line caption phrases (<= ~62 chars, broken at sentence ends and commas)."""
    phrases, i0, length = [], 0, 0
    for i, (_, _, w) in enumerate(words):
        length += len(w) + 1
        nxt = len(words[i + 1][2]) + 1 if i + 1 < len(words) else 0
        if (w[-1:] in ".!?" or (w[-1:] in ",;:" and length >= 28) or length + nxt > 62
                or i == len(words) - 1):
            phrases.append((i0, i + 1))
            i0, length = i + 1, 0
    return phrases


# --------------------------------------------------------------------------------------
# Segment model
# --------------------------------------------------------------------------------------
@dataclass
class Chunk:
    mood: str
    text: str
    dur: float = 0.0
    offset: float = 0.0                      # segment-local start time
    events: List[Tuple[float, float, str]] = field(default_factory=list)


@dataclass
class Segment:
    kind: str                                # intro | card | step | outro
    narration: str
    chapter: int                             # -1 intro, len(CHAPTERS) outro
    step: int = 0
    chunks: List[Chunk] = field(default_factory=list)
    speech_start: float = 0.0
    speech_end: float = 0.0
    duration: float = 8.0
    start: float = 0.0
    words: List[Tuple[float, float, str]] = field(default_factory=list)
    phrases: List[Tuple[int, int]] = field(default_factory=list)
    env: Optional[np.ndarray] = None         # per-frame voice level 0..1 (narrator badge)

    @property
    def chapter_obj(self) -> Optional[Chapter]:
        return CHAPTERS[self.chapter] if 0 <= self.chapter < len(CHAPTERS) else None

    @property
    def step_obj(self) -> Optional[Step]:
        return self.chapter_obj.steps[self.step] if self.kind == "step" else None

    @property
    def accent(self):
        ch = self.chapter_obj
        return ch.accent if ch else (EMERALD if self.kind == "outro" else CYAN)

    @property
    def last_in_chapter(self) -> bool:
        return self.kind == "step" and self.step == len(self.chapter_obj.steps) - 1


def build_segments() -> List[Segment]:
    segs = [Segment("intro", INTRO_NARRATION, -1)]
    for ci, ch in enumerate(CHAPTERS):
        segs.append(Segment("card", ch.hook, ci))
        for si, st in enumerate(ch.steps):
            segs.append(Segment("step", st.narration, ci, si))
    segs.append(Segment("outro", OUTRO_NARRATION, len(CHAPTERS)))
    for seg in segs:
        seg.chunks = [Chunk(m, t) for m, t in mood_runs(seg.narration)]
    return segs


def layout(segs: List[Segment]) -> float:
    """Place every chunk on the timeline, derive word/phrase timings and frame-exact durations."""
    t = 0.0
    for seg in segs:
        cur = LEAD[seg.kind]
        seg.words = []
        for c in seg.chunks:
            c.offset = cur
            toks = c.text.split()
            for (a, b), w in zip(align_words(toks, c.events, c.dur), toks):
                seg.words.append((cur + a, cur + b, w))
            cur += c.dur + GAP
        seg.speech_start, seg.speech_end = LEAD[seg.kind], cur - GAP
        hold = {"intro": 1.2, "card": 1.1, "outro": 5.5}.get(
            seg.kind, HOLD + (CHAPTER_EXTRA if seg.last_in_chapter else 0.0))
        d = max(seg.speech_end + hold, 3.6 if seg.kind == "card" else 0.0)
        seg.duration = math.ceil(d * FPS) / FPS      # frame-exact, so audio and video never drift
        seg.start = t
        t += seg.duration
        seg.phrases = build_phrases(seg.words)
    return t


# --------------------------------------------------------------------------------------
# Shared timing for picture and sound (terminal typing, stickers, outro click)
# --------------------------------------------------------------------------------------
TX1, TY1, TX2, TY2 = 724, 118, 1864, 918


def line_weights(lines: List[Line]) -> List[float]:
    return [max(len(t), 4) * 1.0 if k == "cmd" else 10.0 if k == "blank" else 16.0 for k, t in lines]


def term_rows(seg: Segment) -> List[Tuple[str, str, float, float, int]]:
    """(kind, text, reveal_start, reveal_end, y) per terminal line."""
    st = seg.step_obj
    weights = line_weights(st.lines)
    total = sum(weights) or 1
    t0 = seg.speech_start + 0.35
    window = max(2.5, (seg.speech_end - seg.speech_start) * 0.7)
    rows, cum, y = [], 0.0, TY1 + 70
    for (kind, text), w in zip(st.lines, weights):
        rows.append((kind, text, t0 + window * cum / total, t0 + window * (cum + w) / total, y))
        y += 14 if kind == "blank" else (33 if st.diagram else 34)
        cum += w
    return rows


STICKER_LIFE = 3.4


def stickers(seg: Segment) -> List[Tuple[float, str, str, Tuple[int, int, int]]]:
    if seg.kind != "step":
        return []
    st, rows, out = seg.step_obj, term_rows(seg), []
    warn_t = next((r[2] for r in rows if r[0] == "warn"), None)
    if warn_t is not None and not (st.react and st.react[2] in (AMBER, ROSE)):
        out.append((warn_t + 0.15, "⚠️", "Heads up!", AMBER))
    if st.react:
        t = rows[-1][3] + 0.25
        if out and abs(out[0][0] - t) < 1.0:
            t = out[0][0] + 1.0
        out.append((t, *st.react))
    return out


def outro_click_time(seg: Segment) -> float:
    """The cursor clicks 'Star' exactly when Ava says 'star'."""
    return next((a for a, _, w in seg.words if _norm(w) == "star"), 6.0)


INTRO_CARD_T0, INTRO_CARD_DT = 2.4, 0.32
BULLET_T0, BULLET_DT = 0.5, 0.6


# --------------------------------------------------------------------------------------
# Audio: TTS, voice track, sound effects, generated music, mix
# --------------------------------------------------------------------------------------
async def synthesize(segs: List[Segment], tmp: Path, voice: str) -> List[List[Path]]:
    import edge_tts

    sem = asyncio.Semaphore(5)
    paths = [[tmp / f"v_{i:03d}_{j}.mp3" for j in range(len(s.chunks))] for i, s in enumerate(segs)]

    async def one(i: int, j: int):
        c, out = segs[i].chunks[j], paths[i][j]
        rate, pitch, volume = MOODS[c.mood]
        async with sem:
            last_err = None
            for attempt in range(5):
                try:
                    comm = edge_tts.Communicate(c.text, voice, rate=rate, pitch=pitch, volume=volume,
                                                boundary="WordBoundary")
                    data, events = bytearray(), []
                    async for ch in comm.stream():
                        if ch["type"] == "audio":
                            data += ch["data"]
                        elif ch["type"] == "WordBoundary":
                            events.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
                    if not data:
                        raise RuntimeError("empty audio")
                    out.write_bytes(bytes(data))
                    c.events = events
                    return
                except Exception as exc:  # network hiccups / throttling
                    last_err = exc
                    await asyncio.sleep(1.5 * (attempt + 1))
            raise RuntimeError(f"TTS failed for segment {i} chunk {j}: {last_err}")

    await asyncio.gather(*(one(i, j) for i, s in enumerate(segs) for j in range(len(s.chunks))))
    return paths


def decode(ffmpeg: str, path: Path) -> np.ndarray:
    raw = subprocess.run([ffmpeg, "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    pcm = np.frombuffer(raw, np.float32).copy()
    loud = np.nonzero(np.abs(pcm) > 0.008)[0]
    return pcm[: loud[-1] + int(0.1 * SR)] if len(loud) else pcm  # trim trailing silence: tighter pacing


def tt(d: float) -> np.ndarray:
    return np.arange(int(d * SR), dtype=np.float32) / SR


def _peak1(x: np.ndarray) -> np.ndarray:
    return (x / (np.max(np.abs(x)) + 1e-9)).astype(np.float32)


def bell(f: float, d: float = 1.4) -> np.ndarray:
    t = tt(d)
    parts = [(1.0, 1.0, 0.45), (2.0, 0.35, 0.25), (2.76, 0.25, 0.15), (5.4, 0.08, 0.06)]
    return sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / dec) for m, a, dec in parts) * np.minimum(1, t / 0.002)


def sfx_bank() -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(3)
    bank: Dict[str, np.ndarray] = {}
    # whoosh: noise through a one-pole low-pass whose cutoff sweeps up and back down
    n = int(0.75 * SR)
    noise = rng.standard_normal(n)
    shape = np.sin(np.pi * np.linspace(0, 1, n))
    coef = np.exp(-2 * np.pi * (250 + 4500 * shape ** 2) / SR)
    y, s = np.empty(n), 0.0
    for i in range(n):
        s = coef[i] * s + (1 - coef[i]) * noise[i]
        y[i] = s
    bank["whoosh"] = _peak1(y * shape ** 1.5)
    for k in range(6):  # keyboard clicks
        t = tt(0.03)
        burst = np.diff(rng.standard_normal(len(t)), prepend=0) * np.exp(-t / 0.0025)
        knock = 0.6 * np.sin(2 * np.pi * rng.uniform(1500, 2600) * t) * np.exp(-t / 0.006)
        bank[f"key{k}"] = _peak1(burst + knock)
    t = tt(0.14)
    bank["pop"] = _peak1(np.sin(2 * np.pi * np.cumsum(380 + 900 * np.exp(-t * 18)) / SR) * np.exp(-t / 0.035))
    ding = bell(1318.5)
    ding[int(0.09 * SR):] += 0.8 * bell(1975.5)[: len(ding) - int(0.09 * SR)]
    bank["ding"] = _peak1(ding)
    t1, t2 = tt(0.16), tt(0.34)
    bank["warn"] = _peak1(np.concatenate([np.sin(2 * np.pi * 659.3 * t1) * np.exp(-t1 / 0.08),
                                          np.sin(2 * np.pi * 523.3 * t2) * np.exp(-t2 / 0.12)]))
    t = tt(0.4)
    bank["thump"] = _peak1(np.sin(2 * np.pi * np.cumsum(55 + 90 * np.exp(-t * 30)) / SR) * np.exp(-t / 0.12))
    chime = np.zeros(int(1.8 * SR))
    for i, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):  # C6 E6 G6 C7 arpeggio
        b = bell(f, 1.4)
        chime[int(i * 0.08 * SR): int(i * 0.08 * SR) + len(b)] += b * (0.9 - i * 0.1)
    bank["chime"] = _peak1(chime)
    t = tt(0.05)
    click = np.diff(rng.standard_normal(len(t)), prepend=0) * np.exp(-t / 0.004)
    bank["mclick"] = _peak1(np.concatenate([click, np.zeros(int(0.06 * SR)), 0.6 * click]))
    sparkle = np.zeros(int(1.2 * SR))
    for _ in range(9):
        b = bell(rng.uniform(2500, 4200), 0.5) * rng.uniform(0.3, 0.8)
        o = int(rng.uniform(0, 0.6) * SR)
        sparkle[o: o + len(b)] += b
    bank["sparkle"] = _peak1(sparkle)
    return bank


SFX_GAIN = {"whoosh": 0.13, "key": 0.05, "pop": 0.08, "ding": 0.11, "warn": 0.09, "thump": 0.2,
            "chime": 0.13, "mclick": 0.12, "sparkle": 0.06}


def sfx_events(segs: List[Segment]) -> List[Tuple[float, str, float]]:
    """(absolute time, sound, gain): derived from the same timings the renderer uses."""
    rng = np.random.default_rng(5)
    ev: List[Tuple[float, str, float]] = []
    for seg in segs:
        T = seg.start
        if seg.kind == "intro":
            ev += [(T + 0.05, "whoosh", 0.8), (T + 0.55, "chime", 1.0)]
            ev += [(T + INTRO_CARD_T0 + i * INTRO_CARD_DT, "pop", 0.35) for i in range(len(CHAPTERS))]
        elif seg.kind == "card":
            ev += [(T, "whoosh", 1.0), (T + 0.35, "thump", 1.0), (T + 0.45, "pop", 0.6)]
        elif seg.kind == "outro":
            tc = outro_click_time(seg)
            ev += [(T + 0.8 + i * 0.35, "pop", 0.4) for i in range(3)]
            ev += [(T + tc, "mclick", 1.0), (T + tc + 0.03, "ding", 0.9), (T + tc + 0.05, "sparkle", 1.0)]
        else:
            if seg.step:
                ev.append((T, "whoosh", 0.3))
            else:
                ev += [(T + BULLET_T0 + i * BULLET_DT, "pop", 0.25) for i in range(len(seg.chapter_obj.bullets))]
            for kind, text, a, b, _ in term_rows(seg):
                if kind != "cmd":
                    continue
                last = -1.0
                for j, ch in enumerate(text):
                    t = a + (b - a) * j / max(1, len(text))
                    if ch != " " and t - last >= 0.055:  # fast typing would buzz; keep clicks distinct
                        ev.append((T + t, f"key{rng.integers(6)}", float(rng.uniform(0.5, 1.0))))
                        last = t
                ev.append((T + b + 0.04, f"key{rng.integers(6)}", 1.3))  # Enter
            for t, _, _, color in stickers(seg):
                ev.append((T + t, "ding" if color == EMERALD else "warn" if color in (AMBER, ROSE) else "pop", 0.9))
    return ev


def mtof(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def make_music(n: int, seed: int = 11) -> np.ndarray:
    """Generated ambient lo-fi bed: warm pad, soft echoing arpeggio, round bass, light hats."""
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2), np.float32)
    arp = np.zeros((n, 2), np.float32)
    beat = 60 / 84
    chords = [(41, [53, 57, 60, 64]), (43, [55, 59, 62, 64]), (40, [52, 55, 59, 62]), (45, [57, 60, 64, 67])]

    def add(buf, start, sig, gl, gr):
        s0 = int(start * SR)
        if s0 >= n:
            return
        sig = sig[: n - s0]
        buf[s0: s0 + len(sig), 0] += sig * gl
        buf[s0: s0 + len(sig), 1] += sig * gr

    t, ci, total = 0.0, 0, n / SR
    while t < total:
        root, notes = chords[ci % 4]
        cd = 8 * beat
        L = min(n - int(t * SR), int((cd + 1.6) * SR))
        x = np.arange(L, dtype=np.float32) / SR
        env = np.minimum(1, x / 1.2) * np.clip((cd + 1.6 - x) / 1.6, 0, 1)
        pl, pr = np.zeros(L, np.float32), np.zeros(L, np.float32)
        for m in notes:
            f = mtof(m)
            pl += np.sin(2 * np.pi * f * 0.9985 * x) + 0.15 * np.sin(4 * np.pi * f * x)
            pr += np.sin(2 * np.pi * f * 1.0015 * x) + 0.15 * np.sin(4 * np.pi * f * x + 0.5)
        add(out, t, 0.05 * env * pl, 1, 0)
        add(out, t, 0.05 * env * pr, 0, 1)
        bx = tt(1.2)
        bass = (np.sin(2 * np.pi * mtof(root) * bx) + 0.2 * np.sin(4 * np.pi * mtof(root) * bx)) \
            * np.exp(-bx / 0.5) * np.minimum(1, bx / 0.01)
        for bt in (0, 2.5, 4, 6.5):
            add(out, t + bt * beat, 0.09 * bass, 0.5, 0.5)
        pattern = rng.permutation(4).tolist() + rng.integers(0, 4, 4).tolist()
        for e in range(16):
            if rng.random() < 0.3:
                continue
            f = mtof(notes[pattern[e % 8]] + 12)
            px = tt(0.9)
            pl_sig = (np.sin(2 * np.pi * f * px) + 0.25 * np.sin(4 * np.pi * f * px) + 0.08 * np.sin(6 * np.pi * f * px)) \
                * np.exp(-px / 0.32) * np.minimum(1, px / 0.004)
            g = 0.035 * rng.uniform(0.6, 1.0)
            pan = 0.65 if e % 2 else 0.35
            add(arp, t + e * beat / 2, g * pl_sig, 1 - pan, pan)
            if e % 2 and rng.random() < 0.6 and t > 4 * cd:  # hats join after the intro
                hx = tt(0.08)
                add(out, t + e * beat / 2, 0.012 * np.diff(rng.standard_normal(len(hx)), prepend=0)
                    * np.exp(-hx / 0.018), 0.5, 0.5)
        t += cd
        ci += 1
    d = int(0.75 * beat * SR)  # dotted-eighth ping-pong echo on the arpeggio
    out += arp
    out[d:, 0] += 0.3 * arp[:-d, 1]
    out[d:, 1] += 0.3 * arp[:-d, 0]
    out[2 * d:] += 0.12 * arp[:-2 * d]
    return out


def build_audio(segs: List[Segment], pcms: Dict[Tuple[int, int], np.ndarray], total: float,
                tmp: Path, ffmpeg: str) -> Path:
    n_frames = int(round(total * FPS))
    n = n_frames * (SR // FPS)
    voice = np.zeros(n, np.float32)
    for i, seg in enumerate(segs):
        for j, c in enumerate(seg.chunks):
            s0 = int(round((seg.start + c.offset) * SR))
            pcm = pcms[(i, j)][: n - s0]
            voice[s0: s0 + len(pcm)] += pcm
    speech = voice[np.abs(voice) > 0.01]
    voice *= 0.1 / (np.sqrt(np.mean(speech ** 2)) + 1e-9)    # speech RMS -20 dBFS before loudnorm

    rms = np.sqrt(np.mean(voice.reshape(n_frames, -1) ** 2, axis=1))
    ref = np.percentile(rms[rms > 0.01], 95) if np.any(rms > 0.01) else 1.0
    env = np.clip(rms / ref, 0, 1)
    smooth = np.empty_like(env)
    acc = 0.0
    for i, v in enumerate(env):  # fast attack, slow decay: the badge ring breathes with the voice
        acc = max(v, acc * 0.78)
        smooth[i] = acc
    for seg in segs:
        f0 = int(round(seg.start * FPS))
        seg.env = smooth[f0: f0 + int(round(seg.duration * FPS))].astype(np.float32)

    bank = sfx_bank()
    sfx = np.zeros(n, np.float32)
    for t, name, g in sfx_events(segs):
        s0 = int(t * SR)
        if 0 <= s0 < n:
            sig = bank[name][: n - s0]
            sfx[s0: s0 + len(sig)] += sig * g * SFX_GAIN[re.sub(r"\d", "", name)]

    music = make_music(n)
    music *= 0.1 * 10 ** (-17 / 20) / (np.sqrt(np.mean(music ** 2)) + 1e-9)  # -17 dB under the voice, unducked
    speaking = rms > 0.1 * 0.1
    card = np.zeros(n_frames, bool)
    for seg in segs:
        if seg.kind == "card":
            card[int(round(seg.start * FPS)): int(round((seg.start + seg.duration) * FPS))] = True
    gain, g = np.empty(n_frames, np.float32), 1.0
    for i in range(n_frames):
        target = 0.33 if speaking[i: i + 5].any() else 1.0   # look ahead 5 frames: duck before she speaks
        target *= 1.35 if card[i] else 1.0
        g += (target - g) * (0.3 if target < g else 0.045)
        gain[i] = g
    fade = np.clip(np.arange(n_frames) / (1.5 * FPS), 0, 1) * np.clip((n_frames - np.arange(n_frames)) / (4 * FPS), 0, 1)
    g_s = np.interp(np.arange(n), np.arange(n_frames) * (SR // FPS) + SR // FPS // 2, gain * fade).astype(np.float32)
    mono = voice + sfx
    mix = np.stack([mono + music[:, 0] * g_s, mono + music[:, 1] * g_s], axis=1)
    mix *= 0.98 / max(1e-9, float(np.max(np.abs(mix))))

    wav = tmp / "mix.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    master = tmp / "master.m4a"
    subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(wav), "-af", "loudnorm=I=-15:TP=-1.5:LRA=11",
                    "-ar", str(SR), "-c:a", "aac", "-b:a", "192k", str(master)], check=True)
    return master


# --------------------------------------------------------------------------------------
# Drawing helpers & assets
# --------------------------------------------------------------------------------------
def clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease_out(x: float) -> float:
    return 1 - (1 - clamp01(x)) ** 3


def ease_in_out(x: float) -> float:
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_back(x: float) -> float:
    if x <= 0:
        return 0.0
    x = clamp01(x) - 1
    return 1 + 2.70158 * x ** 3 + 1.70158 * x ** 2


def mix(c1, c2, t: float):
    t = clamp01(t)
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def rrect(draw, box, r, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def wrap(draw, text, font, max_w) -> List[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if draw.textlength(cand, font=font) <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def centered(draw, y, text, font, fill):
    w = draw.textlength(text, font=font)
    draw.text(((WIDTH - w) / 2, y), text, font=font, fill=fill)


class Fonts:
    def __init__(self):
        self.huge = load_font(SANS_BOLD, 400)
        self.card_title = load_font(SANS_BOLD, 92)
        self.title_xl = load_font(SANS_BOLD, 88)
        self.title = load_font(SANS_BOLD, 56)
        self.sans_lg = load_font(SANS_REG, 34)
        self.sans_lg_b = load_font(SANS_BOLD, 32)
        self.sans_md_b = load_font(SANS_BOLD, 26)
        self.sans_md = load_font(SANS_REG, 23)
        self.sans_sm = load_font(SANS_REG, 22)
        self.sans_sm_b = load_font(SANS_BOLD, 20)
        self.sans_xs_b = load_font(SANS_BOLD, 15)
        self.small = load_font(SANS_REG, 16)
        self.cap = load_font(SANS_MED, 33)
        self.mono = load_font(MONO_REG, 18)
        self.mono_b = load_font(MONO_BOLD, 18)
        self.mono_xs = load_font(MONO_BOLD, 15)
        self.mono_md = load_font(MONO_BOLD, 22)


@lru_cache(maxsize=None)
def emoji(e: str, size: int) -> Image.Image:
    """Colour emoji sprite (Noto Color Emoji renders only at 109px, so draw then scale)."""
    img = Image.new("RGBA", (160, 140), (0, 0, 0, 0))
    try:
        ImageDraw.Draw(img).text((10, 6), e, font=ImageFont.truetype(EMOJI_FONT, 109), embedded_color=True)
    except OSError:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img = img.crop(img.getbbox() or (0, 0, 1, 1))
    k = size / max(img.size)
    return img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.LANCZOS)


class Assets:
    def __init__(self):
        self.fonts = Fonts()
        bg = Image.new("RGB", (WIDTH, HEIGHT), BG)
        d = ImageDraw.Draw(bg)
        for gx in range(32, WIDTH, 48):
            for gy in range(96, 936, 48):
                d.point((gx, gy), fill=(24, 34, 54))
                d.point((gx + 1, gy), fill=(24, 34, 54))
        glow = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))  # soft colour wash: cyan top-left, violet bottom-right
        ImageDraw.Draw(glow).ellipse((-300, -500, 1100, 500), fill=(6, 22, 44))
        ImageDraw.Draw(glow).ellipse((1100, 500, 2400, 1500), fill=(22, 10, 40))
        self.bg = ImageChops.add(bg, glow.filter(ImageFilter.GaussianBlur(220)))
        self.flat = Image.new("RGB", (WIDTH, HEIGHT), BG)
        self.shade_y = 925
        h = HEIGHT - self.shade_y
        self.shade_rgb = Image.new("RGB", (WIDTH, h), (3, 7, 18))
        self.shade_mask = Image.new("L", (WIDTH, h))
        ImageDraw.Draw(self.shade_mask).rectangle((0, 0, WIDTH, h), fill=232)
        for y in range(70):
            ImageDraw.Draw(self.shade_mask).line((0, y, WIDTH, y), fill=int(232 * (y / 70) ** 1.4))
        av = Image.new("RGBA", (76, 76), (0, 0, 0, 0))
        ImageDraw.Draw(av).ellipse((0, 0, 75, 75), fill=(49, 46, 129, 255), outline=(129, 140, 248, 255), width=2)
        e = emoji("👩‍💻", 46)
        av.paste(e, ((76 - e.width) // 2, (76 - e.height) // 2 + 2), e)
        self.avatar = av
        logo = Image.new("RGBA", (112, 112), (0, 0, 0, 0))
        ImageDraw.Draw(logo).rounded_rectangle((0, 0, 111, 111), 26, fill=CYAN + (255,))
        jf = load_font(SANS_BOLD, 80)
        ImageDraw.Draw(logo).text((56 - ImageDraw.Draw(logo).textlength("J", font=jf) / 2, 6), "J", font=jf, fill=BG)
        self.logo = logo


@lru_cache(maxsize=1)
def assets() -> Assets:
    return Assets()


@lru_cache(maxsize=None)
def sticker_sprite(e: str, text: str, color: Tuple[int, int, int]) -> Image.Image:
    F = assets().fonts
    tw = int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(text, font=F.sans_md_b))
    w, h, m = 20 + 44 + 14 + tw + 28, 68, 16
    img = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((m, m + 6, m + w, m + h + 6), 34, fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(7)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((m, m, m + w, m + h), 34, fill=mix(PANEL, color, 0.12) + (255,), outline=color + (255,), width=3)
    sp = emoji(e, 42)
    img.paste(sp, (m + 20, m + (h - sp.height) // 2), sp)
    d.text((m + 20 + 44 + 14, m + 19), text, font=F.sans_md_b, fill=TEXT)
    return img


def paste_scaled(img: Image.Image, sprite: Image.Image, cx: float, cy: float, s: float):
    if s <= 0.02:
        return
    sp = sprite if abs(s - 1) < 1e-3 else sprite.resize((max(1, int(sprite.width * s)), max(1, int(sprite.height * s))),
                                                         Image.BILINEAR)
    img.paste(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)), sp)


def draw_header(draw, fonts: Fonts, active: int, accent):
    draw.rectangle([(0, 0), (WIDTH, 76)], fill=(15, 23, 42))
    draw.line([(0, 76), (WIDTH, 76)], fill=PANEL_BORDER, width=2)
    rrect(draw, (48, 18, 86, 56), 10, accent)
    draw.text((60, 23), "J", font=fonts.sans_md_b, fill=BG)
    draw.text((100, 24), "Jasmin Web Panel", font=fonts.sans_md_b, fill=TEXT)
    draw.text((318, 28), "Installation Guide", font=fonts.sans_sm, fill=MUTED)
    widths = [int(draw.textlength(c.nav, font=fonts.sans_xs_b)) + 26 for c in CHAPTERS]
    x = WIDTH - 48 - (sum(widths) + 10 * (len(widths) - 1))
    for i, (ch, w) in enumerate(zip(CHAPTERS, widths)):
        is_active, done = i == active, i < active
        fill = ch.accent if is_active else ((24, 34, 54) if done else (15, 23, 42))
        outline = ch.accent if (is_active or done) else PANEL_BORDER
        fg = BG if is_active else (TEXT if done else DIM)
        rrect(draw, (x, 22, x + w, 54), 16, fill, outline, 1)
        draw.text((x + 13, 29), ch.nav, font=fonts.sans_xs_b, fill=fg)
        x += w + 10


# --------------------------------------------------------------------------------------
# Step scenes
# --------------------------------------------------------------------------------------
def step_base(seg: Segment) -> Image.Image:
    A = assets()
    F, ch, st = A.fonts, seg.chapter_obj, seg.step_obj
    img = A.bg.copy()
    d = ImageDraw.Draw(img)
    draw_header(d, F, seg.chapter, ch.accent)
    lx = 56
    bw = int(d.textlength(ch.badge, font=F.mono_xs)) + 28
    rrect(d, (lx, 118, lx + bw, 152), 17, (19, 32, 54), ch.accent, 1)
    d.text((lx + 14, 127), ch.badge, font=F.mono_xs, fill=ch.accent)
    y = 168
    for line in ch.title.split("\n"):
        d.text((lx, y), line, font=F.title, fill=TEXT)
        y += 66
    y += 8
    for line in wrap(d, ch.subtitle, F.sans_md, 620)[:2]:
        d.text((lx, y), line, font=F.sans_md, fill=MUTED)
        y += 32
    sy = 404
    rrect(d, (lx, sy, 688, sy + 78), 16, (19, 32, 54), ch.accent, 2)
    d.text((lx + 22, sy + 12), f"CHAPTER {seg.chapter + 1}  •  STEP {seg.step + 1} OF {len(ch.steps)}",
           font=F.mono_xs, fill=ch.accent)
    d.text((lx + 22, sy + 36), st.title, font=F.sans_md_b, fill=TEXT)
    dx = 688 - 22 - len(ch.steps) * 18
    for i in range(len(ch.steps)):
        d.ellipse((dx + i * 18, sy + 16, dx + i * 18 + 10, sy + 26), fill=ch.accent if i <= seg.step else PANEL_BORDER)
    rrect(d, (lx, 502, 688, 918), 18, PANEL, PANEL_BORDER, 2)
    d.text((lx + 26, 524), "KEY HIGHLIGHTS", font=F.mono_xs, fill=ch.accent)
    rrect(d, (TX1 - 3, TY1 - 3, TX2 + 3, TY2 + 3), 20, mix(BG, ch.accent, 0.18))   # faint accent rim
    rrect(d, (TX1, TY1, TX2, TY2), 18, TERM_BG, PANEL_BORDER, 2)
    rrect(d, (TX1, TY1, TX2, TY1 + 48), 18, TERM_TOP)
    d.rectangle([(TX1, TY1 + 26), (TX2, TY1 + 48)], fill=TERM_TOP)
    d.line([(TX1, TY1 + 48), (TX2, TY1 + 48)], fill=PANEL_BORDER, width=1)
    for i, col in enumerate([(239, 68, 68), (245, 158, 11), (34, 197, 94)]):
        d.ellipse((TX1 + 20 + i * 24, TY1 + 17, TX1 + 34 + i * 24, TY1 + 31), fill=col)
    d.text((TX1 + 104, TY1 + 15), st.terminal_title, font=F.mono_xs, fill=MUTED)
    return img


def draw_diagram(draw, x, y, fonts: Fonts, progress: float, lt: float):
    nodes = [
        ("Browser / API", CYAN, (x + 24, y + 36, x + 230, y + 106)),
        ("Jasmin Panel", EMERALD, (x + 295, y + 36, x + 520, y + 106)),
        ("Jasmin Gateway", VIOLET, (x + 585, y + 36, x + 820, y + 106)),
        ("SMSC Carriers", AMBER, (x + 885, y + 36, x + 1075, y + 106)),
        ("PostgreSQL", CYAN, (x + 295, y + 160, x + 520, y + 224)),
        ("RabbitMQ + sms_logger", ROSE, (x + 585, y + 160, x + 890, y + 224)),
    ]
    links = [((230, 71), (295, 71), CYAN), ((520, 71), (585, 71), CYAN), ((820, 71), (885, 71), CYAN),
             ((700, 106), (700, 160), ROSE), ((585, 192), (520, 192), ROSE), ((408, 160), (408, 106), EMERALD)]
    live = progress > 0.2
    for (x1, y1), (x2, y2), col in links:
        c = col if live else (71, 85, 105)
        draw.line([(x + x1, y + y1), (x + x2, y + y2)], fill=c, width=3)
        ux, uy = (x2 - x1) / max(1, abs(x2 - x1) + abs(y2 - y1)), (y2 - y1) / max(1, abs(x2 - x1) + abs(y2 - y1))
        draw.polygon([(x + x2, y + y2), (x + x2 - 11 * ux - 6 * uy, y + y2 - 11 * uy + 6 * ux),
                      (x + x2 - 11 * ux + 6 * uy, y + y2 - 11 * uy - 6 * ux)], fill=c)
    for label, lx, ly in (("jcli :8990", 516, 14), ("SMPP", 834, 14), ("AMQP", 712, 124), ("Submit Logs", 286, 124)):
        draw.text((x + lx, y + ly), label, font=fonts.mono_xs, fill=MUTED)
    for label, color, box in nodes:
        rrect(draw, box, 12, (15, 23, 42), color, 2)
        tw = draw.textlength(label, font=fonts.sans_sm_b)
        draw.text(((box[0] + box[2]) / 2 - tw / 2, (box[1] + box[3]) / 2 - 11), label, font=fonts.sans_sm_b, fill=TEXT)
    if live:  # data packets travelling along every link
        for idx, ((x1, y1), (x2, y2), col) in enumerate(links):
            f = (lt * 0.9 + idx * 0.17) % 1.0
            px, py = x + x1 + (x2 - x1) * f, y + y1 + (y2 - y1) * f
            draw.ellipse((px - 9, py - 9, px + 9, py + 9), fill=mix(TERM_BG, col, 0.35))
            draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=mix(col, TEXT, 0.4))


def draw_terminal(d, seg: Segment, lt: float, F: Fonts):
    st = seg.step_obj
    rows = term_rows(seg)
    # amber highlight around each run of warning lines, pulsing when it appears
    i = 0
    while i < len(rows):
        if rows[i][0] != "warn":
            i += 1
            continue
        j = i
        while j + 1 < len(rows) and rows[j + 1][0] == "warn":
            j += 1
        if lt >= rows[i][2]:
            last = max(k for k in range(i, j + 1) if rows[k][2] <= lt)
            age = lt - rows[i][2]
            inten = 0.45 + 0.55 * math.exp(-age * 1.1) * abs(math.cos(age * 4.5))
            rrect(d, (TX1 + 12, rows[i][4] - 7, TX2 - 12, rows[last][4] + 29), 10,
                  mix(TERM_BG, AMBER, 0.08), mix(TERM_BG, AMBER, inten), 2)
        i = j + 1
    colors = {"comment": DIM, "ok": EMERALD, "warn": AMBER, "out": MUTED}
    for kind, text, a, b, y in rows:
        if lt < a:
            break
        if kind == "blank":
            continue
        if kind == "cmd":
            typing = lt < b
            shown = text if not typing else text[: max(1, int(len(text) * (lt - a) / max(1e-6, b - a)))]
            if typing:
                rrect(d, (TX1 + 10, y - 6, TX2 - 10, y + 28), 8, (12, 20, 40))
            if not text.startswith("  "):  # indented = continuation of the previous command, no prompt
                d.text((TX1 + 26, y), "$", font=F.mono_b, fill=EMERALD)
            d.text((TX1 + 50, y), shown, font=F.mono, fill=TEXT)
            if typing:
                cx = TX1 + 50 + d.textlength(shown, font=F.mono) + 2
                d.rectangle((cx, y + 1, cx + 10, y + 22), fill=CYAN)
        else:
            k = ease_out((lt - a) / 0.2)
            font = F.mono_b if kind in ("ok", "warn") else F.mono
            d.text((TX1 + 26, y + int((1 - k) * 8)), text, font=font, fill=mix(TERM_BG, colors[kind], k))
    if not st.diagram and lt > rows[-1][3] + 0.3:  # idle prompt with a blinking cursor
        y = rows[-1][4] + 34
        if y < TY2 - 36:
            d.text((TX1 + 26, y), "$", font=F.mono_b, fill=EMERALD)
            if int(lt * 2) % 2 == 0:
                d.rectangle((TX1 + 50, y + 1, TX1 + 60, y + 22), fill=TEXT)
    if st.diagram:
        p = clamp01((lt - rows[0][2]) / max(0.1, rows[-1][3] - rows[0][2]))
        d.line([(TX1 + 24, TY2 - 266), (TX2 - 24, TY2 - 266)], fill=PANEL_BORDER, width=1)
        draw_diagram(d, TX1 + 16, TY2 - 252, F, p, lt)


def step_scene(seg: Segment, lt: float, base: Image.Image) -> Image.Image:
    F, ch = assets().fonts, seg.chapter_obj
    img = base.copy()
    d = ImageDraw.Draw(img)
    by = 566
    for i, bullet in enumerate(ch.bullets):
        lines = wrap(d, bullet, F.sans_sm, 560)
        k = 1.0 if seg.step else ease_out((lt - BULLET_T0 - i * BULLET_DT) / 0.45)
        if k > 0:
            dx = int((1 - k) * -36)
            d.ellipse((82 + dx, by + 9, 94 + dx, by + 21), fill=mix(PANEL, ch.accent, k))
            for n, wl in enumerate(lines):
                d.text((108 + dx, by + 30 * n), wl, font=F.sans_sm, fill=mix(PANEL, TEXT, k))
        by += 30 * len(lines) + 22
    draw_terminal(d, seg, lt, F)
    return img


# --------------------------------------------------------------------------------------
# Intro, chapter cards, outro
# --------------------------------------------------------------------------------------
def intro_scene(seg: Segment, lt: float) -> Image.Image:
    A = assets()
    F = A.fonts
    img = A.bg.copy()
    d = ImageDraw.Draw(img)
    kr = clamp01((lt - 0.7) / 1.0)
    if 0 < kr < 1:  # shockwave ring when the logo lands
        r = 60 + 260 * ease_out(kr)
        d.ellipse((960 - r, 186 - r, 960 + r, 186 + r), outline=mix(BG, CYAN, 1 - kr), width=4)
    paste_scaled(img, A.logo, 960, 186, ease_back((lt - 0.15) / 0.6))
    k = ease_out((lt - 0.7) / 0.7)
    centered(d, 268 + (1 - k) * 30, "Jasmin Web Panel", F.title_xl, mix(BG, TEXT, k))
    k = ease_out((lt - 1.1) / 0.7)
    centered(d, 378 + (1 - k) * 20, "Complete Installation & Deployment Guide", F.sans_lg, mix(BG, CYAN, k))
    k = ease_out((lt - 1.5) / 0.7)
    centered(d, 428, "curl installer  •  Docker Compose  •  systemd + Nginx  •  Kubernetes  •  .deb / .rpm",
             F.sans_md, mix(BG, MUTED, k))
    col_w, gap = 540, 24
    x0 = (WIDTH - (3 * col_w + 2 * gap)) // 2
    for i, ch in enumerate(CHAPTERS):
        k = ease_out((lt - INTRO_CARD_T0 - i * INTRO_CARD_DT) / 0.5)
        if k <= 0:
            continue
        r, c = divmod(i, 3)
        x, y = x0 + c * (col_w + gap), 510 + r * 104 + int((1 - k) * 40)
        rrect(d, (x, y, x + col_w, y + 84), 16, mix(BG, PANEL, k), mix(BG, ch.accent, k), 2)
        sp = emoji(ch.emoji, 34)
        if k > 0.6:
            img.paste(sp, (x + col_w - 58, y + 24), sp)
        d.text((x + 22, y + 18), f"{i + 1:02d}", font=F.mono_md, fill=mix(BG, ch.accent, k))
        d.text((x + 80, y + 14), ch.nav, font=F.sans_md_b, fill=mix(BG, TEXT, k))
        d.text((x + 80, y + 48), ch.blurb, font=F.sans_sm, fill=mix(BG, MUTED, k))
    centered(d, 846, "Free & Open Source  •  MIT License  •  github.com/101t/jasmin-web-panel", F.mono_xs,
             mix(BG, DIM, ease_out((lt - 2.0) / 0.8)))
    return img


def card_scene(seg: Segment, lt: float) -> Image.Image:
    A = assets()
    F, ch = A.fonts, seg.chapter_obj
    acc = ch.accent
    img = A.bg.copy()
    d = ImageDraw.Draw(img)
    k1, k2, k3, k4 = (ease_out((lt - t0) / 0.6) for t0 in (0.05, 0.2, 0.32, 0.5))
    d.text((1190, 150), f"{seg.chapter + 1:02d}", font=F.huge, fill=mix(BG, acc, 0.13 * k2))
    x0 = 160
    d.rectangle((x0, 300, x0 + 8, 300 + int(330 * k1)), fill=acc)
    d.text((x0 + 40 - (1 - k2) * 40, 312), f"CHAPTER {seg.chapter + 1:02d} OF {len(CHAPTERS)}", font=F.mono_md,
           fill=mix(BG, acc, k2))
    d.text((x0 + 40, 350 + (1 - k3) * 40), ch.title.replace("\n", " "), font=F.card_title, fill=mix(BG, TEXT, k3))
    d.text((x0 + 40, 470 + (1 - k4) * 30), ch.blurb, font=F.sans_lg, fill=mix(BG, MUTED, k4))
    bw = int(d.textlength(ch.badge, font=F.mono_xs)) + 28
    rrect(d, (x0 + 40, 540, x0 + 40 + bw, 574), 17, mix(BG, (19, 32, 54), k4), mix(BG, acc, k4), 1)
    d.text((x0 + 54, 549), ch.badge, font=F.mono_xs, fill=mix(BG, acc, k4))
    paste_scaled(img, emoji(ch.emoji, 230), 1480, 400 + math.sin(lt * 2.2) * 10, ease_back((lt - 0.4) / 0.7))
    # what's inside this chapter
    x, y = x0 + 40, 650
    d.text((x, y), "IN THIS CHAPTER", font=F.mono_xs, fill=mix(BG, DIM, k4))
    y += 34
    for i, st in enumerate(ch.steps):
        k = ease_out((lt - 0.9 - i * 0.15) / 0.4)
        label = f"{i + 1}. {st.title}"
        w = int(d.textlength(label, font=F.sans_sm)) + 36
        if x + w > WIDTH - 160:
            x, y = x0 + 40, y + 58
        if k > 0:
            rrect(d, (x, y + (1 - k) * 16, x + w, y + 44 + (1 - k) * 16), 22, mix(BG, PANEL, k), mix(BG, acc, 0.6 * k), 2)
            d.text((x + 18, y + 10 + (1 - k) * 16), label, font=F.sans_sm, fill=mix(BG, TEXT, k))
        x += w + 14
    # chapter progress dots
    for i in range(len(CHAPTERS)):
        cx = WIDTH // 2 - (len(CHAPTERS) - 1) * 14 + i * 28
        col = acc if i == seg.chapter else (MUTED if i < seg.chapter else PANEL_BORDER)
        r = 7 if i == seg.chapter else 5
        d.ellipse((cx - r, 880 - r, cx + r, 880 + r), fill=col)
    return img


def confetti(d, t: float, ox: float, oy: float):
    if not 0 <= t <= 3.2:
        return
    rng = np.random.default_rng(42)
    cols = [CYAN, EMERALD, AMBER, VIOLET, ROSE, GOLD]
    for _ in range(150):
        a = math.radians(rng.uniform(-165, -15))
        v = rng.uniform(500, 1400)
        x = ox + math.cos(a) * v * t
        y = oy + math.sin(a) * v * t + 0.5 * 1500 * t * t
        w, h = rng.uniform(6, 10), rng.uniform(10, 18)
        th = rng.uniform(0, 6.28) + rng.uniform(-8, 8) * t
        col = mix(BG, cols[int(rng.integers(len(cols)))], 1 - clamp01((t - 2.4) / 0.8))
        c, s = math.cos(th), math.sin(th)
        d.polygon([(x + c * px - s * py, y + s * px + c * py) for px, py in
                   ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))], fill=col)


def outro_scene(seg: Segment, lt: float) -> Image.Image:
    A = assets()
    F = A.fonts
    img = A.bg.copy()
    d = ImageDraw.Draw(img)
    k = ease_out(lt / 0.6)
    centered(d, 112 + (1 - k) * 30, "Thanks for watching!", F.title_xl, mix(BG, TEXT, k))
    centered(d, 222, "You're ready to run Jasmin SMS Gateway like a pro.", F.sans_lg, mix(BG, MUTED, ease_out((lt - 0.3) / 0.6)))
    cards = [("🐙", "GitHub", "github.com/101t/jasmin-web-panel", CYAN),
             ("📚", "Documentation", "about.supernovasoft.com/jasmin-web-panel", EMERALD),
             ("💬", "Community (Telegram)", "t.me/jasminwebpanel", VIOLET)]
    cw, gap = 540, 24
    x0 = (WIDTH - (3 * cw + 2 * gap)) // 2
    for i, (e, title, url, col) in enumerate(cards):
        k = ease_out((lt - 0.8 - i * 0.35) / 0.5)
        if k <= 0:
            continue
        x, y = x0 + i * (cw + gap), 300 + int((1 - k) * 30)
        rrect(d, (x, y, x + cw, y + 130), 18, mix(BG, PANEL, k), mix(BG, col, k), 2)
        if k > 0.6:
            sp = emoji(e, 34)
            img.paste(sp, (x + 26, y + 26), sp)
        d.text((x + 72, y + 28), title, font=F.sans_md_b, fill=mix(BG, TEXT, k))
        d.text((x + 28, y + 82), url, font=F.mono, fill=mix(BG, col, k))
    # "Star on GitHub" button, clicked exactly when Ava says "star"
    tc = outro_click_time(seg)
    s = ease_back((lt - 1.6) / 0.5) * (0.94 if tc <= lt < tc + 0.14 else 1.0)
    starred = lt >= tc
    if s > 0:
        bw, bh, cx, cy = 470 * s, 84 * s, 960, 520
        rrect(d, (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), int(42 * s),
              mix(BG, GOLD, 0.92) if starred else PANEL, GOLD, 3)
        if s > 0.85:
            label = "Starred — thank you!" if starred else "Star on GitHub"
            tw = d.textlength(label, font=F.sans_lg_b)
            sp = emoji("⭐", 40)
            x = cx - (tw + 54) / 2
            img.paste(sp, (int(x), int(cy - 21)), sp)
            d.text((x + 54, cy - 19), label, font=F.sans_lg_b, fill=BG if starred else TEXT)
    k = ease_out((lt - 2.4) / 0.6)
    if k > 0:
        bx1, bx2, y = WIDTH // 2 - 560, WIDTH // 2 + 560, 620 + int((1 - k) * 30)
        rrect(d, (bx1, y, bx2, y + 140), 20, mix(BG, (19, 26, 46), k), mix(BG, AMBER, k), 2)
        d.text((bx1 + 36, y + 24), "ENTERPRISE EDITION", font=F.mono_xs, fill=mix(BG, AMBER, k))
        d.text((bx1 + 36, y + 54), "SMPP Forge — the full-featured enterprise SMS platform", font=F.sans_md_b,
               fill=mix(BG, TEXT, k))
        d.text((bx1 + 36, y + 94), "smppforge.com   •   info@smppforge.com", font=F.mono, fill=mix(BG, AMBER, k))
    centered(d, 820, "Free & Open Source  •  MIT License", F.mono_xs, DIM)
    confetti(d, lt - tc, 960, 520)
    # mouse cursor glides to the button and clicks
    if tc - 1.3 <= lt <= tc + 1.2:
        k = ease_in_out((lt - (tc - 1.3)) / 1.15)
        px, py = 1560 + (1000 - 1560) * k, 900 + (538 - 900) * k
        pts = [(0, 0), (0, 30), (8, 23), (14, 36), (20, 33), (14, 21), (24, 21)]
        d.polygon([(px + x, py + y) for x, y in pts], fill=TEXT, outline=BG)
        if tc <= lt < tc + 0.35:
            r = 10 + 40 * (lt - tc) / 0.35
            d.ellipse((px - r, py - r, px + r, py + r), outline=mix(BG, GOLD, 1 - (lt - tc) / 0.35), width=3)
    return img


# --------------------------------------------------------------------------------------
# Camera, overlay, frame composition
# --------------------------------------------------------------------------------------
def camera(seg: Segment, lt: float) -> Tuple[float, float, float]:
    """Punch in on the terminal while typing (following the active line), pull back to read."""
    if seg.kind != "step" or seg.step_obj.diagram:
        drift = {"intro": 0.03, "card": 0.045, "outro": 0.0}.get(seg.kind, 0.0)
        return 1 + drift * ease_in_out(lt / seg.duration), 960, 540
    rows = [r for r in term_rows(seg) if r[0] != "blank"]
    t_in, t_end = rows[0][2] + 0.4, rows[-1][3]
    k = ease_in_out((lt - t_in) / 1.0) * (1 - ease_in_out((lt - t_end - 0.6) / 1.1))

    def line_y(t):
        y = rows[0][4]
        for r in rows:
            if r[2] <= t:
                y = r[4]
        return y

    fy = sum(line_y(lt - j * 0.07) for j in range(12)) / 12 + 14   # box-filtered focus = smooth tracking
    return 1 + 0.2 * k, 960 + ((TX1 + TX2) / 2 - 960) * k, 540 + (fy - 540) * k


def apply_camera(img: Image.Image, s: float, cx: float, cy: float) -> Image.Image:
    if s < 1.001:
        return img
    w, h = WIDTH / s, HEIGHT / s
    x0 = min(max(cx - w / 2, 0), WIDTH - w)
    y0 = min(max(cy - h / 2, 0), HEIGHT - h)
    return img.resize((WIDTH, HEIGHT), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))


def fade_amount(seg: Segment, lt: float) -> float:
    fin = {"intro": 0.8, "card": 0.3, "outro": 0.4}.get(seg.kind, 0.3 if seg.step == 0 else 0.0)
    fout = {"intro": 0.35, "card": 0.25, "outro": 1.2}.get(seg.kind, 0.4 if seg.last_in_chapter else 0.0)
    a = 1.0
    if fin and lt < fin:
        a = lt / fin
    if fout and lt > seg.duration - fout:
        a = min(a, (seg.duration - lt) / fout)
    return clamp01(a)


def draw_captions(img: Image.Image, d, seg: Segment, lt: float, F: Fonts):
    cur = None
    for p in seg.phrases:
        if seg.words[p[0]][0] - 0.1 <= lt:
            cur = p
    if cur is None or lt > seg.words[cur[1] - 1][1] + 1.0:
        return
    ws = seg.words[cur[0]: cur[1]]
    space = d.textlength(" ", font=F.cap)
    widths = [d.textlength(w, font=F.cap) for _, _, w in ws]
    total = sum(widths) + space * (len(ws) - 1)
    x, y = (WIDTH - total) / 2, 992
    box = (int(x - 28), y - 14, int(x + total + 28), y + 52)
    mask = Image.new("L", (box[2] - box[0], box[3] - box[1]))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, mask.width - 1, mask.height - 1), 20, fill=200)
    img.paste((2, 6, 23), box, mask)
    for (a, b, w), wd in zip(ws, widths):
        if a <= lt < b + 0.06:  # the word Ava is saying right now
            rrect(d, (x - 6, y - 4, x + wd + 6, y + 40), 8, mix((2, 6, 23), seg.accent, 0.45))
            d.text((x, y), w, font=F.cap, fill=TEXT)
        else:
            d.text((x, y), w, font=F.cap, fill=TEXT if lt >= b else (190, 200, 214))
        x += wd + space


def draw_overlay(img: Image.Image, seg: Segment, lt: float, gp: float, marks: List[float]):
    A = assets()
    F, acc = A.fonts, seg.accent
    img.paste(A.shade_rgb, (0, A.shade_y), A.shade_mask)
    d = ImageDraw.Draw(img)
    draw_captions(img, d, seg, lt, F)
    # narrator badge with a voice-reactive ring and equaliser
    e = float(seg.env[min(int(lt * FPS), len(seg.env) - 1)]) if seg.env is not None and len(seg.env) else 0.0
    cx, cy = 92, 1010
    r = 41 + e * 9
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=mix(BG, acc, 0.3 + 0.7 * e), width=3)
    img.paste(A.avatar, (cx - 38, cy - 38), A.avatar)
    d.text((146, 986), NARRATOR, font=F.sans_md_b, fill=TEXT)
    d.text((146, 1018), "your guide", font=F.small, fill=MUTED)
    for k in range(4):
        h = 4 + e * 24 * (0.55 + 0.45 * math.sin(lt * 11 + k * 1.7))
        bx = 206 + k * 9
        d.rounded_rectangle((bx, 998 - h / 2, bx + 5, 998 + h / 2), 2, fill=acc)
    # chapter label + progress bar with chapter ticks
    label = ("INTRO" if seg.kind == "intro" else "WRAP-UP" if seg.kind == "outro"
             else f"CHAPTER {seg.chapter + 1} / {len(CHAPTERS)}  ·  {seg.chapter_obj.nav.upper()}")
    d.text((WIDTH - 48 - d.textlength(label, font=F.mono_xs), 1012), label, font=F.mono_xs, fill=MUTED)
    d.rectangle([(0, HEIGHT - 8), (WIDTH, HEIGHT)], fill=(30, 41, 59))
    d.rectangle([(0, HEIGHT - 8), (int(WIDTH * gp), HEIGHT)], fill=acc)
    for m in marks[1:]:
        d.rectangle([(int(WIDTH * m) - 1, HEIGHT - 8), (int(WIDTH * m) + 1, HEIGHT)], fill=BG)
    # reaction stickers, top-right
    shown: List[float] = []
    for t, em, text, col in stickers(seg):
        slot = sum(1 for p in shown if p + STICKER_LIFE > t)
        shown.append(t)
        if t <= lt < t + STICKER_LIFE:
            s = ease_back((lt - t) / 0.4) * (1 - ease_in_out((lt - t - STICKER_LIFE + 0.3) / 0.3))
            sp = sticker_sprite(em, text, col)
            paste_scaled(img, sp, WIDTH - 40 - sp.width / 2, 140 + slot * 92, s)


def render_frame(seg: Segment, lt: float, total: float, marks: List[float], base=None) -> Image.Image:
    gp = min(1.0, (seg.start + lt) / total)
    if seg.kind == "step":
        scene = step_scene(seg, lt, base if base is not None else step_base(seg))
    else:
        scene = {"intro": intro_scene, "card": card_scene, "outro": outro_scene}[seg.kind](seg, lt)
    scene = apply_camera(scene, *camera(seg, lt))
    if seg.kind != "step":  # drawn after the slow push-in so the header never gets cropped
        draw_header(ImageDraw.Draw(scene), assets().fonts, {"intro": -1, "outro": len(CHAPTERS)}.get(seg.kind, seg.chapter),
                    seg.accent)
    a = fade_amount(seg, lt)
    if seg.kind == "outro":  # the end fades everything, overlay included
        draw_overlay(scene, seg, lt, gp, marks)
        return scene if a > 0.99 else Image.blend(assets().flat, scene, a)
    if a < 0.99:  # chapter transitions dip the scene to dark; badge, captions and progress stay put
        scene = Image.blend(assets().flat, scene, a)
    draw_overlay(scene, seg, lt, gp, marks)
    return scene


def preview_time(seg: Segment) -> float:
    return seg.duration * (0.8 if seg.kind == "card" else 0.88)


def render_segment_job(args) -> str:
    i, seg, total, marks, ffmpeg, out, preview = args
    n = int(round(seg.duration * FPS))
    base = step_base(seg) if seg.kind == "step" else None
    cmd = [ffmpeg, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-threads", "2", "-an", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    pf = int(preview_time(seg) * FPS)
    for f in range(n):
        frame = render_frame(seg, f / FPS, total, marks, base)
        if f == pf:
            frame.save(preview)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", "replace")
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed on segment {i}: {err}")
    return seg_label(seg)


def seg_label(seg: Segment) -> str:
    return seg.kind if seg.kind in ("intro", "outro") else (
        f"{seg.chapter_obj.nav} / title card" if seg.kind == "card" else f"{seg.chapter_obj.nav} / {seg.step_obj.title}")


# --------------------------------------------------------------------------------------
# Thumbnail, captions, description, docs
# --------------------------------------------------------------------------------------
def make_thumbnail(path: Path):
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), BG)
    glow = Image.new("RGB", (w, h), BG)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((640, 60, 1300, 680), fill=(14, 60, 110))
    gd.ellipse((-200, 380, 500, 900), fill=(40, 22, 80))
    img = glow.filter(ImageFilter.GaussianBlur(120))
    d = ImageDraw.Draw(img)
    for gx in range(20, w, 40):
        for gy in range(20, h, 40):
            d.point((gx, gy), fill=(28, 40, 62))
    d.rectangle([(0, 0), (14, h)], fill=CYAN)
    f_badge = load_font(MONO_BOLD, 22)
    f_big = load_font(SANS_BOLD, 96)
    f_mid = load_font(SANS_BOLD, 58)
    f_small = load_font(SANS_BOLD, 26)
    f_mono = load_font(MONO_BOLD, 20)
    rrect(d, (60, 56, 420, 100), 22, (19, 32, 54), EMERALD, 2)
    d.text((82, 66), "FREE & OPEN SOURCE", font=f_badge, fill=EMERALD)
    d.text((60, 126), "INSTALL", font=f_big, fill=CYAN)
    d.text((60, 236), "Jasmin SMS", font=f_mid, fill=TEXT)
    d.text((60, 304), "Web Panel", font=f_mid, fill=TEXT)
    tags = [("curl", EMERALD), ("Docker", CYAN), ("systemd", EMERALD), ("Kubernetes", VIOLET), (".deb/.rpm", AMBER)]
    x, y = 60, 410
    for label, col in tags:
        tw = int(d.textlength(label, font=f_small)) + 32
        if x + tw > 640:
            x, y = 60, y + 62
        rrect(d, (x, y, x + tw, y + 48), 24, (19, 32, 54), col, 2)
        d.text((x + 16, y + 9), label, font=f_small, fill=col)
        x += tw + 14
    d.text((60, 640), "Step-by-step  •  Production-ready  •  Full guide", font=f_small, fill=MUTED)
    tx1, ty1, tx2, ty2 = 680, 120, 1230, 600
    rrect(d, (tx1 - 4, ty1 - 4, tx2 + 4, ty2 + 4), 22, (20, 70, 110))
    rrect(d, (tx1, ty1, tx2, ty2), 18, TERM_BG, PANEL_BORDER, 3)
    rrect(d, (tx1, ty1, tx2, ty1 + 44), 18, TERM_TOP)
    d.rectangle([(tx1, ty1 + 24), (tx2, ty1 + 44)], fill=TERM_TOP)
    for i, col in enumerate([(239, 68, 68), (245, 158, 11), (34, 197, 94)]):
        d.ellipse((tx1 + 18 + i * 22, ty1 + 15, tx1 + 32 + i * 22, ty1 + 29), fill=col)
    rows = [("$ curl -fsSL .../install.sh \\", TEXT), ("    | sudo bash", TEXT), ("", TEXT),
            ("[INFO] Detected OS: Ubuntu 24.04", MUTED), ("[INFO] Installing Docker stack...", MUTED),
            ("[ OK ] Secrets generated", EMERALD), ("[ OK ] jcli locked to 127.0.0.1", EMERALD),
            ("[ OK ] Panel is healthy!", EMERALD), ("", TEXT), ("  https://sms.example.com", CYAN)]
    yy = ty1 + 70
    for text, col in rows:
        d.text((tx1 + 24, yy), text, font=f_mono, fill=col)
        yy += 36
    rocket = emoji("🚀", 150)
    img.paste(rocket, (tx2 - 110, ty1 - 90), rocket)
    img.save(path, optimize=True)


def ts(t: float, srt: bool = False) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    if srt:
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"
    return f"{int(h)}:{int(m):02d}:{int(s):02d}" if h else f"{int(m):02d}:{int(s):02d}"


def write_srt(segs: List[Segment], path: Path):
    cues = []
    for seg in segs:
        for k, (i0, i1) in enumerate(seg.phrases):
            a = seg.start + seg.words[i0][0]
            b = seg.start + seg.words[i1 - 1][1] + 0.4
            if k + 1 < len(seg.phrases):
                b = min(b, seg.start + seg.words[seg.phrases[k + 1][0]][0])
            cues.append((a, max(b, a + 0.3), " ".join(w for _, _, w in seg.words[i0:i1])))
    path.write_text("\n".join(f"{n}\n{ts(a, True)} --> {ts(b, True)}\n{text}\n"
                              for n, (a, b, text) in enumerate(cues, 1)), encoding="utf-8")


def chapter_marks(segs: List[Segment]) -> List[Tuple[float, str]]:
    marks = [(0.0, "Introduction")]
    for seg in segs:
        if seg.kind == "card":
            marks.append((seg.start, f"{seg.chapter_obj.nav} — {seg.chapter_obj.blurb}"))
        if seg.kind == "outro":
            marks.append((seg.start, "Wrap-up & resources"))
    return marks


def write_description(segs: List[Segment], total: float, path: Path):
    lines = [
        "# YouTube upload kit",
        "",
        "## Title",
        "Install Jasmin SMS Gateway Web Panel: curl, Docker, systemd, Kubernetes & .deb/.rpm (Complete Guide)",
        "",
        "## Description",
        "Learn how to install, configure and secure Jasmin Web Panel, the free and open-source web UI and REST API "
        "for Jasmin SMS Gateway. This step-by-step guide covers the one-line installer, Docker Compose, native "
        "systemd + Nginx with Let's Encrypt, Kubernetes (Kustomize), Debian/RPM packages, your first users, "
        "SMPP connectors, routes and test SMS, the Submit Log, and a production security checklist.",
        "",
        f"GitHub: {REPO}",
        f"Documentation: {DOCS}",
        f"Telegram community: {TELEGRAM}",
        "Enterprise edition: SMPP Forge — https://smppforge.com (info@smppforge.com)",
        "",
        "Chapters:",
    ]
    lines += [f"{ts(t)} {name}" for t, name in chapter_marks(segs)]
    lines += [
        "",
        "## Tags",
        "jasmin sms gateway, jasmin web panel, smpp, sms gateway, open source sms, django, docker compose, "
        "kubernetes, systemd, nginx, lets encrypt, sms api, smsc, telecom, self-hosted",
        "",
        "## Upload checklist",
        "- Video: `media/jasmin-web-panel-install-guide.mp4`",
        "- Thumbnail: `media/youtube/thumbnail.png`",
        "- Subtitles: `media/youtube/captions.en.srt` (Subtitles > Upload file > With timing)",
        "- Category: Science & Technology; Language: English; License: Standard YouTube License",
        "- Narration is a synthetic (AI) voice; music and sound effects are generated by the script (no third-party "
        "licenses).",
        "- After publishing, put the video ID in `docs/video-tutorial.md` (see the comment at the top).",
        "",
        f"Total duration: {ts(total)}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def update_docs(segs: List[Segment], total: float, root: Path):
    page = root / "docs" / "video-tutorial.md"
    if not page.exists():
        return
    table = ["| Time | Chapter |", "|------|---------|"] + [f"| `{ts(t)}` | {name} |" for t, name in chapter_marks(segs)]
    table += ["", f"Total length: **{ts(total)}**"]
    text = page.read_text(encoding="utf-8")
    start, end = "<!-- chapters:start -->", "<!-- chapters:end -->"
    if start in text and end in text:
        before, after = text.split(start)[0], text.split(end)[1]
        page.write_text(before + start + "\n" + "\n".join(table) + "\n" + end + after, encoding="utf-8")


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------
def self_test():
    w = "Version 3.12 on sms.example.com, ok!".split()
    t = align_words(w, [(0.0, 1.0, "Version 3.12"), (1.0, 1.2, "on"), (1.2, 2.0, "sms.example.com"), (2.0, 2.5, "ok")], 3)
    assert t == [(0.0, 0.5), (0.5, 1.0), (1.0, 1.2), (1.2, 2.0), (2.0, 2.5)], t
    assert align_words(["a", "—", "b"], [(0.0, 1.0, "a"), (2.0, 3.0, "b")], 3)[1] == (1.0, 2.0)
    assert align_words(["a", "b"], [], 2.0) == [(0.0, 1.0), (1.0, 2.0)]
    assert mood_runs("[excited] Hi! [excited] Yo. [calm] Yes.") == [("excited", "Hi! Yo."), ("calm", "Yes.")]
    assert mood_runs("Plain. [happy] Wow!") == [("calm", "Plain."), ("happy", "Wow!")]
    words = [(i, i + 1, w) for i, w in enumerate("Hello there. This is a test, of phrases!".split())]
    assert build_phrases(words) == [(0, 2), (2, 8)], build_phrases(words)
    for ch in CHAPTERS:  # every tag in the script must be a known mood
        for text in [ch.hook] + [s.narration for s in ch.steps]:
            assert not re.search(r"\[[a-z]+\]", MOOD_TAG.sub("", text)), text
    print("self-test ok")


def estimate_timing(segs: List[Segment]):
    """--frames-only: fake TTS durations and evenly spaced word timings (~2.6 words/s)."""
    for seg in segs:
        for c in seg.chunks:
            toks = c.text.split()
            c.dur = len(toks) / 2.6 + 0.3
            c.events = [(0.1 + k / 2.6, 0.1 + (k + 0.9) / 2.6, w) for k, w in enumerate(toks)]
    total = layout(segs)
    for seg in segs:
        n = int(round(seg.duration * FPS))
        lt = np.arange(n) / FPS
        talking = np.zeros(n, bool)
        for a, b, _ in seg.words:
            talking[int(a * FPS): int(b * FPS) + 1] = True
        seg.env = (talking * (0.6 + 0.4 * np.sin(lt * 17))).astype(np.float32)
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--frames-only", action="store_true",
                        help="render preview stills with estimated timings (no TTS, no video)")
    parser.add_argument("--voice", default=VOICE, help=f"edge-tts voice (default: {VOICE})")
    parser.add_argument("--jobs", type=int, default=max(1, min(8, (multiprocessing.cpu_count() or 2) // 2)),
                        help="parallel segment renderers")
    parser.add_argument("--self-test", action="store_true", help="run the built-in checks and exit")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    root = Path(__file__).resolve().parent.parent
    media, yt, previews = root / "media", root / "media" / "youtube", root / "media" / "previews"
    for p in (media, yt, previews, root / "docs" / "assets" / "images"):
        p.mkdir(parents=True, exist_ok=True)
    for old in previews.glob("*.png"):  # numbering changes when segments change
        old.unlink()
    output = media / "jasmin-web-panel-install-guide.mp4"

    segs = build_segments()
    make_thumbnail(yt / "thumbnail.png")
    shutil.copy(yt / "thumbnail.png", root / "docs" / "assets" / "images" / "video-thumbnail.png")

    if args.frames_only:
        total = estimate_timing(segs)
        marks = [t / total for t, _ in chapter_marks(segs)]
        for i, seg in enumerate(segs):
            render_frame(seg, preview_time(seg), total, marks).save(previews / f"{i:02d}_{seg.kind}.png")
            if seg.kind == "step":  # mid-typing, camera punched in
                rows = term_rows(seg)
                mid = (rows[0][2] + rows[-1][3]) / 2
                render_frame(seg, mid, total, marks).save(previews / f"{i:02d}_{seg.kind}_typing.png")
        print(f"Preview frames written to {previews} (estimated length {ts(total)})")
        return 0

    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    with tempfile.TemporaryDirectory(prefix="jwp_video_") as tmpdir:
        tmp = Path(tmpdir)
        n_chunks = sum(len(s.chunks) for s in segs)
        print(f"1/6 Synthesizing {n_chunks} emotional voice phrases with {args.voice} ...")
        paths = asyncio.run(synthesize(segs, tmp, args.voice))
        pcms = {}
        for i, seg in enumerate(segs):
            for j, c in enumerate(seg.chunks):
                pcms[(i, j)] = decode(ffmpeg, paths[i][j])
                c.dur = len(pcms[(i, j)]) / SR
        total = layout(segs)
        print(f"    Total length: {ts(total)}")

        print("2/6 Mixing voice, generated music (ducked) and sound effects ...")
        master = build_audio(segs, pcms, total, tmp, ffmpeg)
        del pcms

        print(f"3/6 Rendering {len(segs)} segments on {args.jobs} workers ...")
        marks = [t / total for t, _ in chapter_marks(segs)]
        jobs = [(i, seg, total, marks, ffmpeg, tmp / f"seg_{i:03d}.mp4", previews / f"{i:02d}_{seg.kind}.png")
                for i, seg in enumerate(segs)]
        jobs.sort(key=lambda j: -j[1].duration)  # longest first balances the pool
        with ProcessPoolExecutor(max_workers=args.jobs, mp_context=multiprocessing.get_context("fork")) as pool:
            futures = [pool.submit(render_segment_job, j) for j in jobs]
            for done, fut in enumerate(as_completed(futures), 1):
                print(f"    [{done:02d}/{len(segs)}] {fut.result()}")

        print("4/6 Joining segments and muxing audio ...")
        lst = tmp / "list.txt"
        lst.write_text("\n".join(f"file '{(tmp / f'seg_{i:03d}.mp4').as_posix()}'" for i in range(len(segs))))
        subprocess.run([ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(master),
                        "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", "-shortest",
                        str(output)], check=True)

    print("5/6 Writing captions, YouTube description and docs chapter table ...")
    write_srt(segs, yt / "captions.en.srt")
    write_description(segs, total, yt / "description.md")
    update_docs(segs, total, root)

    size = output.stat().st_size / 1024 / 1024
    print(f"6/6 Done: {output} ({size:.1f} MB, {ts(total)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
