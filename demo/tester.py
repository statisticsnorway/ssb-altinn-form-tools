import pprint
import sqlite3

import pandas as pd

conn = sqlite3.connect("/home/dbo/Github/ssb-altinn-form-tools/demo/db.db")
results = conn.execute("SELECT * FROM skjemadata").fetchall()

for res in results:
    # if "kommNaering" in res[6]:
    pprint.pprint(res)
print(pd.DataFrame(results))
