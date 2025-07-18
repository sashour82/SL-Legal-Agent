<script setup>
import { ref, onMounted } from 'vue'

const message = ref('Loading...')

onMounted(() => {
  fetch('/api/')
    .then(res => res.json())
    .then(data => {
      message.value = data.message
    })
    .catch(err => {
      console.error('❌ Server connection failed:', err)
      message.value = 'Failed to connect to server'
    })
})
</script>

<template>
  <main style="padding: 2rem; font-size: 1.5rem;">
    <p>{{ message }}</p>
  </main>
</template>
