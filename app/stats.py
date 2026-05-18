import sqlite3
from pathlib import Path

DATABASE_TIMEOUT_SECONDS = 5


def initialize_stats_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path, timeout=DATABASE_TIMEOUT_SECONDS) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversion_stats (
                input_format TEXT NOT NULL,
                output_format TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (input_format, output_format)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS counters (
                name TEXT PRIMARY KEY,
                count INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def increment_conversion_count(
    database_path: Path,
    input_format: str,
    output_format: str,
) -> None:
    with sqlite3.connect(database_path, timeout=DATABASE_TIMEOUT_SECONDS) as connection:
        connection.execute(
            """
            INSERT INTO conversion_stats (input_format, output_format, count)
            VALUES (?, ?, 1)
            ON CONFLICT(input_format, output_format)
            DO UPDATE SET count = count + 1
            """,
            (input_format, output_format),
        )


def increment_failure_count(database_path: Path, reason: str) -> None:
    increment_counter(database_path, "conversion_failures")
    increment_counter(database_path, f"conversion_failures.{reason}")


def increment_failure_detail_count(
    database_path: Path,
    reason: str,
    detail_type: str,
    detail_value: str,
) -> None:
    increment_counter(
        database_path,
        f"conversion_failures.{reason}.{detail_type}.{detail_value}",
    )


def increment_counter(database_path: Path, name: str) -> None:
    with sqlite3.connect(database_path, timeout=DATABASE_TIMEOUT_SECONDS) as connection:
        connection.execute(
            """
            INSERT INTO counters (name, count)
            VALUES (?, 1)
            ON CONFLICT(name)
            DO UPDATE SET count = count + 1
            """,
            (name,),
        )


def get_counter(database_path: Path, name: str) -> int:
    with sqlite3.connect(database_path, timeout=DATABASE_TIMEOUT_SECONDS) as connection:
        row = connection.execute(
            """
            SELECT count
            FROM counters
            WHERE name = ?
            """,
            (name,),
        ).fetchone()

    if row is None:
        return 0

    return row[0]


def get_conversion_stats(database_path: Path) -> dict:
    with sqlite3.connect(database_path, timeout=DATABASE_TIMEOUT_SECONDS) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT input_format, output_format, count
            FROM conversion_stats
            ORDER BY count DESC, input_format, output_format
            """
        ).fetchall()

    failure_reasons = {
        "file_too_large": get_counter(database_path, "conversion_failures.file_too_large"),
        "invalid_image": get_counter(database_path, "conversion_failures.invalid_image"),
        "conversion_error": get_counter(database_path, "conversion_failures.conversion_error"),
    }
    failure_details = {
        "file_too_large": {
            "by_limit_mb": get_counter_group(
                database_path,
                "conversion_failures.file_too_large.limit_mb.",
            ),
        },
        "invalid_image": {
            "by_extension": get_counter_group(
                database_path,
                "conversion_failures.invalid_image.extension.",
            ),
            "by_content_type": get_counter_group(
                database_path,
                "conversion_failures.invalid_image.content_type.",
            ),
        },
    }

    return {
        "failures": {
            "total": get_counter(database_path, "conversion_failures"),
            "reasons": failure_reasons,
            "details": failure_details,
        },
        "conversions": [
            {
                "input_format": row["input_format"],
                "output_format": row["output_format"],
                "count": row["count"],
            }
            for row in rows
        ]
    }


def get_counter_group(database_path: Path, prefix: str) -> dict:
    with sqlite3.connect(database_path, timeout=DATABASE_TIMEOUT_SECONDS) as connection:
        rows = connection.execute(
            """
            SELECT name, count
            FROM counters
            WHERE name LIKE ?
            ORDER BY count DESC, name
            """,
            (prefix + "%",),
        ).fetchall()

    return {
        name.removeprefix(prefix): count
        for name, count in rows
    }
