import os
import json
import openai
import faiss
import numpy as np
import streamlit as st
from dotenv import load_dotenv

# Page configuration (must be first Streamlit call)
st.set_page_config(page_title="المستشار القانوني", layout="centered")

# Load environment variables
load_dotenv()
client = openai.OpenAI(api_key="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")

# Load legal articles from JSON file
with open("law.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

texts = [a["article_text"] for a in articles]
numbers = [a["article_number"] for a in articles]

# Build FAISS index (cached to avoid recomputation)
@st.cache_resource
def build_index():
    response = client.embeddings.create(model="text-embedding-ada-002", input=texts)
    embeddings = np.array([d.embedding for d in response.data]).astype("float32")
    d = embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embeddings)
    return index, embeddings

index, embeddings = build_index()

# Initialize conversation history if not already present
if "messages" not in st.session_state:
    st.session_state.messages = []

# App UI
st.title("⚖️ المستشار القانوني الذكي")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_query = st.chat_input("📝 اطرح سؤالك القانوني:")

if user_query:
    # Add user message to session
    st.session_state.messages.append({"role": "user", "content": user_query})

    # Generate query embedding
    q_res = client.embeddings.create(model="text-embedding-ada-002", input=[user_query])
    q_emb = np.array(q_res.data[0].embedding).astype("float32")

    # Search top 3 articles
    D, I = index.search(np.array([q_emb]), k=3)
    matched_articles = [(numbers[i], texts[i]) for i in I[0]]

    # Build reference prompt from top articles
    references = "\n\n".join(
        [f"📘 المادة {num}:\n\"{txt}\"" for num, txt in matched_articles]
    )
    full_prompt = f"{references}\n\n🧾 استنادًا إلى المواد أعلاه، أجب على السؤال التالي:\n'{user_query}'"

    # Generate answer from OpenAI
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": full_prompt}],
    )
    answer = completion.choices[0].message.content

    # Add assistant message to session
    st.session_state.messages.append({"role": "assistant", "content": answer})

    # Display response
    with st.chat_message("assistant"):
        st.markdown(answer)

    # Show matched articles in expandable view
    st.divider()
    st.subheader("📚 المواد القانونية المرجعية:")
    for num, txt in matched_articles:
        with st.expander(f"📖 المادة {num}"):
            st.write(txt)
