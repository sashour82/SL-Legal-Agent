import requests

# إعداد عنوان السيرفر
BASE_URL = "http://127.0.0.1:5000/api/legal"

# السؤال المراد اختباره
payload = {
    "question": "تقييم الاداء"
}

# إرسال الطلب
response = requests.post(BASE_URL, json=payload)

# طباعة النتائج
if response.status_code == 200:
    data = response.json()
    print("\n✅ تم الاتصال بنجاح")
    print("🔹 السؤال:", data["question"])
    print("🔹 نوع النية:", data["intent"])
    print("🔹 الإجابة:\n", data["answer"])
    print("🔹 المواد المرجعية:")
    for ref in data["references"]:
        print(f"   📘 المادة {ref['number']}: {ref['text'][:60]}...")
else:
    print("\n❌ حدث خطأ")
    print("Status Code:", response.status_code)
    print("Response:", response.text)
