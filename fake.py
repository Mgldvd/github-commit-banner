import os
import subprocess
import random
import secrets
import sys
import termios
import tty
from datetime import datetime, timedelta, timezone

RESET = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[33m"

def load_env(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

load_env()

GIT_USER_NAME = os.environ.get("GIT_USER_NAME")
GIT_USER_EMAIL = os.environ.get("GIT_USER_EMAIL")
START_YEAR = int(os.environ.get("START_YEAR", "0"))
END_YEAR = int(os.environ.get("END_YEAR", "0"))

def run(cmd, env=None):
    subprocess.run(cmd, env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def format_seconds(seconds):
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    if m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"

def read_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch in ("\r", "\n"):
            return "ENTER"
        return "OTHER"
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def label(name):
    return f"{YELLOW}{name:<14}:{RESET}"

def main():
    if not GIT_USER_NAME or not GIT_USER_EMAIL or START_YEAR <= 0 or END_YEAR <= 0 or END_YEAR < START_YEAR:
        print("Invalid or missing .env values")
        sys.exit(1)

    commits_by_weekday = {
        0: 7,
        1: 14,
        2: 21,
        3: 14,
        4: 7,
        5: 2,
        6: 2
    }

    start_date = datetime(START_YEAR, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(END_YEAR, 12, 31, tzinfo=timezone.utc)

    simulated_total = 0
    total_days = 0
    d = start_date
    while d <= end_date:
        simulated_total += commits_by_weekday[d.weekday()]
        total_days += 1
        d += timedelta(days=1)

    print()
    print(f"{BOLD}GitHub Commit Canvas{RESET}")
    print(f"{label('USER')} {GIT_USER_NAME} <{GIT_USER_EMAIL}>")
    print(f"{label('RANGE')} {start_date.date()} -> {end_date.date()} ({total_days} days)")
    print(f"{label('PATTERN')} Mon 7 | Tue 14 | Wed 21 | Thu 14 | Fri 7 | Sat 2 | Sun 2")
    print(f"{label('TOTAL COMMITS')} {simulated_total}")
    print()
    print("Press ENTER to start, any other key to exit")

    if read_key() != "ENTER":
        print("\nCancelled")
        return

    if not os.path.exists(".git"):
        run(["git", "init"])

    run(["git", "config", "user.name", GIT_USER_NAME])
    run(["git", "config", "user.email", GIT_USER_EMAIL])
    run(["git", "config", "core.fsync", "none"])

    with open("data.txt", "w", encoding="utf-8") as f:
        f.write("seed\n")

    run(["git", "add", "data.txt"])
    run(["git", "commit", "--no-verify", "-m", "Reset data file"])

    current_commit = 0
    current_day = start_date
    started = datetime.now(timezone.utc).timestamp()
    last_update = 0

    while current_day <= end_date:
        commits_today = commits_by_weekday[current_day.weekday()]

        for i in range(commits_today):
            dt = current_day + timedelta(seconds=random.randint(0, 86399))
            stamp = dt.strftime("%Y-%m-%dT%H:%M:%S%z")

            with open("data.txt", "a", encoding="utf-8") as f:
                f.write(f"{current_day.date()}-{i:02d} {secrets.token_hex(16)}\n")

            run(["git", "add", "data.txt"])

            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = stamp
            env["GIT_COMMITTER_DATE"] = stamp
            run(["git", "commit", "--no-verify", "-m", f"Commit {current_day.date()} #{i+1}"], env=env)

            current_commit += 1
            now = datetime.now(timezone.utc).timestamp()
            if now - last_update >= 0.2 or current_commit == simulated_total:
                last_update = now
                elapsed = now - started
                rate = current_commit / elapsed if elapsed > 0 else 0
                remaining = (simulated_total - current_commit) / rate if rate > 0 else 0

                width = 30
                filled = int((current_commit / simulated_total) * width)
                bar = "#" * filled + "-" * (width - filled)

                sys.stdout.write(
                    f"\r[{bar}] {current_commit}/{simulated_total} "
                    f"{format_seconds(elapsed)} elapsed "
                    f"{format_seconds(remaining)} left "
                    f"{rate:5.1f} c/s"
                )
                sys.stdout.flush()

        current_day += timedelta(days=1)

    run(["git", "add", ".gitignore", "README.md", "example.env", "fake.py"])
    run(["git", "commit", "--amend", "--no-verify", "-m", "Final commit"])

    print("\nDone")
    print(f"Total commits: {current_commit}")

if __name__ == "__main__":
    main()
