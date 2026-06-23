"""Smart dependency installer for ghostprovider."""

import shutil
import subprocess


def required_tools(has_compose: bool, has_dockerfile: bool,
                   has_package_json: bool, has_requirements: bool,
                   has_go_mod: bool, has_cargo: bool,
                   has_index: bool = False) -> list[str]:
    """Return list of required tool names based on repo analysis."""
    tools = ["git"]
    if has_compose or has_dockerfile or has_index:
        tools.append("docker")
    if has_requirements:
        tools.append("python3")
    if has_package_json:
        tools.append("node")
    return tools


def tool_display_name(tool: str) -> str:
    names = {
        "git": "Git",
        "docker": "Docker",
        "python3": "Python 3",
        "node": "Node.js",
    }
    return names.get(tool, tool)


def tool_description(tool: str) -> str:
    desc = {
        "git": "Git — version control system (cloning repositories)",
        "docker": "Docker — containerization (running isolated services)",
        "python3": "Python 3 — interpreter for Python projects",
        "node": "Node.js — runtime for JavaScript/TypeScript projects",
    }
    return desc.get(tool, tool)


def is_installed(tool: str) -> bool:
    if tool == "docker":
        return shutil.which("docker") is not None
    return shutil.which(tool) is not None


def missing_tools(tools: list[str]) -> list[str]:
    return [t for t in tools if not is_installed(t)]


def detect_pm() -> str | None:
    """Detect available system package manager."""
    for cmd in ("apt-get", "pacman", "dnf", "yum", "brew", "apk", "zypper"):
        if shutil.which(cmd):
            return cmd
    return None


def _pm_install_cmd(pm: str, tool: str) -> list[str]:
    pkgs = {
        "apt-get": {
            "git": "git",
            "docker": "docker.io",
            "python3": "python3",
            "node": "nodejs",
        },
        "pacman": {
            "git": "git",
            "docker": "docker",
            "python3": "python",
            "node": "nodejs",
        },
        "dnf": {
            "git": "git",
            "docker": "docker",
            "python3": "python3",
            "node": "nodejs",
        },
        "yum": {
            "git": "git",
            "docker": "docker",
            "python3": "python3",
            "node": "nodejs",
        },
        "brew": {
            "git": "git",
            "docker": "docker",
            "python3": "python3",
            "node": "node",
        },
        "apk": {
            "git": "git",
            "docker": "docker",
            "python3": "python3",
            "node": "nodejs",
        },
        "zypper": {
            "git": "git",
            "docker": "docker",
            "python3": "python3",
            "node": "nodejs",
        },
    }
    pkg = pkgs.get(pm, {}).get(tool)
    if not pkg:
        return []
    base = {
        "apt-get": ["apt-get", "install", "-y"],
        "pacman": ["pacman", "-S", "--noconfirm"],
        "dnf": ["dnf", "install", "-y"],
        "yum": ["yum", "install", "-y"],
        "brew": ["brew", "install"],
        "apk": ["apk", "add"],
        "zypper": ["zypper", "install", "-y"],
    }
    return base.get(pm, []) + [pkg]


def install_tools(tools: list[str], password: str | None = None) -> list[str]:
    """Install missing tools. Returns list of failed tools.

    If *password* is provided, uses ``sudo -S`` to pass it non-interactively.
    Otherwise the usual ``sudo`` is tried without stdin (will likely fail
    when there is no TTY).

    For security the password is zeroed from memory after use.
    """
    pm = detect_pm()
    if not pm:
        return tools

    # Convert to mutable bytearray so we can zero it after use
    pw_bytes: bytearray | None = None
    if password is not None:
        pw_bytes = bytearray(password, "utf-8")

    sudo_path = shutil.which("sudo")
    failed: list[str] = []
    for tool in tools:
        if is_installed(tool):
            continue
        cmd = _pm_install_cmd(pm, tool)
        if not cmd:
            failed.append(tool)
            continue

        try:
            if pw_bytes is not None and sudo_path:
                full_cmd = ["sudo", "-S"] + cmd
                proc = subprocess.Popen(
                    full_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                proc.communicate(input=pw_bytes + b"\n", timeout=120)
                if proc.returncode != 0:
                    failed.append(tool)
            elif sudo_path and pm not in ("brew",):
                full_cmd = [sudo_path] + cmd
                subprocess.run(
                    full_cmd,
                    capture_output=True, text=True,
                    timeout=120,
                )
            else:
                subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if not is_installed(tool):
                failed.append(tool)
        except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
            failed.append(tool)

    # Zero out password bytes
    if pw_bytes is not None:
        for i in range(len(pw_bytes)):
            pw_bytes[i] = 0

    return failed
