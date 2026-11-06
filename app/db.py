import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents(id TEXT PRIMARY KEY,name TEXT NOT NULL,description TEXT NOT NULL,token_hash TEXT NOT NULL UNIQUE,allowed_actions TEXT NOT NULL,approval_actions TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY,agent_id TEXT NOT NULL,action TEXT NOT NULL,resource TEXT NOT NULL,status TEXT NOT NULL,reason TEXT NOT NULL,payload TEXT NOT NULL,outcome TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(agent_id) REFERENCES agents(id));
CREATE INDEX IF NOT EXISTS idx_actions_created ON actions(created_at DESC);
CREATE TABLE IF NOT EXISTS work_items(id TEXT PRIMARY KEY,title TEXT NOT NULL,description TEXT NOT NULL,departments TEXT NOT NULL,status TEXT NOT NULL,priority TEXT NOT NULL,result TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_work_items_updated ON work_items(updated_at DESC);
"""

class Database:
    def __init__(self, path):
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as c:
            c.executescript(SCHEMA)

    def connect(self):
        c = sqlite3.connect(self.path, check_same_thread=False)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        return c

    def execute(self, query, params=()):
        with self.connect() as c:
            c.execute(query, params)

    def one(self, query, params=()):
        with self.connect() as c:
            row = c.execute(query, params).fetchone()
            return dict(row) if row else None

    def all(self, query, params=()):
        with self.connect() as c:
            return [dict(r) for r in c.execute(query, params).fetchall()]

    @staticmethod
    def decode_agent(row):
        row["allowed_actions"] = json.loads(row["allowed_actions"])
        row["approval_actions"] = json.loads(row["approval_actions"])
        row.pop("token_hash", None)
        return row

    @staticmethod
    def decode_action(row):
        row["payload"] = json.loads(row["payload"])
        row["outcome"] = json.loads(row["outcome"]) if row["outcome"] else None
        return row
