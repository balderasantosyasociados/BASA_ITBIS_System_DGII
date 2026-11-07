# Verificamos la estructura y columnas de la tabla sales_invoices para corregir cualquier restricción NOT NULL
import sqlite3

conn = sqlite3.connect("itbis_sistem_dgii_full.db", timeout=15.0)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(sales_invoices)")
cols = cursor.fetchall()
print("Columnas en sales_invoices:", cols)
conn.close()
