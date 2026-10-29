<script setup>
import { ref, computed, onMounted } from 'vue'
import { authApi, taskApi } from './services/taskService'

// State
const token = ref(localStorage.getItem('token') || '')
const currentUser = ref(null)
const tasks = ref([])
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// Auth form state
const authMode = ref('login') // 'login' | 'register'
const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ name: '', username: '', email: '', password: '' })
const authLoading = ref(false)

// Task filters & search
const searchQuery = ref('')
const activeFilter = ref('all') // 'all' | 'pending' | 'completed'

// Task creation & editing state
const showCreateForm = ref(false)
const newTask = ref({ title: '', description: '', is_completed: false })
const editingTaskId = ref(null)
const editForm = ref({ title: '', description: '', is_completed: false })

const isLoggedIn = computed(() => !!token.value)

const setFeedback = (error = '', success = '') => {
  errorMessage.value = error
  successMessage.value = success
  if (success) {
    setTimeout(() => {
      successMessage.value = ''
    }, 4000)
  }
}

// Authentication Actions
const handleLogin = async () => {
  setFeedback()
  if (!loginForm.value.username || !loginForm.value.password) {
    setFeedback('Username and password are required.')
    return
  }
  authLoading.value = true
  try {
    const res = await authApi.login({
      username: loginForm.value.username,
      password: loginForm.value.password,
    })
    const receivedToken = res.data.token || res.data.access_token
    token.value = receivedToken
    localStorage.setItem('token', receivedToken)
    loginForm.value = { username: '', password: '' }
    setFeedback('', 'Signed in successfully.')
  } catch (err) {
    const detail = err.response?.data?.detail
    const msg = Array.isArray(detail) ? detail.map((d) => d.msg).join(', ') : detail
    setFeedback(msg || 'Authentication failed. Please verify your credentials.')
    return
  } finally {
    authLoading.value = false
  }

  try {
    await checkCurrentUser()
    await fetchTasks()
  } catch (err) {
    console.error('Error loading user data or tasks:', err)
  }
}

const handleRegister = async () => {
  setFeedback()
  const { name, username, email, password } = registerForm.value
  if (!name || !username || !email || !password) {
    setFeedback('All registration fields are required.')
    return
  }
  authLoading.value = true
  try {
    await authApi.register({ name, username, email, password })
    setFeedback('', 'Account created successfully. Please sign in.')
    authMode.value = 'login'
    loginForm.value.username = username
    registerForm.value = { name: '', username: '', email: '', password: '' }
  } catch (err) {
    const detail = err.response?.data?.detail
    const msg = Array.isArray(detail) ? detail.map((d) => d.msg).join(', ') : detail
    setFeedback(msg || 'Registration failed. Username or email may already be registered.')
  } finally {
    authLoading.value = false
  }
}

const handleLogout = () => {
  token.value = ''
  currentUser.value = null
  tasks.value = []
  localStorage.removeItem('token')
  setFeedback('', 'Signed out.')
}

const checkCurrentUser = async () => {
  if (!token.value) return
  try {
    const res = await authApi.checkAuth()
    currentUser.value = res.data
  } catch (err) {
    if (err.response?.status === 401) {
      handleLogout()
    }
  }
}

// Task Management Actions
const fetchTasks = async () => {
  if (!token.value) return
  isLoading.value = true
  try {
    const res = await taskApi.getTasks()
    tasks.value = res.data || []
  } catch (err) {
    setFeedback('Unable to retrieve tasks from the server.')
  } finally {
    isLoading.value = false
  }
}

const handleCreateTask = async () => {
  setFeedback()
  if (!newTask.value.title.trim() || !newTask.value.description.trim()) {
    setFeedback('Task title and description are both required.')
    return
  }
  try {
    await taskApi.createTask({
      title: newTask.value.title.trim(),
      description: newTask.value.description.trim(),
      is_completed: newTask.value.is_completed,
    })
    newTask.value = { title: '', description: '', is_completed: false }
    showCreateForm.value = false
    await fetchTasks()
    setFeedback('', 'Task created.')
  } catch (err) {
    const detail = err.response?.data?.detail
    const msg = Array.isArray(detail) ? detail.map((d) => d.msg).join(', ') : detail
    setFeedback(msg || 'Failed to create task.')
  }
}

