import sqlite3


DB_PATH = "chat_messages.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_message(user_id: str, text: str, timestamp: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (user_id, text, timestamp) VALUES (?, ?, ?)",
        (user_id, text, timestamp),
    )
    conn.commit()
    conn.close()


def get_last_messages(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT user_id, text, timestamp FROM messages ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    return [{"user_id": row[0], "text": row[1], "timestamp": row[2]} for row in reversed(rows)]
