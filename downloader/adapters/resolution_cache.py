import json
import os
import sqlite3
import time


class ResolutionCache:
    """
    Small sqlite-backed cache for scraped page results, so cancelled or
    repeated downloads do not re-scrape pages already processed. Entries
    expire after ttl_seconds in case the page is edited on the site.
    Any storage failure silently disables the cache: resolution then
    falls back to scraping, never breaking the download.
    """

    COLUMNS = ["cache_key", "payload", "resolved_at"]

    def __init__(self, table, db_path="resources/config/downloads.db", ttl_seconds=7 * 24 * 3600):
        self.table = table
        self.db_path = db_path
        self.ttl_seconds = ttl_seconds
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            try:
                cols = [row[1] for row in conn.execute(f"PRAGMA table_info({self.table})")]
                if cols and cols != self.COLUMNS:
                    conn.execute(f"DROP TABLE {self.table}")

                conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {self.table} ("
                    "cache_key TEXT PRIMARY KEY, payload TEXT, resolved_at REAL)"
                )
                conn.execute(
                    f"DELETE FROM {self.table} WHERE resolved_at < ?",
                    (time.time() - self.ttl_seconds,),
                )
                conn.commit()
            finally:
                conn.close()
            self.available = True
        except Exception:
            self.available = False

    def load(self, key):
        if not self.available:
            return None
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                row = conn.execute(
                    f"SELECT payload, resolved_at FROM {self.table} WHERE cache_key = ?",
                    (key,),
                ).fetchone()
            finally:
                conn.close()

            if row is None:
                return None

            payload, resolved_at = row
            if time.time() - resolved_at > self.ttl_seconds:
                return None

            return json.loads(payload)
        except Exception:
            return None

    def store(self, key, payload):
        if not self.available:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    f"INSERT OR REPLACE INTO {self.table} (cache_key, payload, resolved_at) VALUES (?, ?, ?)",
                    (key, json.dumps(payload), time.time()),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass
