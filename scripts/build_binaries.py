from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"
VERSION = (ROOT / "railforge" / "__init__.py").read_text(encoding="utf-8").split('"')[1]


def target_suffix() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = "arm64" if machine in {"arm64", "aarch64"} else "amd64"
    if system == "darwin":
        os_name = "darwin"
    elif system == "windows":
        os_name = "windows"
    else:
        os_name = "linux"
    return f"{os_name}-{arch}"


def build_binary(entry_module: str, output_name: str) -> None:
    subprocess.run(
        [
            "pyinstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--name",
            output_name,
            "-m",
            entry_module,
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> None:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)

    suffix = target_suffix()
    build_binary("railforge", f"railforge-{suffix}")
    build_binary("railforge.codeagent", f"railforge-codeagent-{suffix}")

    (DIST / "manifest.txt").write_text(
        "\n".join(
            [
                f"version={VERSION}",
                f"target={suffix}",
                f"files=railforge-{suffix},railforge-codeagent-{suffix}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
