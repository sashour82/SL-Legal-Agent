import os
import json
import numpy as np
import faiss
import openai

# ✅ 1. Setup OpenAI client (v1 interface)
client = openai.OpenAI(api_key="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")

# ✅ 2. Load legal articles from JSON file
with open("law.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

texts = [a["article_text"] for a in articles]
numbers = [a["article_number"] for a in articles]

# ✅ 3. Generate embeddings for all articles
print("🔄 Generating embeddings...")
response = client.embeddings.create(
    model="text-embedding-ada-002",
    input=texts
)
embeddings = np.array([r.embedding for r in response.data]).astype("float32")

# ✅ 4. Build FAISS index
d = embeddings.shape[1]  # dimension
index = faiss.IndexFlatL2(d)
index.add(embeddings)

# ✅ 5. Interactive legal assistant loop
while True:
    query = input("\n🔎 Ask a legal question (or type 'exit'): ")
    if query.strip().lower() == "exit":
        break

    # a. Embed the query
    q_resp = client.embeddings.create(
        model="text-embedding-ada-002",
        input=[query]
    )
    q_emb = np.array(q_resp.data[0].embedding).astype("float32")

    # b. Search for closest article
    D, I = index.search(np.array([q_emb]), k=1)
    idx = I[0][0]
    matched_text = texts[idx]
    matched_num = numbers[idx]

    # c. Generate answer using GPT
    prompt = f"The following legal article (No. {matched_num}) is relevant:\n\n\"{matched_text}\"\n\nUse it to answer the question: '{query}'"
    chat_resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = chat_resp.choices[0].message.content

    # d. Display results
    print(f"\n📜 Closest article (No. {matched_num}):\n{matched_text}\n")
    print(f"🤖 Assistant's answer:\n{answer}")
