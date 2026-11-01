#!/usr/bin/env python3
"""End-to-end GTK single-instance activation test using two OS processes.

Run under one dbus-run-session and Xvfb display. The first process owns a live
GtkApplication window; the second launches the same binary with no arguments.
We assert that D-Bus forwarded activation to the primary, which reuses exactly
one GTK window. The compositor, not GTK, decides whether focus is granted.
"""
import os
import selectors
import subprocess
import sys
import time

TIMEOUT = 15.0


def wait_for_line(proc, expected, timeout):
    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ)
    chunks = bytearray()
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            if proc.poll() is not None and not selector.select(0):
                break
            ready = selector.select(0.2)
            if not ready:
                continue
            part = os.read(proc.stdout.fileno(), 4096)
            if not part:
                break
            chunks.extend(part)
            if expected in chunks:
                return bytes(chunks)
            if len(chunks) > 16384:
                break
        raise RuntimeError("GTK primary did not report expected activation milestone")
    finally:
        selector.close()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_gtk_ipc.py <gtk-binary>")
    binary = os.path.abspath(sys.argv[1])
    primary = subprocess.Popen(
        [binary, "--ipc-primary-smoke"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        bufsize=0,
    )
    try:
        before = wait_for_line(primary, b"PRIMARY_WINDOW_READY", TIMEOUT)
        if primary.poll() is not None:
            raise RuntimeError("GTK primary exited before secondary launch")
        secondary = subprocess.run(
            [binary], capture_output=True, timeout=TIMEOUT, check=False,
        )
        if secondary.returncode != 0:
            raise RuntimeError("Secondary GTK process did not exit cleanly")
        # The primary's actual activate callback prints the marker and quits.
        after = wait_for_line(primary, b"REMOTE_ACTIVATION_RECEIVED", TIMEOUT)
        stdout, stderr = primary.communicate(timeout=TIMEOUT)
        total = before + after + stdout
        if primary.returncode != 0 or b"PASS: cross-process D-Bus activation reused one window" not in total:
            raise RuntimeError("Primary did not prove single-window remote activation")
        print("PASS: second GTK process activated existing primary via D-Bus; one window retained")
        print("NOTE: Wayland compositor focus is not guaranteed by this test")
    finally:
        if primary.poll() is None:
            primary.kill()
            primary.communicate(timeout=TIMEOUT)


if __name__ == "__main__":
    main()
