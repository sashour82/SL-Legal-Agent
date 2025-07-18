<template>
  <div class="max-w-2xl mx-auto p-4">
    <h1 class="text-2xl font-bold mb-6 text-center">⚖️ المستشار القانوني الذكي</h1>

    <input
      v-model="question"
      type="text"
      placeholder="📝 اكتب سؤالك القانوني هنا..."
      class="w-full p-3 border border-gray-300 rounded mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
    />

    <button
      @click="sendQuestion"
      :disabled="loading || !question"
      class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
    >
      {{ loading ? "جاري المعالجة..." : "إرسال السؤال" }}
    </button>

    <div v-if="response" class="mt-6 bg-white p-4 rounded shadow-md">
      <h2 class="text-lg font-semibold mb-1">🔹 السؤال:</h2>
      <p class="mb-4">{{ response.question }}</p>

      <h2 class="text-lg font-semibold mb-1">🎯 نوع النية:</h2>
      <p class="mb-4 text-green-700 font-medium">{{ response.intent }}</p>

      <h2 class="text-lg font-semibold mb-1">🧾 الإجابة القانونية:</h2>
      <p class="mb-6 whitespace-pre-line">{{ response.answer }}</p>

      <h2 class="text-lg font-semibold mb-2">📚 المواد القانونية المرجعية:</h2>
      <div v-if="response.relevant_articles?.length > 0">
        <div
          v-for="(article, index) in response.relevant_articles"
          :key="index"
          class="mb-3"
        >
          <details class="bg-gray-100 p-3 rounded">
            <summary class="cursor-pointer font-semibold text-blue-700">
              📘 المادة {{ article.article_number }}
            </summary>
            <p class="mt-2 whitespace-pre-line text-gray-800">{{ article.text }}</p>
          </details>
        </div>
      </div>
      <p v-else class="text-gray-500">⚠️ لا توجد مواد قانونية مرجعية لهذا السؤال.</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const question = ref('')
const response = ref(null)
const loading = ref(false)

const sendQuestion = async () => {
  if (!question.value.trim()) return

  loading.value = true
  response.value = null

  try {
    const res = await axios.post('/api/legal', { question: question.value })
    response.value = res.data
  } catch (error) {
    console.error('❌ خطأ في الاتصال بالخادم:', error)
    alert("حدث خطأ أثناء الاتصال بالخادم. يرجى المحاولة لاحقًا.")
  } finally {
    loading.value = false
  }
}
</script>
