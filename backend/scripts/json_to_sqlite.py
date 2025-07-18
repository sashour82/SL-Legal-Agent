import json
import sqlite3
import os

# تحديد المسارات بناءً على هيكل المشروع
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
JSON_PATH = os.path.join(BASE_DIR, "data", "law.json")
DB_PATH = os.path.join(BASE_DIR, "db", "laws.db")

# تحميل البيانات من law.json
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# الاتصال بقاعدة البيانات وإنشاء الجدول
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    law_name TEXT,
    article_number TEXT,
    article_text TEXT,
    intent TEXT
)
""")

# إدخال البيانات
for item in data:
    cursor.execute("""
        INSERT INTO articles (law_name, article_number, article_text, intent)
        VALUES (?, ?, ?, ?)
    """, (
        item.get("law_name", ""),
        item.get("article_number", ""),
        item.get("article_text", ""),
        item.get("intent", None)
    ))

conn.commit()
conn.close()
print("✅ تم إنشاء قاعدة البيانات وإدخال المواد القانونية بنجاح.")