const handleToggleStatus = async (task) => {
  try {
    await taskApi.updateTask(task.id, {
      title: task.title,
      description: task.description,
      is_completed: !task.is_completed,
    })
    await fetchTasks()
  } catch (err) {
    setFeedback('Failed to update task status.')
  }
}

const startEditTask = (task) => {
  editingTaskId.value = task.id
  editForm.value = {
    title: task.title,
    description: task.description,
    is_completed: task.is_completed,
  }
}

const cancelEdit = () => {
  editingTaskId.value = null
  editForm.value = { title: '', description: '', is_completed: false }
}

const handleUpdateTask = async (id) => {
  setFeedback()
  if (!editForm.value.title.trim() || !editForm.value.description.trim()) {
    setFeedback('Title and description cannot be empty.')
    return
  }
  try {
    await taskApi.updateTask(id, {
      title: editForm.value.title.trim(),
      description: editForm.value.description.trim(),
      is_completed: editForm.value.is_completed,
    })
    editingTaskId.value = null
    await fetchTasks()
    setFeedback('', 'Task updated.')
  } catch (err) {
    setFeedback('Failed to save task updates.')
  }
}

const handleDeleteTask = async (task) => {
  if (!confirm(`Are you sure you want to delete task #${task.id}: "${task.title}"?`)) {
    return
  }
  try {
    await taskApi.deleteTask(task.id)
    await fetchTasks()
    setFeedback('', `Task #${task.id} deleted.`)
  } catch (err) {
    setFeedback('Failed to delete task.')
  }
}

// Metrics & Filtering
const taskCounts = computed(() => {
  const total = tasks.value.length
  const completed = tasks.value.filter((t) => t.is_completed).length
  const pending = total - completed
  return { total, completed, pending }
})

const filteredTasks = computed(() => {
  return tasks.value.filter((task) => {
    // Status filter
    if (activeFilter.value === 'pending' && task.is_completed) return false
    if (activeFilter.value === 'completed' && !task.is_completed) return false

    // Search query filter
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase()
      const titleMatch = task.title.toLowerCase().includes(q)
      const descMatch = (task.description || '').toLowerCase().includes(q)
      const idMatch = String(task.id).includes(q)
      return titleMatch || descMatch || idMatch
    }
    return true
  })
})

onMounted(async () => {
  if (isLoggedIn.value) {
    await checkCurrentUser()
    await fetchTasks()
  }
})
</script>

<template>
  <div class="app-layout">
    <!-- Top System Header -->
    <header class="app-header">
      <div class="header-container">
        <div class="header-left">
          <span class="header-title">Task Management System</span>
        </div>
        <div class="header-right">
          <template v-if="isLoggedIn">
            <span class="user-label">
              User: <strong>{{ currentUser?.username || 'Authenticated' }}</strong>
              <span v-if="currentUser?.email" class="user-email mono">[{{ currentUser.email }}]</span>
            </span>
            <button class="btn btn-secondary btn-sm" @click="handleLogout">Sign Out</button>
          </template>
          <template v-else>
            <span class="user-label">Session: Unauthenticated</span>
          </template>
        </div>
      </div>
    </header>

    <!-- Main Workspace Content -->
    <main class="main-content">
      <!-- Global Alerts -->
      <div v-if="errorMessage" class="alert alert-danger" role="alert">
        {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="alert alert-success" role="status">
        {{ successMessage }}
      </div>

      <!-- UNAUTHENTICATED STATE -->
      <section v-if="!isLoggedIn" class="auth-section">
        <div class="auth-panel">
          <div class="auth-tabs">
            <button
              class="auth-tab"
              :class="{ 'auth-tab-active': authMode === 'login' }"
              @click="authMode = 'login'"
            >
              Sign In
            </button>
            <button
              class="auth-tab"
              :class="{ 'auth-tab-active': authMode === 'register' }"
              @click="authMode = 'register'"
            >
              Register Account
            </button>
          </div>

          <!-- Login Form -->
          <form v-if="authMode === 'login'" class="auth-form" @submit.prevent="handleLogin">
            <div class="form-group">
              <label for="login-username">Username or Email</label>
              <input
                id="login-username"
                v-model="loginForm.username"
                type="text"
                autocomplete="username"
                required
                placeholder="Enter username or email"
              />
            </div>
            <div class="form-group">
              <label for="login-password">Password</label>
              <input
                id="login-password"
                v-model="loginForm.password"
                type="password"
                autocomplete="current-password"
                required
                placeholder="Enter password"
              />
            </div>
            <div class="form-actions">
              <button class="btn btn-primary btn-block" type="submit" :disabled="authLoading">
                {{ authLoading ? 'Authenticating...' : 'Sign In' }}
              </button>
            </div>
          </form>

          <!-- Register Form -->
          <form v-else class="auth-form" @submit.prevent="handleRegister">
            <div class="form-group">
              <label for="reg-name">Full Name</label>
              <input
                id="reg-name"
                v-model="registerForm.name"
                type="text"
                required
                placeholder="Full name"
              />
            </div>
            <div class="form-group">
              <label for="reg-username">Username</label>
              <input
                id="reg-username"
                v-model="registerForm.username"
                type="text"
                autocomplete="username"
                required
                placeholder="Choose username"
              />
            </div>
            <div class="form-group">
              <label for="reg-email">Email Address</label>
              <input
                id="reg-email"
                v-model="registerForm.email"
                type="email"
                autocomplete="email"
                required
                placeholder="user@example.com"
              />
            </div>
            <div class="form-group">
              <label for="reg-password">Password</label>
              <input
                id="reg-password"
                v-model="registerForm.password"
                type="password"
                autocomplete="new-password"
                required
                placeholder="Set password"
              />
            </div>
            <div class="form-actions">
              <button class="btn btn-primary btn-block" type="submit" :disabled="authLoading">
                {{ authLoading ? 'Creating Account...' : 'Register' }}
              </button>
            </div>
          </form>
        </div>
      </section>

      <!-- AUTHENTICATED STATE -->
      <section v-else class="dashboard-section">
        <!-- Metric Statistics Bar -->
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-label">Total Records</span>
            <span class="stat-value mono">{{ taskCounts.total }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">Pending</span>
            <span class="stat-value mono">{{ taskCounts.pending }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">Completed</span>
            <span class="stat-value mono">{{ taskCounts.completed }}</span>
          </div>
        </div>

        <!-- Controls & Filters Toolbar -->
        <div class="toolbar">
          <div class="toolbar-left">
            <button
              class="btn btn-primary"
              @click="showCreateForm = !showCreateForm"
            >
              {{ showCreateForm ? 'Close Entry Form' : 'New Task Entry' }}
            </button>
            <div class="filter-group">
              <button
                class="filter-btn"
                :class="{ 'filter-btn-active': activeFilter === 'all' }"
                @click="activeFilter = 'all'"
              >
                All ({{ taskCounts.total }})
              </button>
              <button
                class="filter-btn"
                :class="{ 'filter-btn-active': activeFilter === 'pending' }"
                @click="activeFilter = 'pending'"
              >
                Pending ({{ taskCounts.pending }})
              </button>
              <button
                class="filter-btn"
                :class="{ 'filter-btn-active': activeFilter === 'completed' }"
                @click="activeFilter = 'completed'"
              >
                Completed ({{ taskCounts.completed }})
              </button>
            </div>
          </div>

          <div class="toolbar-right">
            <input
              v-model="searchQuery"
              type="text"
              class="search-input"
              placeholder="Search by ID, title, description..."
            />
          </div>
        </div>

        <!-- Creation Form Panel -->
        <div v-if="showCreateForm" class="panel create-panel">
          <div class="panel-header">
            <span class="panel-title">New Task Entry</span>
          </div>
          <form class="panel-body" @submit.prevent="handleCreateTask">
            <div class="form-row">
              <div class="form-group flex-2">
                <label for="task-title">Title *</label>
                <input
                  id="task-title"
                  v-model="newTask.title"
                  type="text"
                  required
                  placeholder="Task title"
                />
              </div>
              <div class="form-group flex-1 checkbox-group">
                <label>Initial Status</label>
                <label class="checkbox-label">
                  <input v-model="newTask.is_completed" type="checkbox" />
                  <span>Mark as Completed</span>
                </label>
              </div>
            </div>
            <div class="form-group">
              <label for="task-desc">Description *</label>
              <textarea
                id="task-desc"
                v-model="newTask.description"
                rows="3"
                required
                placeholder="Detailed specifications or instructions"
              ></textarea>
            </div>
            <div class="form-actions-inline">
              <button class="btn btn-primary" type="submit">Save Task</button>
              <button class="btn btn-secondary" type="button" @click="showCreateForm = false">
                Cancel
              </button>
            </div>
          </form>
        </div>

        <!-- Tasks Ledger Table -->
        <div class="ledger-container">
          <table class="ledger-table">
            <thead>
              <tr>
                <th style="width: 110px;">Status</th>
                <th style="width: 65px;" class="mono">ID</th>
                <th>Task Details</th>
                <th style="width: 250px; text-align: right;">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isLoading">
                <td colspan="4" class="table-empty">Loading records...</td>
              </tr>
              <tr v-else-if="filteredTasks.length === 0">
                <td colspan="4" class="table-empty">
                  {{ tasks.length === 0 ? 'No tasks registered in database.' : 'No records match search and filter criteria.' }}
                </td>
              </tr>
              <template v-else>
                <tr
                  v-for="task in filteredTasks"
                  :key="task.id"
                  :class="{ 'row-completed': task.is_completed }"
                >
                  <!-- Status Column -->
                  <td>
                    <span
                      class="badge"
                      :class="task.is_completed ? 'badge-completed' : 'badge-pending'"
                    >
                      {{ task.is_completed ? 'Completed' : 'Pending' }}
                    </span>
                  </td>

                  <!-- ID Column -->
                  <td class="mono task-id">
                    #{{ task.id }}
                  </td>

                  <!-- Task Details / Edit Row -->
                  <td>
                    <!-- In-place Edit Form -->
                    <div v-if="editingTaskId === task.id" class="inline-edit-box">
                      <div class="form-group">
                        <label>Title</label>
                        <input v-model="editForm.title" type="text" required />
                      </div>
                      <div class="form-group">
                        <label>Description</label>
                        <textarea v-model="editForm.description" rows="2" required></textarea>
                      </div>
                      <div class="form-group">
                        <label class="checkbox-label">
                          <input v-model="editForm.is_completed" type="checkbox" />
                          <span>Status: Completed</span>
                        </label>
                      </div>
                      <div class="inline-actions">
                        <button class="btn btn-primary btn-sm" @click="handleUpdateTask(task.id)">
                          Save
                        </button>
                        <button class="btn btn-secondary btn-sm" @click="cancelEdit">
                          Cancel
                        </button>
                      </div>
                    </div>

                    <!-- Regular View -->
                    <div v-else class="task-info">
                      <div class="task-title" :class="{ 'text-strikethrough': task.is_completed }">
                        {{ task.title }}
                      </div>
                      <div class="task-desc">
                        {{ task.description }}
                      </div>
                    </div>
                  </td>

                  <!-- Actions Column -->
                  <td class="actions-cell">
                    <div v-if="editingTaskId !== task.id" class="action-buttons">
                      <button
                        class="btn btn-secondary btn-sm"
                        @click="handleToggleStatus(task)"
                      >
                        {{ task.is_completed ? 'Mark Pending' : 'Mark Complete' }}
                      </button>
                      <button
                        class="btn btn-secondary btn-sm"
                        @click="startEditTask(task)"
                      >
                        Edit
                      </button>
                      <button
                        class="btn btn-danger btn-sm"
                        @click="handleDeleteTask(task)"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.app-header {
  background-color: #ffffff;
  border-bottom: 1px solid var(--border-light);
  padding: 0 16px;
}

.header-container {
  max-width: 1080px;
  margin: 0 auto;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--text-main);
}

.header-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 5px;
  background-color: var(--bg-subtle);
  border: 1px solid var(--border-medium);
  border-radius: 3px;
  color: var(--text-muted);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-label {
  font-size: 13px;
  color: var(--text-muted);
}

.user-email {
  color: var(--text-subtle);
  margin-left: 4px;
  font-size: 12px;
}

/* Main Content */
.main-content {
  max-width: 1080px;
  width: 100%;
  margin: 0 auto;
  padding: 24px 16px 48px;
  flex: 1;
}

/* Auth Section */
.auth-section {
  display: flex;
  justify-content: center;
  padding-top: 40px;
}

.auth-panel {
  width: 100%;
  max-width: 400px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 4px;
}

.auth-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-light);
  background-color: var(--bg-subtle);
}

