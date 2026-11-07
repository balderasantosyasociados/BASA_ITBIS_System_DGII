import sqlite3

DB_PATH = "itbis_sistem_dgii_full.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
print("Tables:", [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
for table in ['empresas_clientes', 'purchases_606', 'sales_invoices']:
    print(f"\nColumns for {table}:")
    for col in cursor.execute(f"PRAGMA table_info({table})").fetchall():
        print(col[1], col[2])
conn.close()
