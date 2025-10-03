import React, { useState, useEffect, useRef } from 'react'
import { useSocket } from '../contexts/SocketContext'
import { useAuth } from '../contexts/AuthContext'
import { Send, Loader2, User, Bot, FileText, Clock } from 'lucide-react'
import axios from '../api/axios'
import toast from 'react-hot-toast'

const Chat = () => {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const { socket, connected } = useSocket()
  const { user } = useAuth()

  useEffect(() => {
    fetchChatHistory()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (socket) {
      socket.on('response', handleResponse)
      socket.on('typing', handleTyping)
      socket.on('stop_typing', handleStopTyping)

      return () => {
        socket.off('response', handleResponse)
        socket.off('typing', handleTyping)
        socket.off('stop_typing', handleStopTyping)
      }
    }
  }, [socket])

  const fetchChatHistory = async () => {
    try {
      const response = await axios.get('/api/chat/history')
      setMessages(response.data)
    } catch (error) {
      console.error('Error fetching chat history:', error)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleResponse = (data) => {
    setMessages(prev => [...prev, data])
    setIsTyping(false)
    setLoading(false)
  }

  const handleTyping = () => {
    setIsTyping(true)
  }

  const handleStopTyping = () => {
    setIsTyping(false)
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || loading) return

    const userMessage = {
      id: Date.now(),
      message: inputMessage,
      sender: 'user',
      timestamp: new Date().toISOString(),
      user_name: user?.name
    }

    setMessages(prev => [...prev, userMessage])
    setLoading(true)
    setInputMessage('')

    try {
      if (socket && connected) {
        // Send via WebSocket for real-time response
        socket.emit('message', { message: inputMessage })
      } else {
        // Fallback to HTTP request
        const response = await axios.post('/api/chat/message', {
          message: inputMessage
        })
        handleResponse(response.data)
      }
    } catch (error) {
      console.error('Error sending message:', error)
      toast.error('Failed to send message')
      setLoading(false)
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return ''

    try {
      const date = new Date(timestamp)
      if (isNaN(date.getTime())) return ''

      return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch (error) {
      console.error('Error formatting timestamp:', error)
      return ''
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Knowledge Assistant</h1>
            <p className="text-sm text-gray-600">
              Ask me anything about your enterprise knowledge base
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="h-16 w-16 text-primary-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Welcome to Enterprise Knowledge Assistant
              </h3>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                I'm here to help you find information from your enterprise knowledge base. 
                Ask me questions about policies, procedures, or any documentation.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                <div className="p-4 bg-white rounded-lg border border-gray-200">
                  <FileText className="h-6 w-6 text-primary-600 mb-2" />
                  <p className="text-sm font-medium text-gray-900">Company Policies</p>
                  <p className="text-xs text-gray-600">Ask about HR policies, compliance procedures</p>
                </div>
                <div className="p-4 bg-white rounded-lg border border-gray-200">
                  <Clock className="h-6 w-6 text-primary-600 mb-2" />
                  <p className="text-sm font-medium text-gray-900">Quick Answers</p>
                  <p className="text-xs text-gray-600">Get instant responses to common questions</p>
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex max-w-3xl ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`flex-shrink-0 ${message.sender === 'user' ? 'ml-3' : 'mr-3'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        message.sender === 'user' ? 'bg-primary-600' : 'bg-gray-600'
                      }`}>
                        {message.sender === 'user' ? (
                          <User className="w-4 h-4 text-white" />
                        ) : (
                          <Bot className="w-4 h-4 text-white" />
                        )}
                      </div>
                    </div>
                    <div className={`flex flex-col ${message.sender === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className={`chat-message ${message.sender}`}>
                        <p className="text-sm whitespace-pre-wrap">{message.message}</p>
                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-xs font-medium text-gray-600 mb-2">Sources:</p>
                            <div className="space-y-1">
                              {message.sources.map((source, index) => (
                                <div key={index} className="text-xs text-gray-500 flex items-center">
                                  <FileText className="w-3 h-3 mr-1" />
                                  <span>{source.title}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center mt-1 space-x-2 text-xs text-gray-500">
                        {message.sender === 'user' && (
                          <span>{message.user_name || user?.name}</span>
                        )}
                        <span>{formatTimestamp(message.timestamp)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {isTyping && (
                <div className="flex justify-start">
                  <div className="flex mr-3">
                    <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  </div>
                  <div className="bg-gray-100 text-gray-800 p-3 rounded-lg">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Form */}
      <div className="bg-white border-t border-gray-200 p-6">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={sendMessage} className="flex space-x-4">
            <div className="flex-1 relative">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask me anything about your enterprise knowledge base..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent pr-12"
                disabled={loading}
              />
              {loading && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
                </div>
              )}
            </div>
            <button
              type="submit"
              disabled={!inputMessage.trim() || loading}
              className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Enterprise Knowledge Assistant can make mistakes. Please verify important information.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Chat