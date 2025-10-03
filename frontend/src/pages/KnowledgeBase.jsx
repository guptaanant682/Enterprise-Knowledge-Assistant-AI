import React, { useState, useEffect } from 'react'
import { Search, Upload, FileText, Download, Eye, Trash2, Filter } from 'lucide-react'
import axios from '../api/axios'
import toast from 'react-hot-toast'

const KnowledgeBase = () => {
  const [documents, setDocuments] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [activeTab, setActiveTab] = useState('browse')

  const categories = [
    { value: 'all', label: 'All Documents' },
    { value: 'policy', label: 'Policies' },
    { value: 'procedure', label: 'Procedures' },
    { value: 'manual', label: 'Manuals' },
    { value: 'guide', label: 'Guides' },
    { value: 'other', label: 'Other' }
  ]

  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await axios.get('/api/knowledge/documents')
      setDocuments(response.data)
    } catch (error) {
      console.error('Error fetching documents:', error)
      toast.error('Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files)
    if (files.length === 0) return

    setUploading(true)
    const formData = new FormData()
    
    files.forEach(file => {
      formData.append('files', file)
    })

    try {
      await axios.post('/api/knowledge/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      toast.success(`${files.length} file(s) uploaded successfully`)
      fetchDocuments()
      event.target.value = '' // Reset file input
    } catch (error) {
      console.error('Error uploading files:', error)
      toast.error('Failed to upload files')
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteDocument = async (documentId) => {
    if (!confirm('Are you sure you want to delete this document?')) return

    try {
      await axios.delete(`/api/knowledge/documents/${documentId}`)
      toast.success('Document deleted successfully')
      fetchDocuments()
    } catch (error) {
      console.error('Error deleting document:', error)
      toast.error('Failed to delete document')
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchDocuments()
      return
    }

    setLoading(true)
    try {
      const response = await axios.get(`/api/knowledge/search?q=${encodeURIComponent(searchQuery)}`)
      setDocuments(response.data)
    } catch (error) {
      console.error('Error searching documents:', error)
      toast.error('Search failed')
    } finally {
      setLoading(false)
    }
  }

  const filteredDocuments = documents.filter(doc => {
    if (selectedCategory === 'all') return true
    return doc.category === selectedCategory
  })

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Knowledge Base</h1>
        <p className="text-gray-600">
          Manage and explore your enterprise documentation
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('browse')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'browse'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Browse Documents
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'search'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Search
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'upload'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Upload
          </button>
        </nav>
      </div>

      {/* Content based on active tab */}
      {activeTab === 'search' && (
        <div className="mb-6">
          <div className="flex space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                <input
                  type="text"
                  placeholder="Search documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
            <button
              onClick={handleSearch}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Search
            </button>
          </div>
        </div>
      )}

      {activeTab === 'upload' && (
        <div className="mb-6">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Upload Documents</h3>
            <p className="text-gray-600 mb-4">
              Drag and drop files here, or click to select files
            </p>
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.md"
              onChange={handleFileUpload}
              className="hidden"
              id="file-upload"
              disabled={uploading}
            />
            <label
              htmlFor="file-upload"
              className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white ${
                uploading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-primary-600 hover:bg-primary-700 cursor-pointer'
              }`}
            >
              {uploading ? 'Uploading...' : 'Select Files'}
            </label>
            <p className="text-xs text-gray-500 mt-2">
              Supported formats: PDF, DOC, DOCX, TXT, MD
            </p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Filter className="h-5 w-5 text-gray-400" />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {categories.map(category => (
              <option key={category.value} value={category.value}>
                {category.label}
              </option>
            ))}
          </select>
        </div>
        <div className="text-sm text-gray-600">
          {filteredDocuments.length} document(s)
        </div>
      </div>

      {/* Documents Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
          <p className="text-gray-600">
            {searchQuery ? 'Try adjusting your search terms' : 'Upload your first document to get started'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDocuments.map(doc => (
            <div key={doc.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center">
                  <FileText className="h-8 w-8 text-primary-600 mr-3" />
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {doc.title}
                    </h3>
                    <p className="text-xs text-gray-500">{doc.category}</p>
                  </div>
                </div>
                <div className="flex space-x-1">
                  <button
                    onClick={() => window.open(doc.url, '_blank')}
                    className="p-1 text-gray-400 hover:text-gray-600"
                    title="View"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteDocument(doc.id)}
                    className="p-1 text-gray-400 hover:text-red-600"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              
              <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                {doc.summary || 'No summary available'}
              </p>
              
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{formatFileSize(doc.file_size)}</span>
                <span>{formatDate(doc.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default KnowledgeBase