#!/usr/bin/env python3
"""Launch the REAL ncurses interface in a pseudo-terminal, then quit cleanly.

Uses only the Python standard library; does not read user files or secrets.
"""
import errno
import fcntl
import os
import pty
import select
import signal
import struct
import sys
import termios
import time

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_tui_pty.py <tui-binary>")
    executable = os.path.abspath(sys.argv[1])
    pid, master = pty.fork()
    if pid == 0:
        # The child owns its pseudo-terminal and terminal size before exec.
        fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 100, 0, 0))
        os.environ["TERM"] = "xterm-256color"
        os.execv(executable, [executable])
    waited = False
    screen = bytearray()
    sent_quit = False
    deadline = time.monotonic() + 12.0
    try:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(master, 8192)
                except OSError as exc:
                    if exc.errno != errno.EIO:
                        raise
                    chunk = b""
                screen.extend(chunk)
                if len(screen) > 65536:
                    del screen[:-65536]
                if b"TOMBSTONE" in screen and not sent_quit:
                    os.write(master, b"q")
                    sent_quit = True
            ended, status = os.waitpid(pid, os.WNOHANG)
            if ended == pid:
                waited = True
                if not sent_quit or os.waitstatus_to_exitcode(status) != 0:
                    raise RuntimeError("TUI did not draw and exit cleanly")
                print("PASS: actual ncurses TUI drew in a PTY, received q and exited 0")
                return
        raise RuntimeError("TUI PTY smoke timed out")
    finally:
        os.close(master)
        if not waited:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)

if __name__ == "__main__":
    main()
