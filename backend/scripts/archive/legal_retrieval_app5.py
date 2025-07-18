import os
import json
import openai
import faiss
import numpy as np
import streamlit as st
import sqlite3
from dotenv import load_dotenv

# Page configuration (must be the first Streamlit command)
st.set_page_config(page_title="المستشار القانوني", layout="centered")

# Load environment variables
load_dotenv()
client = openai.OpenAI(api_key="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")

# Connect to SQLite and fetch articles
conn = sqlite3.connect("laws.db")
cursor = conn.cursor()
cursor.execute("SELECT article_number, article_text FROM articles")
rows = cursor.fetchall()
conn.close()

# Separate numbers and texts
numbers, texts = zip(*rows)


# Build FAISS index and cache it
@st.cache_resource
def build_index():
    response = client.embeddings.create(model="text-embedding-ada-002", input=texts)
    embeddings = np.array([d.embedding for d in response.data]).astype("float32")
    d = embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embeddings)
    return index, embeddings

index, embeddings = build_index()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# App header
st.title("⚖️ المستشار القانوني الذكي")

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Get user query
user_query = st.chat_input("📝 اطرح سؤالك القانوني:")

if user_query:
    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_query})

    # Generate query embedding
    q_res = client.embeddings.create(model="text-embedding-ada-002", input=[user_query])
    q_emb = np.array(q_res.data[0].embedding).astype("float32")

    # Retrieve top 3 most relevant articles
    D, I = index.search(np.array([q_emb]), k=3)
    matched_articles = [(numbers[i], texts[i]) for i in I[0]]

    # Format reference prompt
    references = "\n\n".join([f"📘 المادة {num}:\n\"{txt}\"" for num, txt in matched_articles])
    full_prompt = f"""أنت مساعد قانوني ذكي ودقيق. وظيفتك أن تُجيب على الأسئلة القانونية بالاستناد إلى المواد القانونية فقط، دون اجتهاد أو إضافة. استخدم لغة قانونية واضحة واذكر رقم المادة المرجعية داخل الإجابة.

المواد القانونية المرجعية:
{references}

🧾 استنادًا إلى النصوص أعلاه، أجب بدقة على السؤال التالي:
"{user_query}"
"""

    # Request answer from OpenAI with system message
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "أنت مساعد قانوني ذكي تجيب بدقة على الأسئلة بالاستناد إلى مواد القانون فقط."},
            {"role": "user", "content": full_prompt}
        ],
    )
    answer = completion.choices[0].message.content

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": answer})

    # Display reply
    with st.chat_message("assistant"):
        st.markdown(answer)

    # Show matched articles in expandable panels
    st.divider()
    st.subheader("📚 المواد القانونية المرجعية:")
    for num, txt in matched_articles:
        with st.expander(f"📖 المادة {num}"):
            st.write(txt)
