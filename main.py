
#MyActivityTracker


import ctypes
import psutil
import time
import sqlite3
from datetime import datetime
from ctypes import wintypes


# WINDOWS API


user32 = ctypes.WinDLL("user32", use_last_error=True)

user32.GetForegroundWindow.restype = wintypes.HWND

user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD)
]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD


def get_active_application():
    hwnd = user32.GetForegroundWindow()

    if not hwnd:
        return None

    pid = wintypes.DWORD()

    user32.GetWindowThreadProcessId(
        hwnd,
        ctypes.byref(pid)
    )

    try:
        return psutil.Process(pid.value).name()

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess
    ):
        return None



# DATABASE


db = sqlite3.connect("activity_tracker.db")

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    date TEXT NOT NULL
)
""")

db.commit()


def save_session(app, start, end, duration):
    cursor.execute("""
    INSERT INTO sessions
    (application, start_time, end_time, duration_seconds, date)
    VALUES (?, ?, ?, ?, ?)
    """, (
        app,
        start.strftime("%H:%M:%S"),
        end.strftime("%H:%M:%S"),
        int(duration),
        start.strftime("%Y-%m-%d")
    ))

    db.commit()

    print(f"\n[DATABASE] {app} session saved.")



# TIME FORMAT


def format_duration(seconds):
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"



# TRACKING SYSTEM


current_app = None
session_start = None
session_start_clock = None

print("================================")
print("       ACTIVITY TRACKER V1")
print("================================")
print("Tracking started.")
print("Database connected.\n")

try:
    while True:

        app = get_active_application()
        now = time.monotonic()
        clock_now = datetime.now()

        # Application changed
        if app != current_app:

            # Save previous session
            if current_app is not None:
                duration = now - session_start

                print(
                    f"\n{current_app} ENDED | "
                    f"Total: {format_duration(duration)}"
                )

                save_session(
                    current_app,
                    session_start_clock,
                    clock_now,
                    duration
                )

            # Start new session
            current_app = app
            session_start = now
            session_start_clock = clock_now

            if current_app is not None:
                print(
                    f"\n{current_app} STARTED | "
                    f"Time: {clock_now.strftime('%H:%M:%S')}"
                )

        # Live timer
        if current_app is not None:
            duration = now - session_start

            print(
                f"\r{current_app} | "
                f"Timer: {format_duration(duration)}",
                end="",
                flush=True
            )

        time.sleep(1)

except KeyboardInterrupt:

    if current_app is not None:
        end_time = datetime.now()
        duration = time.monotonic() - session_start

        print(
            f"\n\n{current_app} ENDED | "
            f"Total: {format_duration(duration)}"
        )

        save_session(
            current_app,
            session_start_clock,
            end_time,
            duration
        )

    print("\nActivity Tracker stopped.")

finally:
    db.close()


