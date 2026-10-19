"""SQLite idempotency log. For cloud schedule use durable DB, not ephemeral runner disk."""
import sqlite3
from datetime import datetime, timezone

class DispatchLog:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.execute('''CREATE TABLE IF NOT EXISTS dispatch (
            item_key TEXT PRIMARY KEY, hotel TEXT, period TEXT, state TEXT,
            recipient TEXT, subject TEXT, body TEXT, ai_status TEXT,
            message_id TEXT, attempted_at TEXT, error TEXT)''')
        self.db.commit()
    def sent(self, key: str) -> bool:
        row = self.db.execute('SELECT state FROM dispatch WHERE item_key = ?', (key,)).fetchone()
        return row is not None and row[0] == 'SENT'
    def record(self, key, hotel, period, state, recipient, subject, body, ai_status, message_id='', error=''):
        self.db.execute('''INSERT INTO dispatch VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(item_key) DO UPDATE SET state=excluded.state,
            attempted_at=excluded.attempted_at, error=excluded.error,
            message_id=excluded.message_id, body=excluded.body, ai_status=excluded.ai_status''',
            (key, hotel, period, state, recipient, subject, body, ai_status,
             message_id, datetime.now(timezone.utc).isoformat(), error))
        self.db.commit()
