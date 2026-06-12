"""Tests for scripts/data_loader.py and its docker-compose service configuration."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parents[2]
LOADER_SCRIPT = REPO_ROOT / "scripts" / "data_loader.py"


# ---------------------------------------------------------------------------
# Fail-fast: missing SUPABASE_DATABASE_URL
# ---------------------------------------------------------------------------


def test_loader_exits_with_error_when_db_url_missing() -> None:
    env = {k: v for k, v in os.environ.items() if k != "SUPABASE_DATABASE_URL"}
    result = subprocess.run(
        [sys.executable, str(LOADER_SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode != 0, "loader must exit non-zero when DB URL is missing"
    output = result.stdout + result.stderr
    assert (
        "SUPABASE_DATABASE_URL" in output
    ), "error output must mention SUPABASE_DATABASE_URL so the developer knows what to fix"


def test_loader_error_message_has_no_traceback_when_db_url_missing() -> None:
    env = {k: v for k, v in os.environ.items() if k != "SUPABASE_DATABASE_URL"}
    result = subprocess.run(
        [sys.executable, str(LOADER_SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert (
        "Traceback (most recent call last)" not in result.stderr
    ), "missing-env error must print a plain message, not a Python traceback"


# ---------------------------------------------------------------------------
# docker-compose: data-loader service shape
# ---------------------------------------------------------------------------


def test_docker_compose_has_data_loader_service() -> None:
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    assert "data-loader" in compose.get(
        "services", {}
    ), "docker-compose.yml must define a 'data-loader' service"


def test_data_loader_service_uses_backend_image() -> None:
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    svc = compose["services"]["data-loader"]
    assert "build" in svc or "image" in svc, "data-loader must have a build or image"
    # reuses the backend build context — no separate Dockerfile
    if "build" in svc:
        build = svc["build"]
        context = build if isinstance(build, str) else build.get("context", "")
        assert context == ".", "data-loader must build from the repo root context"


def test_data_loader_service_mounts_data_volume() -> None:
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    volumes = compose["services"]["data-loader"].get("volumes", [])
    assert any(
        "data" in str(v) for v in volumes
    ), "data-loader must mount the ./data directory"


def test_data_loader_service_mounts_supabase_volume() -> None:
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    volumes = compose["services"]["data-loader"].get("volumes", [])
    assert any(
        "supabase" in str(v) for v in volumes
    ), "data-loader must mount the ./supabase directory for SQL schema files"


def test_data_loader_service_has_no_restart_policy() -> None:
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    svc = compose["services"]["data-loader"]
    assert (
        svc.get("restart") != "unless-stopped"
    ), "data-loader is a one-shot service and must not have restart: unless-stopped"


def test_data_loader_service_has_env_file() -> None:
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    svc = compose["services"]["data-loader"]
    env_file = svc.get("env_file", [])
    env_file_list = [env_file] if isinstance(env_file, str) else env_file
    assert any(
        ".env" in str(e) for e in env_file_list
    ), "data-loader must declare env_file: .env to inject SUPABASE_DATABASE_URL"
