import os
import json
import openai
import faiss
import numpy as np
import streamlit as st
from dotenv import load_dotenv

st.set_page_config(page_title="المستشار القانوني", layout="centered")

# Load API key
load_dotenv()
client = openai.OpenAI(api_key="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")

# Load legal articles
with open("law.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

texts = [a["article_text"] for a in articles]
numbers = [a["article_number"] for a in articles]

# Compute embeddings (once per session)
@st.cache_resource
def build_index():
    response = client.embeddings.create(model="text-embedding-ada-002", input=texts)
    embeddings = np.array([d.embedding for d in response.data]).astype("float32")
    d = embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embeddings)
    return index, embeddings

index, embeddings = build_index()

# Streamlit UI
st.title("⚖️ المستشار القانوني الذكي")

query = st.text_input("📝 اطرح سؤالك القانوني:")

if query:
    # Embed the query
    q_res = client.embeddings.create(model="text-embedding-ada-002", input=[query])
    q_emb = np.array(q_res.data[0].embedding).astype("float32")

    # Search top 3
    D, I = index.search(np.array([q_emb]), k=3)

    # Build combined articles
    matched_articles = "\n\n".join(
        [f"المادة رقم {numbers[i]}:\n{texts[i]}" for i in I[0]]
    )

    # Chat Completion using all 3 articles
    prompt = "\n\n⚠️ لا تستخدم أي مصادر خارج النصوص أعلاه. لا تفترض. فقط أجب من المواد المذكورة."
    prompt += f"""السؤال التالي:\"{query}\"المواد القانونية الأقرب هي:{matched_articles}يرجى استخدام النصوص أعلاه للإجابة على السؤال بدقة وبلغة قانونية واضحة:"""

    resp = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    answer = resp.choices[0].message.content

    st.subheader("📜 المواد الأقرب:")
    st.write(matched_articles)

    st.subheader("🤖 إجابة المساعد:")
    st.write(answer)
