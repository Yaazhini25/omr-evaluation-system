import sqlite3

conn = sqlite3.connect("omr_results.db")
c = conn.cursor()
c.execute("SELECT * FROM results")
data = c.fetchall()
print(data)
conn.close()
