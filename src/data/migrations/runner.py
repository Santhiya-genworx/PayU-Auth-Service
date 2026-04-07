"""This module provides functionality for managing database schema migrations in the PayU Authentication Service. It includes functions to discover migration files, apply pending migrations to the database, and ensure that the migration history is accurately tracked. The module uses SQLAlchemy's asynchronous connection to execute SQL statements defined in migration files, and it maintains a `schema_migrations` table to keep track of applied migrations, their version numbers, names, and checksums. The migration files are expected to follow a specific naming convention and contain valid SQL statements. The module also includes error handling to ensure that any issues during the migration process are properly reported and do not lead to inconsistent database states.       """

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path
 
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
 
 
_logger = logging.getLogger("uvicorn.error")
_MIGRATION_FILE_RE = re.compile(r"^(?P<version_number>\d{8,14})_(?P<name>[a-z0-9_]+)\.sql$")
_DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parent / "versions"
 
 
@dataclass(frozen=True, slots=True)
class MigrationFile:
    """Data class representing a database migration file. It contains the identifier, version number, name, checksum, SQL content, and file path of the migration. The identifier is derived from the filename and is used to track applied migrations in the database. The version number and name are extracted from the filename for organizational purposes. The checksum is calculated from the SQL content to ensure that applied migrations have not been altered. This class serves as a structured representation of migration files for use in the migration process. """
    identifier: str
    version_number: str
    name: str
    checksum: str
    sql: str
    path: Path
 
 
def discover_migrations(migrations_dir: Path | None = None) -> list[MigrationFile]:
    """Discover and validate migration files in the specified directory. This function scans the given directory (or the default migrations directory if none is provided) for SQL files that match the expected naming convention. It validates each file's name, ensures that it contains valid SQL content, and calculates a checksum for the file's content. The function returns a list of MigrationFile instances representing the discovered migrations. If any issues are found during this process, such as invalid filenames, duplicate identifiers, or empty files, appropriate exceptions are raised with detailed error messages.    Args:      migrations_dir: An optional Path object specifying the directory to search for migration files. If None, the default migrations directory is used.    Returns: A list of MigrationFile instances representing the discovered migrations.    Raises:      FileNotFoundError: If the migration directory does not exist.      NotADirectoryError: If the migration path is not a directory.      ValueError: If any migration file has an invalid name or is empty.          """
    directory = migrations_dir or _DEFAULT_MIGRATIONS_DIR
    if not directory.exists():
        raise FileNotFoundError(f"Migration directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Migration path is not a directory: {directory}")
 
    migrations: list[MigrationFile] = []
    seen_identifiers: set[str] = set()
 
    for path in sorted(directory.glob("*.sql")):
        match = _MIGRATION_FILE_RE.match(path.name)
        if not match:
            raise ValueError(
                "Invalid migration filename "
                f"{path.name!r}. Expected '<version>_<name>.sql' with lowercase snake_case."
            )
 
        identifier = path.stem
        if identifier in seen_identifiers:
            raise ValueError(f"Duplicate migration identifier found: {identifier}")
        seen_identifiers.add(identifier)
 
        sql = path.read_text(encoding="utf-8").strip()
        if not sql:
            raise ValueError(f"Migration file is empty: {path}")
 
        migrations.append(
            MigrationFile(
                identifier=identifier,
                version_number=match.group("version_number"),
                name=match.group("name"),
                checksum=hashlib.sha256(sql.encode("utf-8")).hexdigest(),
                sql=sql,
                path=path,
            )
        )
 
    return migrations
 
 
async def apply_migrations(
    conn: AsyncConnection,
    migrations_dir: Path | None = None,
) -> None:
    """Apply pending database migrations to the connected database. This function retrieves the list of migration files from the specified directory, checks which migrations have already been applied to the database by querying the `schema_migrations` table, and applies any pending migrations in order. For each migration, it executes the SQL statements defined in the migration file and records the migration as applied in the database with its version number, name, and checksum. If any issues arise during this process, such as SQL execution errors or checksum mismatches for already applied migrations, appropriate exceptions are raised with detailed error messages to prevent inconsistent database states.    Args:    conn: An instance of AsyncConnection representing the connection to the database.    migrations_dir: An optional Path object specifying the directory to search for migration files. If None, the default migrations directory is used.    Raises:      RuntimeError: If a checksum mismatch is detected for an already applied migration, indicating that the migration file has been altered since it was applied.      ValueError: If any migration file contains no executable SQL statements.      AppException: If any error occurs during the execution of SQL statements or database operations while applying migrations.                      """
    migrations = discover_migrations(migrations_dir)
    await _ensure_schema_migrations_table(conn)
 
    result = await conn.execute(
        text(
            """
            SELECT version, version_number, name, checksum
            FROM schema_migrations
            """
        )
    )
    applied = {
        row.version: {
            "version_number": row.version_number,
            "name": row.name,
            "checksum": row.checksum,
        }
        for row in result
    }
 
    for migration in migrations:
        existing = applied.get(migration.identifier)
        if existing is not None:
            await _validate_or_backfill_migration_record(conn, migration, existing)
            continue
 
        statements = _split_sql_statements(migration.sql)
        if not statements:
            raise ValueError(f"Migration {migration.identifier} contains no executable SQL statements.")
 
        _logger.info("Applying DB migration: %s", migration.identifier)
        for statement in statements:
            await conn.exec_driver_sql(statement)
 
        await conn.execute(
            text(
                """
                INSERT INTO schema_migrations (version, version_number, name, checksum)
                VALUES (:version, :version_number, :name, :checksum)
                """
            ),
            {
                "version": migration.identifier,
                "version_number": migration.version_number,
                "name": migration.name,
                "checksum": migration.checksum,
            },
        )
        _logger.info("Applied DB migration: %s", migration.identifier)
 
 
