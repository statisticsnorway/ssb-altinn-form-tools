import json
import os
from datetime import datetime

from duckdb import DuckDBPyConnection
from duckdb import Statement
from ssb_parquedit import ParquEdit


class ParqueditConnection(DuckDBPyConnection):
    def execute(
        self,
        query: Statement | str,
        parameters: object = None,
        changelog: list[object] | None = None,
    ) -> DuckDBPyConnection:

        if isinstance(query, Statement):
            pass
        else:
            if "update" in query:
                assert changelog is not None
                assert len(changelog) != 0

            expression = query.split(";")
            for idx, expr in enumerate(expression):
                trimmed_expr = expr.lstrip().lower()
                if trimmed_expr.startswith("update") or trimmed_expr.startswith(
                    "delete"
                ):
                    assert changelog is not None
                    log_entry = changelog[idx]

        return super().execute(query, parameters)

    def executemany(
        self, query: Statement | str, parameters: object = None
    ) -> DuckDBPyConnection:
        return super().executemany(query, parameters)


def log_change(con: DuckDBPyConnection):
    latest_snapshot = con.execute(
        """SELECT snapshot_id FROM test_catalog.snapshots()
            ORDER BY snapshot_id DESC
            LIMIT 1 OFFSET 0;"""
    ).fetchone()
    second_latest_snapshot = con.execute(
        """SELECT snapshot_id FROM test_catalog.snapshots()
            ORDER BY snapshot_id DESC
            LIMIT 1 OFFSET 1;"""
    ).fetchone()
    print(latest_snapshot)

    if (latest_snapshot is None) or (second_latest_snapshot is None):
        print("No snapshots found for table.")
        return

    # Fetch updated rows between snapshots
    updates = con.execute(f"""
        SELECT *
        FROM ducklake_table_changes('test_catalog', 'main', 'skjemadata', {second_latest_snapshot[0]}, {latest_snapshot[0]})
     """).fetchall()
    updates = {}
    for row in updates:
        snapshot_id, rowid, commit_type, *values = row
        print(snapshot_id)
        print(rowid)
        print(values)
        print(commit_type)

        updates[rowid] = {commit_type: [snapshot_id, rowid, *values]}

    con.execute("""
        CREATE TABLE IF NOT EXISTS _history(
            snapshot_id BIGINT,
            old_row JSON,
            new_row JSON,
            message VARCHAR,
            author VARCHAR
        )
    """)
    for key, val in updates.items():
        new = val.get("update_postimage")
        old = val.get("update_preimage")


# === MAIN LOGIC ===
def run_update_check():
    parq = ParquEdit.local("data")
    con = parq._get_connection().raw
    # query = """CALL test_catalog.set_commit_message('Pedro', 'Inserting myself', extra_info => '{''foo'': 7, ''bar'': 10}');"""
    # con.execute(query)
    print(con.execute("""SELECT * FROM test_catalog.snapshots();""").fetchall())
    # con.execute(
    #    "UPDATE skjemadata SET verdi = 'tull' WHERE _id == 'cf123083-1a1d-4e53-bd82-dbf60d048891' "
    # ).commit()
    # print(parq.view("skjemadata", "_id == 'cf123083-1a1d-4e53-bd82-dbf60d048891'"))
    # con.execute(
    #    "UPDATE skjemadata SET verdi = '2. september - 8. september 2025' WHERE _id == 'cf123083-1a1d-4e53-bd82-dbf60d048891'"
    # ).commit()
    # print(parq.view("skjemadata", "_id == 'cf123083-1a1d-4e53-bd82-dbf60d048891'"))
    # Get the latest snapshot ID for the table

    # if not updates:
    #    print("No updated rows found.")
    # else:
    #    print(f"Found {len(updates)} updated rows.")
    #    for row_id, new_value in updates:
    #        process_update(row_id, new_value)

    # Save the latest snapshot ID
    # save_last_snapshot(latest_snapshot)

    log_change(con)
    con.close()


# === RUN SCRIPT ===
if __name__ == "__main__":
    run_update_check()
