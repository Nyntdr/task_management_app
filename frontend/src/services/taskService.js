import api from './api'

export const authApi = {
  login: (credentials) => api.post('/users/login', credentials),
  register: (userData) => api.post('/users/register', userData),
  checkAuth: () => api.get('/users/is_auth'),
}

export const taskApi = {
  getTasks: () => api.get('/tasks/all'),
  createTask: (task) => api.post('/tasks/create', task),
  updateTask: (id, task) => api.put(`/tasks/update/${id}`, task),
  deleteTask: (id) => api.delete(`/tasks/delete/${id}`),
}