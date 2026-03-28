import sqlite3

conn = sqlite3.connect('barbearia.db')
cursor = conn.execute("PRAGMA table_info(agendamentos)")
for row in cursor:
    print(row)
conn.close()