"""
SQLite-based persistent memory store.

Stores previous research queries, results, and full reports
for retrieval and reference in future searches.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime

from agent.config import Config
from agent.models import MemoryRecord, ResearchReport

logger = logging.getLogger(__name__)


class MemoryStore:
    """Persistent storage for research history using SQLite."""

    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or Config.MEMORY_DB_PATH
        # Ensure directory exists
        os.makedirs(os.path.dirname(self._db_path) if os.path.dirname(self._db_path) else ".", exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    sources_used TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    full_report_json TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_query ON research_history(query)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON research_history(timestamp)
            """)

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self._db_path)

    def store(self, report: ResearchReport):
        """
        Store a research report in memory.

        Args:
            report: The completed research report to store.
        """
        try:
            sources_str = ", ".join(s.value for s in report.sources_used)
            report_json = report.model_dump_json()

            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO research_history (query, timestamp, sources_used, summary, full_report_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        report.query,
                        report.timestamp,
                        sources_str,
                        report.executive_summary[:500],
                        report_json,
                    ),
                )

            logger.info(f"Stored research report for query: '{report.query}'")

        except Exception as e:
            logger.error(f"Error storing report: {e}")

    def get_history(self, limit: int = 20) -> list[MemoryRecord]:
        """
        Retrieve recent research history.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of MemoryRecord objects, most recent first.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT id, query, timestamp, sources_used, summary, full_report_json
                    FROM research_history
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()

            return [
                MemoryRecord(
                    id=row[0],
                    query=row[1],
                    timestamp=row[2],
                    sources_used=row[3],
                    summary=row[4],
                    full_report_json=row[5],
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error retrieving history: {e}")
            return []

    def get_report_by_id(self, record_id: int) -> ResearchReport | None:
        """
        Retrieve a full research report by its ID.

        Args:
            record_id: The database ID of the record.

        Returns:
            The full ResearchReport, or None if not found.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "SELECT full_report_json FROM research_history WHERE id = ?",
                    (record_id,),
                )
                row = cursor.fetchone()

            if row:
                return ResearchReport.model_validate_json(row[0])
            return None

        except Exception as e:
            logger.error(f"Error retrieving report {record_id}: {e}")
            return None

    def search_history(self, query: str, limit: int = 10) -> list[MemoryRecord]:
        """
        Search previous research by query text.

        Args:
            query: Search text to match against past queries.
            limit: Maximum results.

        Returns:
            Matching MemoryRecord objects.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT id, query, timestamp, sources_used, summary, full_report_json
                    FROM research_history
                    WHERE query LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", limit),
                )
                rows = cursor.fetchall()

            return [
                MemoryRecord(
                    id=row[0],
                    query=row[1],
                    timestamp=row[2],
                    sources_used=row[3],
                    summary=row[4],
                    full_report_json=row[5],
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error searching history: {e}")
            return []

    def clear_history(self):
        """Delete all stored research history."""
        try:
            with self._get_conn() as conn:
                conn.execute("DELETE FROM research_history")
            logger.info("Research history cleared")
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
