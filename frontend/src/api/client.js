import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  paramsSerializer: {
    serialize: (params) => {
      const searchParams = new URLSearchParams()
      for (const [key, value] of Object.entries(params)) {
        if (Array.isArray(value)) {
          // FastAPI expects repeated keys for list params: key=val1&key=val2
          value.forEach(v => searchParams.append(key, v))
        } else if (value !== undefined && value !== null) {
          searchParams.append(key, value)
        }
      }
      return searchParams.toString()
    }
  }
})

api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api
