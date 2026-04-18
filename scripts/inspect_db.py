import sqlite3
import os

paths = [
    os.path.join("backend", "dev.db"),
    os.path.join("backend", "dev.sqlite"),
    "dev.db",
    "dev.sqlite",
]

for path in paths:
    if os.path.exists(path):
        try:
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(users)")
            cols = [r[1] for r in cur.fetchall()]
            print(path, cols)
            conn.close()
        except Exception as e:
            print("ERROR inspecting", path, e)
    else:
        print("MISSING", path)
