from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
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


def build_binary(entry_script: Path, output_name: str) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--name",
            output_name,
            str(entry_script),
        ],
        cwd=ROOT,
        check=True,
    )


def binary_output_name(base_name: str, suffix: str) -> str:
    ext = ".exe" if platform.system().lower() == "windows" else ""
    return f"{base_name}-{suffix}{ext}"


def sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)

    suffix = target_suffix()
    build_binary(ROOT / "railforge" / "__main__.py", f"railforge-{suffix}")
    build_binary(ROOT / "railforge" / "codeagent" / "__main__.py", f"railforge-codeagent-{suffix}")

    asset_names = [
        binary_output_name("railforge", suffix),
        binary_output_name("railforge-codeagent", suffix),
    ]
    manifest = {
        "version": VERSION,
        "target": suffix,
        "assets": [],
    }
    for asset_name in asset_names:
        asset_path = DIST / asset_name
        manifest["assets"].append(
            {
                "name": asset_name,
                "sha256": sha256_file(asset_path),
                "size": asset_path.stat().st_size,
            }
        )

    (DIST / "manifest.txt").write_text(
        "\n".join(
            [
                f"version={VERSION}",
                f"target={suffix}",
                f"files={','.join(asset_names)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (DIST / f"manifest-{suffix}.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
