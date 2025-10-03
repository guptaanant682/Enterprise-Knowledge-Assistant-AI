import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from '../api/axios'
import Cookies from 'js-cookie'
import toast from 'react-hot-toast'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  // Set up axios defaults
  useEffect(() => {
    const token = Cookies.get('token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      verifyToken()
    } else {
      setLoading(false)
    }
  }, [])

  const verifyToken = async () => {
    try {
      const response = await axios.get('/api/auth/me')
      setUser(response.data)
      setIsAuthenticated(true)
    } catch (error) {
      console.error('Token verification failed:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      const response = await axios.post('/api/auth/login', {
        email,
        password
      })
      
      const { access_token, user: userData } = response.data
      
      // Set token in cookie and axios headers
      Cookies.set('token', access_token, { expires: 7 })
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      setUser(userData)
      setIsAuthenticated(true)
      
      toast.success('Login successful!')
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed'
      toast.error(message)
      return { success: false, error: message }
    }
  }

  const loginWithGoogle = async (credential) => {
    try {
      const response = await axios.post('/api/auth/google', {
        credential
      })
      
      const { access_token, user: userData } = response.data
      
      Cookies.set('token', access_token, { expires: 7 })
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      setUser(userData)
      setIsAuthenticated(true)
      
      toast.success('Google login successful!')
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Google login failed'
      toast.error(message)
      return { success: false, error: message }
    }
  }

  const register = async (userData) => {
    try {
      const response = await axios.post('/api/auth/register', userData)
      toast.success('Registration successful! Please login.')
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed'
      toast.error(message)
      return { success: false, error: message }
    }
  }

  const logout = () => {
    Cookies.remove('token')
    delete axios.defaults.headers.common['Authorization']
    setUser(null)
    setIsAuthenticated(false)
    toast.success('Logged out successfully')
  }

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    loginWithGoogle,
    register,
    logout
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}