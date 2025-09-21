import sqlite3
conn = sqlite3.connect("omr_results.db")
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS results")
conn.commit()
conn.close()