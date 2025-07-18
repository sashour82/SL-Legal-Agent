import os
import json
import openai
import faiss
import numpy as np
import streamlit as st
import sqlite3
from dotenv import load_dotenv
import re

# Page configuration
st.set_page_config(page_title="المستشار القانوني", layout="centered")

# Load API key
load_dotenv()
client = openai.OpenAI(api_key="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")

# Load articles from SQLite
conn = sqlite3.connect("laws.db")
cursor = conn.cursor()
cursor.execute("SELECT article_number, article_text FROM articles")
rows = cursor.fetchall()
conn.close()

numbers, texts = zip(*rows)

# Build FAISS index
@st.cache_resource
def build_index():
    response = client.embeddings.create(model="text-embedding-3-large", input=texts)
    embeddings = np.array([d.embedding for d in response.data]).astype("float32")
    d = embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embeddings)
    return index, embeddings

index, embeddings = build_index()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Define intent labels
intent_labels = [
    "عقوبة", "شروط التطبيق", "إجراء قانوني", "الاختصاص", "استشارة عامة",
    "تعريف قانوني", "مدة زمنية", "مقارنة قانونية", "تفسير مادة"
]

# Streamlit UI
st.title("⚖️ المستشار القانوني الذكي")

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_query = st.chat_input("📝 اطرح سؤالك القانوني:")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})

    # Step 1: Detect intent
    intent_prompt = f"""صنف نية السؤال التالي إلى واحدة فقط من التصنيفات التالية بدقة شديدة دون شرح:
{", ".join(intent_labels)}.

السؤال:
"{user_query}"

الإجابة المطلوبة: اسم التصنيف فقط دون شرح.
"""
    intent_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": intent_prompt}]
    )
    detected_intent = intent_response.choices[0].message.content.strip()
    st.info(f"🎯 **تصنيف نية السؤال:** {detected_intent}")

    # Step 2: Embed query
    q_res = client.embeddings.create(model="text-embedding-3-large", input=[user_query])
    q_emb = np.array(q_res.data[0].embedding).astype("float32")

    # Step 3: FAISS retrieval
    D, I = index.search(np.array([q_emb]), k=10)
    top_matches = [(numbers[i], texts[i]) for i in I[0]]

    # Step 4: Keyword extraction
    keywords = [word for word in re.findall(r'\b\w{4,}\b', user_query) if re.match(r'^[\u0600-\u06FF]+$', word)]

    # Step 5: Prioritized matching
    high_score = [(n, t) for n, t in top_matches if any(kw in t for kw in keywords)]
    low_score = [item for item in top_matches if item not in high_score]

    # Combine with priority: keyword + semantic match first
    prioritized_matches = high_score + low_score
    matched_articles = prioritized_matches[:3]

    # Step 6: Build prompt
    references = "\n\n".join([f"📘 المادة {num}:\n\"{txt}\"" for num, txt in matched_articles])
    full_prompt = f"""
أنت مساعد قانوني ذكي وخبير في القوانين، مهمتك أن تجيب فقط بالاستناد إلى النصوص القانونية المعطاة دون أي اجتهاد أو تحليل إضافي، إلا إذا طُلب منك ذلك صراحة.

✅ استخدم لغة تشريعية واضحة.
✅ استشهد صراحة برقم المادة (مثلاً: "وفقًا للمادة 12").
✅ لا تكرر نص المادة إن لم يكن ضروريًا.
✅ إذا لم تجد نصًا ينطبق على السؤال، اذكر ذلك بوضوح.

🔍 سياق السؤال: "{user_query}"

📚 المواد القانونية المرجعية:
{references}

📥 المطلوب: أجب على السؤال أعلاه بدقة وبالاستناد إلى المواد فقط.
"""

    # Step 7: Completion
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "أنت مساعد قانوني ذكي تجيب بدقة على الأسئلة بالاستناد إلى مواد القانون فقط."},
            {"role": "user", "content": full_prompt}
        ],
    )
    answer = completion.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": answer})

    # Show assistant response
    with st.chat_message("assistant"):
        st.markdown(answer)

    # Show references
    st.divider()
    st.subheader("📚 المواد القانونية المرجعية:")
    for num, txt in matched_articles:
        with st.expander(f"📖 المادة {num}"):
            st.write(txt)
