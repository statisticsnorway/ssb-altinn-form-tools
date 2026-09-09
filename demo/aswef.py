from ssb_parquedit import ParquEdit

parquedit_conn = ParquEdit.local("data")
from datetime import datetime

import pandas as pd

schema = {
    "properties": {
        "period": {"type": "string"},
        "dato_mottatt": {"type": "date-time"},
    },
    "required": [
        "period",
    ],
}
table_name = "skjemamottak"
if parquedit_conn.exists(table_name) is False:
    parquedit_conn.create_table(
        table_name,
        schema,
        product_name=table_name,
        user_defined_id=["period"],
        fill=False,
        part_columns=["period"],
    )
in_df = pd.DataFrame([{"period": "test", "dato_mottatt": datetime(2026, 8, 2)}])
print(in_df.dtypes)
parquedit_conn.insert_data(
    "skjemamottak",
    pd.DataFrame([{"period": "test", "dato_mottatt": datetime(2026, 8, 2)}]),
)

result = parquedit_conn.view("skjemamottak")
print(result.dtypes)
assert result.dtypes["dato_mottatt"] == in_df.dtypes["dato_mottatt"]
