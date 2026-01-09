from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterable

import mysql.connector

from config import DB_MODE, MYSQL_CONFIG, SQLITE_PATH


class Database:
    def __init__(self) -> None:
        self.mode = DB_MODE
        if self.mode not in {"mysql", "sqlite"}:
            self.mode = "sqlite"
        self._connection = None

    def connect(self) -> None:
        if self.mode == "mysql":
            self._connection = mysql.connector.connect(**MYSQL_CONFIG)
        else:
            self._connection = sqlite3.connect(SQLITE_PATH)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")

    @property
    def connection(self):
        if self._connection is None:
            self.connect()
        return self._connection

    def _format_query(self, query: str) -> str:
        if self.mode == "mysql":
            return query.replace("?", "%s")
        return query

    @contextmanager
    def cursor(self):
        cur = self.connection.cursor(dictionary=self.mode == "mysql")
        try:
            yield cur
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cur.close()

    def execute(self, query: str, params: Iterable[Any] | None = None) -> int:
        params = params or []
        query = self._format_query(query)
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur.lastrowid or 0

    def query_all(self, query: str, params: Iterable[Any] | None = None) -> list[dict]:
        params = params or []
        query = self._format_query(query)
        with self.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        if self.mode == "sqlite":
            return [dict(row) for row in rows]
        return rows

    def query_one(self, query: str, params: Iterable[Any] | None = None) -> dict | None:
        params = params or []
        query = self._format_query(query)
        with self.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
        if row is None:
            return None
        if self.mode == "sqlite":
            return dict(row)
        return row

    def now(self) -> str:
        return datetime.utcnow().isoformat(sep=" ", timespec="seconds")


db = Database()
