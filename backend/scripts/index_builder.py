import os
import sqlite3
import numpy as np
import faiss
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "laws.db")
INDEX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "faiss.index")

def load_articles():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT article_number, article_text FROM articles")
    rows = cursor.fetchall()
    conn.close()
    return zip(*rows)  # returns (numbers, texts)

def build_faiss_index(texts):
    response = client.embeddings.create(model="text-embedding-3-large", input=list(texts))
    embeddings = np.array([d.embedding for d in response.data]).astype("float32")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index, embeddings

def save_index(index):
    faiss.write_index(index, INDEX_PATH)

def main():
    print("📚 تحميل المواد القانونية...")
    numbers, texts = load_articles()

    print("🔍 إنشاء Embeddings...")
    index, _ = build_faiss_index(texts)

    print("💾 حفظ الفهرس إلى:", INDEX_PATH)
    save_index(index)

    print("✅ تم إنشاء الفهرس بنجاح.")

if __name__ == "__main__":
    main()