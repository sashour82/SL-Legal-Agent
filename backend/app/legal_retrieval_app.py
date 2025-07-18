import os
import json
import openai
import faiss
import numpy as np
import streamlit as st
import sqlite3
from dotenv import load_dotenv
import re

# إعداد الصفحة
st.set_page_config(page_title="المستشار القانوني", layout="centered")

# تحميل مفتاح OpenAI من env
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# المسارات
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "..", "db", "laws.db")
INDEX_PATH = os.path.join(BASE_DIR, "..", "db", "faiss.index")

# تحميل المواد القانونية من القاعدة
@st.cache_resource
def load_articles():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT article_number, article_text FROM articles")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        st.error("⚠️ لا توجد مواد قانونية في قاعدة البيانات.")
        return [], []
    
    numbers, texts = zip(*rows)
    return numbers, texts

# تحميل أو بناء FAISS Index
@st.cache_resource
def build_index(texts):
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
    else:
        response = client.embeddings.create(model="text-embedding-3-large", input=list(texts))
        embeddings = np.array([d.embedding for d in response.data]).astype("float32")
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        faiss.write_index(index, INDEX_PATH)
    return index

# تحميل المواد والمؤشر
numbers, texts = load_articles()
index = build_index(texts)

# تهيئة سجل المحادثة
if "messages" not in st.session_state:
    st.session_state.messages = []

# التصنيفات (نية السؤال)
intent_labels = [
    "عقوبة", "شروط التطبيق", "إجراء قانوني", "الاختصاص", "استشارة عامة",
    "تعريف قانوني", "مدة زمنية", "مقارنة قانونية", "تفسير مادة"
]

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

# الواجهة
st.title("⚖️ المستشار القانوني الذكي")

# عرض الرسائل السابقة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# الإدخال
user_query = st.chat_input("📝 اطرح سؤالك القانوني:")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})

    # 1. تصنيف نية السؤال
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

    # 2. تحويل السؤال إلى embedding
    q_res = client.embeddings.create(model="text-embedding-3-large", input=[user_query])
    q_emb = np.array(q_res.data[0].embedding).astype("float32")

    # 3. البحث عن أقرب المواد
    D, I = index.search(np.array([q_emb]), k=10)

    # 4. استخراج كلمات مفتاحية من السؤال
    keywords = [word for word in re.findall(r'\b\w{4,}\b', user_query) if re.match(r'^[\u0600-\u06FF]+$', word)]

    # 5. حساب النقاط للمواد المسترجعة
    scored_matches = []
    for rank, idx in enumerate(I[0]):
        article_num = numbers[idx]
        article_text = texts[idx]

        # استرجاع intent من القاعدة
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT intent FROM articles WHERE article_number = ?", (article_num,))
        row = cursor.fetchone()
        article_intent = row[0] if row else None
        conn.close()

        # حساب التشابه الدلالي
        distance = D[0][rank]
        semantic_similarity = 1 / (1 + distance)

        # تقاطع الكلمات المفتاحية
        keyword_overlap = sum(1 for kw in keywords if kw in article_text) / (len(keywords) + 1e-5)

        # تعزيز إذا النية متطابقة
        boost = 0.15 if article_intent == detected_intent else 0.0

        # المجموع الكلي
        total_score = 0.6 * semantic_similarity + 0.25 * keyword_overlap + 0.15 * boost

        scored_matches.append((total_score, article_num, article_text))

    # 6. ترتيب وعرض أفضل النتائج
    scored_matches.sort(reverse=True)
    matched_articles = [(num, txt) for _, num, txt in scored_matches[:3]]

    # 7. بناء البرومبت النهائي
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

    # 8. توليد الإجابة النهائية
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "أنت مساعد قانوني ذكي تجيب بدقة على الأسئلة بالاستناد إلى مواد القانون فقط."},
            {"role": "user", "content": full_prompt}
        ],
    )
    answer = completion.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": answer})

    # عرض الرد
    with st.chat_message("assistant"):
        st.markdown(answer)

    # عرض المواد المرجعية
    st.divider()
    st.subheader("📚 المواد القانونية المرجعية:")
    for num, txt in matched_articles:
        with st.expander(f"📖 المادة {num}"):
            st.write(txt)
