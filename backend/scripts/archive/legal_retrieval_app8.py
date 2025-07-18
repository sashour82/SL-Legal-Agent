import json
import os
import re
import sqlite3
import faiss
import numpy as np
import openai
import streamlit as st
from dotenv import load_dotenv

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

# Build FAISS index and cache it
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

# Define possible intent labels
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

    # Step 1: Detect intent category
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

    # Display detected intent
    st.info(f"🎯 **تصنيف نية السؤال:** {detected_intent}")

    # Step 2: Embed the query
    q_res = client.embeddings.create(model="text-embedding-3-large", input=[user_query])
    q_emb = np.array(q_res.data[0].embedding).astype("float32")

    # Step 3: Retrieve top 10 articles
    D, I = index.search(np.array([q_emb]), k=10)
    top_matches = [(numbers[i], texts[i]) for i in I[0]]

    # Step 4: Filter articles by Arabic keywords
    keywords = [word for word in re.findall(r'\b\w{4,}\b', user_query) if re.match(r'^[\u0600-\u06FF]+$', word)]
    filtered_matches = [(num, txt) for num, txt in top_matches if any(kw in txt for kw in keywords)]

    # Step 5: Select final matches
    matched_articles = filtered_matches[:3] if filtered_matches else top_matches[:3]

    # Step 6: Construct the final prompt
    references = "\n\n".join([f"📘 المادة {num}:\n\"{txt}\"" for num, txt in matched_articles])
    full_prompt = f"""أنت مساعد قانوني ذكي ودقيق. وظيفتك أن تُجيب على الأسئلة القانونية بالاستناد إلى المواد القانونية فقط، دون اجتهاد أو إضافة. استخدم لغة قانونية واضحة واذكر رقم المادة المرجعية داخل الإجابة.

المواد القانونية المرجعية:
{references}

🧾 استنادًا إلى النصوص أعلاه، أجب بدقة على السؤال التالي:
"{user_query}"
"""

    # Step 7: Get assistant answer
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "أنت مساعد قانوني ذكي تجيب بدقة على الأسئلة بالاستناد إلى مواد القانون فقط."},
            {"role": "user", "content": full_prompt}
        ],
    )
    answer = completion.choices[0].message.content

    # Step 8: Save and display response
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

    # Step 9: Show matched legal articles
    st.divider()
    st.subheader("📚 المواد القانونية المرجعية:")
    for num, txt in matched_articles:
        with st.expander(f"📖 المادة {num}"):
            st.write(txt)