.auth-tab {
  flex: 1;
  padding: 11px;
  font-size: 13px;
  font-weight: 500;
  text-align: center;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--text-muted);
  border-bottom: 2px solid transparent;
}

.auth-tab-active {
  background-color: var(--bg-surface);
  color: var(--text-main);
  font-weight: 600;
  border-bottom: 2px solid var(--color-primary);
}

.auth-form {
  padding: 20px;
}

.form-group {
  margin-bottom: 14px;
}

.form-actions {
  margin-top: 18px;
}

.btn-block {
  width: 100%;
}

/* Dashboard & Stats */
.dashboard-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 4px;
  padding: 12px 16px;
}

.stat-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-main);
  line-height: 1.2;
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 4px;
  padding: 10px 14px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-group {
  display: inline-flex;
  border: 1px solid var(--border-medium);
  border-radius: 4px;
  overflow: hidden;
}

.filter-btn {
  padding: 6px 11px;
  font-size: 12px;
  border: none;
  background-color: var(--bg-surface);
  color: var(--text-muted);
  cursor: pointer;
  border-right: 1px solid var(--border-medium);
}

.filter-btn:last-child {
  border-right: none;
}

.filter-btn-active {
  background-color: var(--color-primary);
  color: var(--text-inverse);
  font-weight: 500;
}

