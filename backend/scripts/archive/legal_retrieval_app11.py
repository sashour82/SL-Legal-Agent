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

# Define dynamic instructions for each intent
intent_instructions = {
    "عقوبة": "✔️ وضّح نوع العقوبة وحدّتها كما وردت في النص.",
    "شروط التطبيق": "✔️ بيّن الشروط اللازمة لتطبيق المادة.",
    "إجراء قانوني": "✔️ استعرض الخطوات القانونية التي يجب اتباعها.",
    "الاختصاص": "✔️ حدد الجهة أو المحكمة المختصة بهذا النوع من القضايا.",
    "استشارة عامة": "✔️ قدم ملخصًا قانونيًا بالإشارة للمواد ذات الصلة إن وُجدت.",
    "تعريف قانوني": "✔️ عرّف المصطلح إن كان مذكورًا في القانون.",
    "مدة زمنية": "✔️ اذكر المدة القانونية بوضوح، مع الاستناد للمادة.",
    "مقارنة قانونية": "✔️ قارن بين الحالتين باستخدام المواد ذات العلاقة.",
    "تفسير مادة": "✔️ فسّر المادة بلغة مبسطة دون الإخلال بالنص القانوني."
}

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

    # Step 3: FAISS retrieval with distance
    D, I = index.search(np.array([q_emb]), k=10)

    # Step 4: Keyword extraction
    keywords = [word for word in re.findall(r'\b\w{4,}\b', user_query) if re.match(r'^[\u0600-\u06FF]+$', word)]

    # Step 5: Ranking logic
    scored_matches = []
    for rank, idx in enumerate(I[0]):
        article_num = numbers[idx]
        article_text = texts[idx]

        # Semantic similarity
        distance = D[0][rank]
        semantic_similarity = 1 / (1 + distance)

        # Keyword overlap score
        keyword_overlap = sum(1 for kw in keywords if kw in article_text) / (len(keywords) + 1e-5)

        # Intent-based boost (بسيط حاليًا)
        boost = 0.1 if detected_intent in article_text else 0.0

        # Total score
        total_score = 0.6 * semantic_similarity + 0.3 * keyword_overlap + 0.1 * boost

        scored_matches.append((total_score, article_num, article_text))

    # Step 6: Sort and select top articles
    scored_matches.sort(reverse=True)
    matched_articles = [(num, txt) for _, num, txt in scored_matches[:3]]

    # Step 7: Build improved prompt
    references = "\n\n".join([f"📘 المادة {num}:\n\"{txt}\"" for num, txt in matched_articles])
    extra_instruction = intent_instructions.get(detected_intent, "")
    full_prompt = f"""
أنت مساعد قانوني ذكي وخبير في القانون الفلسطيني، ومهمتك أن تُجيب فقط بالاستناد إلى المواد القانونية المقدمة، دون أي اجتهاد قانوني، إلا إذا طُلب منك ذلك صراحة.

📌 تعليمات أساسية:
- استشهد صراحة برقم المادة.
- لا تكرر نص المادة كاملًا إذا لم يكن ضروريًا.
- إذا لم تجد مادة قانونية تنطبق على السؤال، اذكر ذلك بوضوح.
{extra_instruction}

🎯 نوع السؤال: {detected_intent}
🔍 السؤال المطروح: "{user_query}"

📚 المواد القانونية المرجعية:
{references}

✍️ الإجابة القانونية المطلوبة:
"""

    # Step 8: Completion
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
