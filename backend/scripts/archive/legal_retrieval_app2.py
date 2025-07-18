import os
import json
import openai
import faiss
import numpy as np
import streamlit as st
from dotenv import load_dotenv

# Page config (must be first)
st.set_page_config(page_title="⚖️ المستشار القانوني الذكي", layout="centered")

# Load API key
load_dotenv()
client = openai.OpenAI(api_key="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")

# Load data
with open("law.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

texts = [a["article_text"] for a in articles]
numbers = [a["article_number"] for a in articles]

# Build FAISS index (cached)
@st.cache_resource
def build_index():
    response = client.embeddings.create(model="text-embedding-ada-002", input=texts)
    embeddings = np.array([d.embedding for d in response.data]).astype("float32")
    d = embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embeddings)
    return index, embeddings

index, embeddings = build_index()

# Header
st.markdown("<h1 style='text-align: center;'>⚖️ المستشار القانوني الذكي</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>اكتب سؤالك وسنبحث في القوانين للإجابة عليه</p>", unsafe_allow_html=True)

# User input
query = st.text_input("📝 اطرح سؤالك القانوني هنا:")

if query:
    q_res = client.embeddings.create(model="text-embedding-ada-002", input=[query])
    q_emb = np.array(q_res.data[0].embedding).astype("float32")

    # Search top 3 articles
    D, I = index.search(np.array([q_emb]), k=3)

    related_articles = []
    for i in range(3):
        idx = I[0][i]
        related_articles.append((numbers[idx], texts[idx]))

    # Create prompt
    joined_articles = "\n\n".join([f"المادة {num}:\n\"{text}\"" for num, text in related_articles])
    prompt = f"المواد القانونية التالية قد تكون مرتبطة بالسؤال:\n\n{joined_articles}\n\nأجب على هذا السؤال باستخدامها: '{query}'"

    # Chat completion
    resp = client.chat.completions.create(model="gpt-4", messages=[{"role":"user","content":prompt}], temperature=0.2)
    answer = resp.choices[0].message.content

    # Display articles
    st.subheader("📜 المواد القانونية الأقرب:")
    for num, text in related_articles:
        with st.expander(f"📘 المادة رقم {num}"):
            st.markdown(f"<div style='direction: rtl; text-align: justify;'>{text}</div>", unsafe_allow_html=True)

    # Display answer
    st.subheader("🤖 إجابة المستشار القانوني:")
    st.success(answer)

# Footer
st.markdown("<hr><p style='text-align:center; color:gray;'>🚀 مشروع SmartLancer - 2025</p>", unsafe_allow_html=True)
