from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parents[2]


def _parse_env_keys(path: Path) -> set[str]:
    keys = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            keys.add(line.split("=", 1)[0].strip())
    return keys


# ---------------------------------------------------------------------------
# .env.example completeness
# ---------------------------------------------------------------------------


def test_env_example_exists() -> None:
    assert (REPO_ROOT / ".env.example").exists(), ".env.example not found at repo root"


def test_env_example_matches_env_keys() -> None:
    env_keys = _parse_env_keys(REPO_ROOT / ".env")
    example_keys = _parse_env_keys(REPO_ROOT / ".env.example")
    missing = env_keys - example_keys
    assert not missing, f".env.example is missing keys present in .env: {missing}"


# ---------------------------------------------------------------------------
# Dockerfile — no secrets copied in
# ---------------------------------------------------------------------------


def test_backend_dockerfile_exists() -> None:
    assert (REPO_ROOT / "Dockerfile").exists(), "Dockerfile not found at repo root"


def test_backend_dockerfile_does_not_copy_env_file() -> None:
    content = (REPO_ROOT / "Dockerfile").read_text()
    # COPY .env or ADD .env — both are forbidden
    forbidden = re.compile(r"^\s*(COPY|ADD)\s+\.env\b", re.MULTILINE)
    assert not forbidden.search(content), "Dockerfile must not copy .env into the image"


def test_backend_dockerfile_runs_as_non_root() -> None:
    content = (REPO_ROOT / "Dockerfile").read_text()
    user_directives = re.findall(r"^\s*USER\s+(\S+)", content, re.MULTILINE)
    assert user_directives, "Dockerfile must set a non-root USER"
    assert user_directives[-1] not in ("root", "0"), "Dockerfile must not run as root"


def test_frontend_dockerfile_exists() -> None:
    assert (
        REPO_ROOT / "frontend" / "Dockerfile"
    ).exists(), "frontend/Dockerfile not found"


def test_frontend_dockerfile_does_not_copy_env_file() -> None:
    content = (REPO_ROOT / "frontend" / "Dockerfile").read_text()
    forbidden = re.compile(r"^\s*(COPY|ADD)\s+\.env\b", re.MULTILINE)
    assert not forbidden.search(
        content
    ), "frontend/Dockerfile must not copy .env into the image"


# ---------------------------------------------------------------------------
# docker-compose.yml structure
# ---------------------------------------------------------------------------


def test_docker_compose_exists() -> None:
    assert (REPO_ROOT / "docker-compose.yml").exists(), "docker-compose.yml not found"


def test_docker_compose_has_backend_service() -> None:
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    assert "backend" in compose.get(
        "services", {}
    ), "docker-compose.yml must define a 'backend' service"


def test_docker_compose_backend_exposes_port_8000() -> None:
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    ports = compose["services"]["backend"].get("ports", [])
    assert any("8000" in str(p) for p in ports), "backend service must expose port 8000"


def test_docker_compose_has_frontend_service() -> None:
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    assert "frontend" in compose.get(
        "services", {}
    ), "docker-compose.yml must define a 'frontend' service"


def test_docker_compose_frontend_exposes_port_80() -> None:
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    ports = compose["services"]["frontend"].get("ports", [])
    assert any("80" in str(p) for p in ports), "frontend service must expose port 80"


def test_docker_compose_override_exists() -> None:
    assert (
        REPO_ROOT / "docker-compose.override.yml"
    ).exists(), "docker-compose.override.yml not found"


def test_docker_compose_override_backend_mounts_source() -> None:
    override = yaml.safe_load((REPO_ROOT / "docker-compose.override.yml").read_text())
    volumes = override.get("services", {}).get("backend", {}).get("volumes", [])
    assert volumes, "override backend service must mount source code as a volume"


def test_docker_compose_override_frontend_exposes_port_5173() -> None:
    override = yaml.safe_load((REPO_ROOT / "docker-compose.override.yml").read_text())
    ports = override.get("services", {}).get("frontend", {}).get("ports", [])
    assert any(
        "5173" in str(p) for p in ports
    ), "override frontend must expose dev port 5173"