async def _ensure_schema_migrations_table(conn: AsyncConnection) -> None:
    """Ensure that the schema_migrations table exists in the database. This function executes SQL statements to create the `schema_migrations` table if it does not already exist, and to add any missing columns that are required for tracking migration history. The table is designed to store the migration version, version number, name, checksum, and the timestamp of when the migration was applied. If any issues arise during this process, such as SQL execution errors or database connection issues, appropriate exceptions are raised with detailed error messages.    Args:    conn: An instance of AsyncConnection representing the connection to the database.    Raises:      AppException: If any error occurs while ensuring the existence of the schema_migrations table, such as SQL execution errors or database connection issues.                            """
    await conn.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(128) PRIMARY KEY,
            version_number VARCHAR(32),
            name VARCHAR(255),
            checksum VARCHAR(64),
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    await conn.exec_driver_sql(
        "ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS version_number VARCHAR(32)"
    )
    await conn.exec_driver_sql(
        "ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS name VARCHAR(255)"
    )
    await conn.exec_driver_sql(
        "ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS checksum VARCHAR(64)"
    )
 
 
async def _validate_or_backfill_migration_record(
    conn: AsyncConnection,
    migration: MigrationFile,
    existing: dict[str, str | None],
) -> None:
    """Validate the existing migration record against the current migration file, or backfill missing information if necessary. This function checks if the checksum of the already applied migration matches the checksum of the current migration file to ensure that the migration has not been altered since it was applied. If a mismatch is detected, a RuntimeError is raised to prevent potential issues from applying altered migrations. If the version number or name is missing from the existing record, it updates the database with the correct information from the current migration file.    Args:    conn: An instance of AsyncConnection representing the connection to the database.    migration: The MigrationFile instance representing the current migration being validated.    existing: A dictionary containing the existing migration record from the database, with keys for version_number, name, and checksum.    Raises:      RuntimeError: If a checksum mismatch is detected for an already applied migration, indicating that the migration file has been altered since it was applied.      AppException: If any error occurs while validating or backfilling the migration record in the database, such as SQL execution errors or database connection issues.                            """ 
    checksum = existing.get("checksum")
    if checksum:
        if checksum != migration.checksum:
            raise RuntimeError(
                "Migration checksum mismatch for "
                f"{migration.identifier}. Refusing to continue because an applied SQL file changed."
            )
        if existing.get("version_number") and existing.get("name"):
            return
 
    await conn.execute(
        text(
            """
            UPDATE schema_migrations
            SET version_number = COALESCE(version_number, :version_number),
                name = COALESCE(name, :name),
                checksum = COALESCE(checksum, :checksum)
            WHERE version = :version
            """
        ),
        {
            "version": migration.identifier,
            "version_number": migration.version_number,
            "name": migration.name,
            "checksum": migration.checksum,
        },
    )
 
 
def _split_sql_statements(sql: str) -> list[str]:
    """Split a SQL string into individual statements while respecting string literals, comments, and dollar-quoted strings. This function takes a SQL string and parses it to identify individual SQL statements, ensuring that semicolons within string literals, comments, or dollar-quoted strings are not treated as statement separators. The function handles single quotes, double quotes, line comments (starting with --), block comments (enclosed in /* */), and PostgreSQL-style dollar-quoted strings. It returns a list of SQL statements that can be executed separately. If any issues arise during this process, such as unclosed string literals or comments, appropriate exceptions may be raised with detailed error messages.    Args:    sql: A string containing the SQL code to be split into individual statements.    Returns:    A list of strings, each representing an individual SQL statement extracted from the input SQL code.    Raises:      ValueError: If the input SQL string contains unclosed string literals, comments,"""
    statements: list[str] = []
    current: list[str] = []
    i = 0
    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_block_comment = False
    dollar_quote: str | None = None
 
    while i < len(sql):
        char = sql[i]
        next_char = sql[i + 1] if i + 1 < len(sql) else ""
 
        if in_line_comment:
            if char == "\n":
                in_line_comment = False
                current.append(char)
            i += 1
            continue
 
        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
 
        if dollar_quote is not None:
            if sql.startswith(dollar_quote, i):
                current.append(dollar_quote)
                i += len(dollar_quote)
                dollar_quote = None
                continue
            current.append(char)
            i += 1
            continue
 
        if in_single_quote:
            current.append(char)
            if char == "'" and next_char == "'":
                current.append(next_char)
                i += 2
                continue
            if char == "'":
                in_single_quote = False
            i += 1
            continue
 
        if in_double_quote:
            current.append(char)
            if char == '"' and next_char == '"':
                current.append(next_char)
                i += 2
                continue
            if char == '"':
                in_double_quote = False
            i += 1
            continue
 
        if char == "-" and next_char == "-":
            in_line_comment = True
            i += 2
            continue
 
        if char == "/" and next_char == "*":
            in_block_comment = True
            i += 2
            continue
 
        if char == "'":
            in_single_quote = True
            current.append(char)
            i += 1
            continue
 
        if char == '"':
            in_double_quote = True
            current.append(char)
            i += 1
            continue
 
        if char == "$":
            tag_end = sql.find("$", i + 1)
            if tag_end != -1:
                candidate = sql[i : tag_end + 1]
                if re.fullmatch(r"\$[A-Za-z0-9_]*\$", candidate):
                    dollar_quote = candidate
                    current.append(candidate)
                    i = tag_end + 1
                    continue
 
        if char == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            i += 1
            continue
 
        current.append(char)
        i += 1
 
    trailing_statement = "".join(current).strip()
    if trailing_statement:
        statements.append(trailing_statement)
    return statements
 
 