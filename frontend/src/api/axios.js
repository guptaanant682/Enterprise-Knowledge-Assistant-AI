import axios from 'axios'

// Configure axios defaults
const instance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
instance.interceptors.request.use(
  (config) => {
    // Log request for debugging
    console.log('API Request:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
instance.interceptors.response.use(
  (response) => {
    // Log response for debugging
    console.log('API Response:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('Response error:', error.response?.status, error.config?.url, error.response?.data)

    // Handle specific error cases
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      console.warn('Unauthorized access, redirecting to login')
      // Don't redirect here, let the component handle it
    }

    return Promise.reject(error)
  }
)

// Configure global axios defaults
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
axios.defaults.timeout = 30000

export default instance
