
_MIGRATIONS: list[str] = [
    """CREATE TABLE IF NOT EXISTS __schema_version(
        schema_version INTEGER,
        migration: VARCHAR
    )"""
]
