<script setup>
import { ref, onMounted } from 'vue'
import { authApi, taskApi } from './services/taskService'

const tasks = ref([])
const newTaskTitle = ref('')
const newTaskDesc = ref('')
const username = ref('')
const password = ref('')
const isLoggedIn = ref(!!localStorage.getItem('token'))

const handleLogin = async () => {
  try {
    const res = await authApi.login({ username: username.value, password: password.value })
    localStorage.setItem('token', res.data.access_token || res.data.token)
    isLoggedIn.value = true
    fetchTasks()
  } catch (err) {
    alert('Login failed: ' + (err.response?.data?.detail || err.message))
  }
}

const fetchTasks = async () => {
  try {
    const res = await taskApi.getTasks()
    tasks.value = res.data
  } catch (err) {
    console.error('Failed to fetch tasks', err)
  }
}

const handleCreateTask = async () => {
  if (!newTaskTitle.value) return
  try {
    await taskApi.createTask({
      title: newTaskTitle.value,
      description: newTaskDesc.value,
    })
    newTaskTitle.value = ''
    newTaskDesc.value = ''
    fetchTasks()
  } catch (err) {
    alert('Error creating task')
  }
}

onMounted(() => {
  if (isLoggedIn.value) {
    fetchTasks()
  }
})
</script>

<template>
  <main style="padding: 2rem; font-family: sans-serif;">
    <h1>Task Management</h1>

    <!-- Login section if not logged in -->
    <div v-if="!isLoggedIn" style="margin-bottom: 2rem;">
      <h3>Login</h3>
      <input v-model="username" placeholder="Username" />
      <input v-model="password" type="password" placeholder="Password" />
      <button @click="handleLogin">Login</button>
    </div>

    <!-- Task list when logged in -->
    <div v-else>
      <h3>Create Task</h3>
      <input v-model="newTaskTitle" placeholder="Title" />
      <input v-model="newTaskDesc" placeholder="Description" />
      <button @click="handleCreateTask">Add Task</button>

      <h3>My Tasks</h3>
      <ul>
        <li v-for="task in tasks" :key="task.id">
          <strong>{{ task.title }}</strong>: {{ task.description }}
        </li>
      </ul>
    </div>
  </main>
</template>