import sqlite3
import os

paths = [
    os.path.join("backend", "dev.db"),
    "dev.db",
]

for path in paths:
    if not os.path.exists(path):
        print("SKIP missing", path)
        continue
    print("Processing", path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cur.fetchall()]
    # Add stripe columns if missing
    if 'stripe_customer_id' not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255)")
            print("Added stripe_customer_id to", path)
        except Exception as e:
            print("Failed to add stripe_customer_id to", path, e)
    else:
        print("stripe_customer_id already present in", path)

    if 'stripe_subscription_id' not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN stripe_subscription_id VARCHAR(255)")
            print("Added stripe_subscription_id to", path)
        except Exception as e:
            print("Failed to add stripe_subscription_id to", path, e)
    else:
        print("stripe_subscription_id already present in", path)

    # Create indexes (SQLite supports IF NOT EXISTS on create_index in modern versions)
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS ix_users_stripe_customer_id ON users (stripe_customer_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_users_stripe_subscription_id ON users (stripe_subscription_id)")
        print("Ensured indexes on", path)
    except Exception as e:
        print("Failed to create indexes on", path, e)

    conn.commit()
    conn.close()
