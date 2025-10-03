import React, { createContext, useContext, useEffect, useState } from 'react'
import { io } from 'socket.io-client'
import { useAuth } from './AuthContext'
import Cookies from 'js-cookie'

const SocketContext = createContext()

export const useSocket = () => {
  const context = useContext(SocketContext)
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider')
  }
  return context
}

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    if (isAuthenticated) {
      const token = Cookies.get('token')
      const newSocket = io(import.meta.env.VITE_API_URL || 'http://localhost:8000', {
        auth: {
          token
        }
      })

      newSocket.on('connect', () => {
        console.log('Connected to server')
        setConnected(true)
      })

      newSocket.on('disconnect', () => {
        console.log('Disconnected from server')
        setConnected(false)
      })

      setSocket(newSocket)

      return () => {
        newSocket.close()
      }
    } else {
      if (socket) {
        socket.close()
        setSocket(null)
        setConnected(false)
      }
    }
  }, [isAuthenticated])

  const value = {
    socket,
    connected
  }

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  )
}