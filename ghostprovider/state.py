"""Persistent deployment state — maps container IDs to clone paths."""

import json
import os
from pathlib import Path

STATE_DIR = Path.home() / ".config" / "ghostprovider"
STATE_FILE = STATE_DIR / "state.json"


def _ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load() -> dict[str, dict[str, str]]:
    _ensure_state_dir()
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save(state: dict[str, dict[str, str]]) -> None:
    _ensure_state_dir()
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except OSError:
        pass


def register(container_id: str, clone_path: str, repo_url: str) -> None:
    state = load()
    state[container_id] = {"clone_path": clone_path, "repo_url": repo_url}
    save(state)


def unregister(container_id: str) -> None:
    state = load()
    state.pop(container_id, None)
    save(state)


def get_clone_path(container_id: str) -> str | None:
    state = load()
    entry = state.get(container_id)
    if entry and os.path.isdir(entry.get("clone_path", "")):
        return entry["clone_path"]
    return None


def migrate_old_containers(containers: list) -> None:
    """Scan running/stopped ghost containers and register any missing entries."""
    state = load()
    changed = False
    for c in containers:
        clone_path = (c.labels or {}).get("ghostprovider.clone_path", "")
        repo_url = (c.labels or {}).get("ghostprovider.repo", "")
        if c.id not in state and (clone_path or repo_url):
            state[c.id] = {"clone_path": clone_path, "repo_url": repo_url}
            changed = True
    if changed:
        save(state)