.toolbar-right {
  min-width: 280px;
}

.search-input {
  width: 100%;
}

/* Panel */
.panel {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 4px;
}

.panel-header {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-light);
  background-color: var(--bg-subtle);
}

.panel-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
}

.panel-body {
  padding: 14px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.flex-1 { flex: 1; }
.flex-2 { flex: 2; }

.checkbox-group {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding-bottom: 6px;
}

.checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 400;
  color: var(--text-main);
  text-transform: none;
  letter-spacing: normal;
  margin: 0;
  cursor: pointer;
}

.form-actions-inline {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

/* Table Ledger */
.ledger-container {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 4px;
  overflow-x: auto;
}

.ledger-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.ledger-table th {
  padding: 10px 14px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-subtle);
  background-color: var(--bg-subtle);
  border-bottom: 1px solid var(--border-light);
}

.ledger-table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-light);
  vertical-align: top;
}

.ledger-table tr:last-child td {
  border-bottom: none;
}

.row-completed td {
  background-color: #fafbfc;
}

.task-id {
  color: var(--text-subtle);
  font-size: 12px;
  padding-top: 14px;
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.task-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
}

.text-strikethrough {
  text-decoration: line-through;
  color: var(--text-subtle);
}

.task-desc {
  font-size: 13px;
  color: var(--text-muted);
  white-space: pre-wrap;
  word-break: break-word;
}

.actions-cell {
  text-align: right;
}

.action-buttons {
  display: inline-flex;
  gap: 6px;
  justify-content: flex-end;
}

.table-empty {
  text-align: center;
  padding: 36px 16px;
  color: var(--text-subtle);
  font-style: italic;
}

/* Inline Edit Box */
.inline-edit-box {
  background-color: var(--bg-subtle);
  border: 1px solid var(--border-medium);
  border-radius: 4px;
  padding: 12px;
}

.inline-actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}

/* Responsiveness */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .toolbar-left {
    flex-direction: column;
    align-items: stretch;
  }
  .form-row {
    flex-direction: column;
  }
  .actions-cell {
    text-align: left;
  }
  .action-buttons {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>