import subprocess
import os
import pty
import select
import time
from pathlib import Path


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")


def test_local_npx_menu_uses_arrow_prompt_in_tty() -> None:
    result = subprocess.run(
        ["script", "-q", "/dev/null", "node", str(ROOT / "installer" / "bin" / "railforge.mjs")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = result.stdout
    assert "↑↓ navigate" in output
    assert "选择操作编号或字母" not in output
    assert "? ? RailForge 主菜单" not in output
    assert "Multi-Model Collaboration" in output
    assert "查看全部斜杠命令" in output
    assert output.count("初始化 RailForge 配置") == 1


def test_main_menu_arrow_navigation_does_not_repaint_banner() -> None:
    master, slave = pty.openpty()
    proc = subprocess.Popen(
        ["node", str(ROOT / "installer" / "bin" / "railforge.mjs")],
        cwd=ROOT / "installer",
        stdin=slave,
        stdout=slave,
        stderr=slave,
        close_fds=True,
    )
    os.close(slave)

    output = b""
    start = time.time()
    sent = False

    try:
        while time.time() - start < 5:
            readable, _, _ = select.select([master], [], [], 0.2)
            if master in readable:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                output += chunk
                if b"navigate" in output and not sent:
                    os.write(master, b"\x1b[B\x1b[B\x1b[B")
                    time.sleep(0.1)
                    os.write(master, b"\x04")
                    sent = True
            if proc.poll() is not None:
                break
    finally:
        try:
            proc.wait(timeout=5)
        finally:
            os.close(master)

    text = output.decode("utf-8", errors="replace")
    assert text.count("╔════════════════════════════════════════════════════════════╗") == 1
    assert text.count("? RailForge 主菜单") >= 1


def test_help_enter_returns_to_main_menu() -> None:
    master, slave = pty.openpty()
    proc = subprocess.Popen(
        ["node", str(ROOT / "installer" / "bin" / "railforge.mjs")],
        cwd=ROOT / "installer",
        stdin=slave,
        stdout=slave,
        stderr=slave,
        close_fds=True,
    )
    os.close(slave)

    output = b""
    start = time.time()
    stage = "menu"

    try:
        while time.time() - start < 8:
            readable, _, _ = select.select([master], [], [], 0.2)
            if master in readable:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                output += chunk
                text = output.decode("utf-8", errors="replace")
                if stage == "menu" and "↑↓ navigate" in text:
                    os.write(master, b"\x1b[B\x1b[B\x1b[B\x1b[B\x1b[B\x1b[B\n")
                    stage = "help"
                    continue
                if stage == "help" and "按 Enter 返回主菜单" in text:
                    os.write(master, b"\n")
                    stage = "returning"
                    continue
                if stage == "returning" and text.count("? RailForge 主菜单") >= 2:
                    os.write(master, b"\x04")
                    stage = "done"
            if proc.poll() is not None:
                break
    finally:
        try:
            proc.wait(timeout=5)
        finally:
            os.close(master)

    text = output.decode("utf-8", errors="replace")
    assert "按 Enter 返回主菜单" in text
    assert text.count("? RailForge 主菜单") >= 2
