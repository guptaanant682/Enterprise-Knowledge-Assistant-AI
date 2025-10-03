import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  MessageCircle,
  Database,
  Users,
  TrendingUp,
  Clock,
  FileText,
  Search,
  ArrowRight
} from 'lucide-react'
import axios from '../api/axios'

const Dashboard = () => {
  const { user } = useAuth()
  const [stats, setStats] = useState({
    totalQueries: 0,
    documentsCount: 0,
    activeUsers: 0,
    avgResponseTime: 0
  })
  const [recentQueries, setRecentQueries] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [statsResponse, queriesResponse] = await Promise.all([
        axios.get('/api/dashboard/stats'),
        axios.get('/api/dashboard/recent-queries')
      ])
      
      setStats(statsResponse.data)
      setRecentQueries(queriesResponse.data)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const quickActions = [
    {
      title: 'Ask a Question',
      description: 'Get instant answers from our knowledge base',
      icon: MessageCircle,
      link: '/chat',
      color: 'bg-blue-500'
    },
    {
      title: 'Browse Knowledge Base',
      description: 'Explore our comprehensive documentation',
      icon: Database,
      link: '/knowledge',
      color: 'bg-green-500'
    },
    {
      title: 'Search Documents',
      description: 'Find specific information quickly',
      icon: Search,
      link: '/knowledge?tab=search',
      color: 'bg-purple-500'
    }
  ]

  if (user?.role === 'admin') {
    quickActions.push({
      title: 'Admin Panel',
      description: 'Manage users and knowledge base',
      icon: Users,
      link: '/admin',
      color: 'bg-red-500'
    })
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back, {user?.name}!
        </h1>
        <p className="text-gray-600">
          Here's what's happening with your knowledge assistant today.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100">
              <MessageCircle className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Queries</p>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? '...' : stats.totalQueries}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100">
              <FileText className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Documents</p>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? '...' : stats.documentsCount}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100">
              <Users className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Users</p>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? '...' : stats.activeUsers}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-orange-100">
              <Clock className="h-6 w-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Avg Response</p>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? '...' : `${stats.avgResponseTime}s`}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {quickActions.map((action, index) => {
                const Icon = action.icon
                return (
                  <Link
                    key={index}
                    to={action.link}
                    className="flex items-center p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all duration-200 group"
                  >
                    <div className={`p-3 rounded-lg ${action.color}`}>
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <div className="ml-4 flex-1">
                      <h3 className="text-sm font-medium text-gray-900 group-hover:text-primary-600">
                        {action.title}
                      </h3>
                      <p className="text-sm text-gray-600">{action.description}</p>
                    </div>
                    <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-primary-600" />
                  </Link>
                )
              })}
            </div>
          </div>
        </div>

        {/* Recent Queries */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Queries</h2>
          </div>
          <div className="p-6">
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : recentQueries.length === 0 ? (
              <div className="text-center py-8">
                <MessageCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No recent queries</p>
                <Link to="/chat" className="text-primary-600 hover:text-primary-700 text-sm">
                  Start asking questions →
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {recentQueries.map((query, index) => (
                  <div key={index} className="border-l-4 border-primary-200 pl-4">
                    <p className="text-sm font-medium text-gray-900 mb-1">
                      {query.question}
                    </p>
                    <div className="flex items-center text-xs text-gray-500">
                      <span>{query.user_name}</span>
                      <span className="mx-2">•</span>
                      <span>{new Date(query.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Getting Started Section */}
      <div className="mt-8 bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg p-6">
        <div className="flex items-center">
          <TrendingUp className="h-8 w-8 text-primary-600 mr-4" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Getting Started with Enterprise Knowledge Assistant
            </h3>
            <p className="text-gray-600 mb-4">
              Maximize your productivity with our AI-powered knowledge assistant. 
              Ask questions in natural language and get instant, accurate answers from your enterprise knowledge base.
            </p>
            <Link 
              to="/chat" 
              className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Start Chatting
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard