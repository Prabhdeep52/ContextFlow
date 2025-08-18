"use client"
import 'katex/dist/katex.min.css';
import type React from "react"
import { useState, useEffect } from "react"
import axios from "axios"
import { Upload, FileText, MessageSquare, Key, Send, Loader2, AlertCircle, Clock, DollarSign, Hash } from "lucide-react"
import { Button } from "./components/ui/button"
import { Input } from "./components/ui/input"
import { Textarea } from "./components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card"
import { Badge } from "./components/ui/badge"
import { Progress } from "./components/ui/progress"
import { Alert, AlertDescription } from "./components/ui/alert"
import ReactMarkdown, {} from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'

interface Document {
  filename: string
  chunk_count: number
  upload_date: string
}

interface ChatEntry {
  question: string
  answer: string
  sources?: string[]
  timestamp: string
  total_tokens?: number
  cost?: number
}

export default function RAGQASystem() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [question, setQuestion] = useState("")
  const [chatHistory, setChatHistory] = useState<ChatEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [apiKey, setApiKey] = useState("")
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false)
  const [documents, setDocuments] = useState<Document[]>([])
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})
  const [dragActive, setDragActive] = useState(false)

  const API_BASE_URL = "http://localhost:8000"

  useEffect(() => {
    // Check API key status on component mount
    const checkApiKeyStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api_key_status`)
        setApiKeyConfigured(response.data.configured)
        if (response.data.configured) {
          // If already configured, fetch data
          fetchChatHistory()
          fetchDocuments()
        }
      } catch (error) {
        console.error("Error checking API key status:", error)
      }
    }
    checkApiKeyStatus()
  }, [])

  const fetchChatHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/history`)
      const conversations = response.data?.conversations || []
      setChatHistory(conversations)
    } catch (error) {
      console.error("Error fetching chat history:", error)
      setChatHistory([])
    }
  }

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents`)
      const docs = response.data?.documents || []
      setDocuments(docs)
    } catch (error) {
      console.error("Error fetching documents:", error)
      setDocuments([])
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    const files = Array.from(e.dataTransfer.files).filter((file) => file.type === "application/pdf")
    setSelectedFiles(files)
    const progress: Record<string, number> = {}
    files.forEach((file) => {
      progress[file.name] = 0
    })
    setUploadProgress(progress)
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    setSelectedFiles(files)
    const progress: Record<string, number> = {}
    files.forEach((file) => {
      progress[file.name] = 0
    })
    setUploadProgress(progress)
  }

  const handleFileUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      alert("Please select PDF files to upload.")
      return
    }
    setLoading(true)
    const formData = new FormData()
    selectedFiles.forEach((file) => {
      formData.append("files", file)
    })
    try {
      await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const progress: Record<string, number> = {}
          selectedFiles.forEach((file) => {
            progress[file.name] = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1))
          })
          setUploadProgress(progress)
        },
      })
      setSelectedFiles([])
      setUploadProgress({})
      fetchDocuments()
    } catch (error) {
      console.error("Error uploading files:", error)
      alert("Error uploading files. See console for details.")
    } finally {
      setLoading(false)
    }
  }

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      alert("Please enter a question.")
      return
    }
    setLoading(true)
    try {
      await axios.post(`${API_BASE_URL}/ask`, {
        question: question,
        top_k: 4,
        include_context: false,
        context_length: 3,
      })
      await fetchChatHistory()
      setQuestion("")
    } catch (error) {
      console.error("Error asking question:", error)
      alert("Error asking question. See console for details.")
    } finally {
      setLoading(false)
    }
  }

  const handleConfigureApiKey = async () => {
    if (!apiKey.trim()) {
      alert("Please enter your Google API Key.")
      return
    }
    setLoading(true)
    try {
      await axios.post(`${API_BASE_URL}/configure_api_key`, { api_key: apiKey })
      setApiKeyConfigured(true)
      fetchChatHistory()
      fetchDocuments()
    } catch (error) {
      console.error("Error configuring API key:", error)
      alert("Error configuring API key. See console for details.")
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const formatTimestamp = (timestamp: string) => {
    if (!timestamp) return "Unknown"
    return new Date(timestamp).toLocaleString()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">RAG-based Research Paper Q&A</h1>
            <p className="text-lg text-gray-600">Upload multiple PDFs and ask questions with context tracking</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!apiKeyConfigured ? (
          <div className="flex justify-center">
            <div className="w-full max-w-md">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 justify-center">
                    <Key className="h-5 w-5" /> API Configuration
                  </CardTitle>
                  <CardDescription className="text-center">
                    Configure your Google API key to get started
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input
                    type="password"
                    placeholder="Enter your Google API Key"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    disabled={loading}
                  />
                  <Button onClick={handleConfigureApiKey} disabled={loading || !apiKey.trim()} className="w-full">
                    {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Configure API Key"}
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <div className="flex gap-6 h-[calc(100vh-200px)]">
            <div className="w-80 flex flex-col gap-4">
              {/* File Upload Section */}
              <Card className="flex-shrink-0">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="h-5 w-5" /> Upload Documents
                  </CardTitle>
                  <CardDescription>Upload PDF files</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div
                    className={`border-2 border-dashed rounded-lg p-4 text-center ${
                      dragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
                    }`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                  >
                    <Upload className="mx-auto h-8 w-8 text-gray-400 mb-2" />
                    <p className="text-xs text-gray-600">Drag PDFs here or</p>
                    <label className="cursor-pointer">
                      <span className="text-blue-600 hover:text-blue-500 font-medium text-sm">browse files</span>
                      <input
                        type="file"
                        multiple
                        accept=".pdf"
                        onChange={handleFileChange}
                        disabled={loading}
                        className="hidden"
                      />
                    </label>
                  </div>

                  {selectedFiles.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium text-sm text-gray-700">Selected Files</h4>
                      {selectedFiles.map((file, index) => (
                        <div key={index} className="bg-gray-50 rounded-lg p-2">
                          <div className="flex justify-between">
                            <span className="text-xs font-medium truncate">{file.name}</span>
                            <span className="text-xs text-gray-500">{formatFileSize(file.size)}</span>
                          </div>
                          {uploadProgress[file.name] !== undefined && (
                            <Progress value={uploadProgress[file.name]} className="h-1 mt-1" />
                          )}
                        </div>
                      ))}
                      <Button onClick={handleFileUpload} disabled={loading} className="w-full" size="sm">
                        {loading
                          ? "Uploading..."
                          : `Upload ${selectedFiles.length} PDF${selectedFiles.length > 1 ? "s" : ""}`}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Uploaded Documents Section */}
              <Card className="flex-1 overflow-hidden">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" /> Documents ({documents.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="overflow-y-auto">
                  {documents.length > 0 ? (
                    <div className="space-y-2">
                      {documents.map((doc, index) => (
                        <div key={index} className="bg-gray-50 rounded-lg p-2">
                          <h4 className="font-medium text-sm truncate">{doc.filename}</h4>
                          <div className="flex gap-3 text-xs text-gray-500 mt-1">
                            <span className="flex items-center gap-1">
                              <Hash className="h-3 w-3" /> {doc.chunk_count}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" /> {formatTimestamp(doc.upload_date).split(",")[0]}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 text-center">No documents uploaded yet</p>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="flex-1 flex flex-col gap-4">
              {/* Ask Question Section */}
              <Card className="flex-shrink-0">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" /> Ask Questions
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Textarea
                    placeholder="Ask a question about your uploaded documents..."
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    disabled={loading || documents.length === 0}
                    rows={2}
                    className="resize-none"
                  />
                  <div className="flex gap-2">
                    <Button
                      onClick={handleAskQuestion}
                      disabled={loading || !question.trim() || documents.length === 0}
                      className="flex-1"
                    >
                      {loading ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <Send className="mr-2 h-4 w-4" /> Ask Question
                        </>
                      )}
                    </Button>
                  </div>
                  {documents.length === 0 && (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>Please upload documents before asking questions.</AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              {/* Chat History - Takes up remaining space */}
              <Card className="flex-1 overflow-hidden">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" /> Conversation History
                  </CardTitle>
                </CardHeader>
                <CardContent className="h-full overflow-y-auto">
                  {chatHistory.length > 0 ? (
                    <div className="space-y-4">
                      {chatHistory.map((entry, index) => (
                        <div key={index} className="border-l-4 border-blue-500 pl-4 space-y-3">
                          <div className="bg-blue-50 rounded-lg p-3">
                            <p className="font-medium text-sm">Question:</p>
                            <p className="text-sm">{entry.question}</p>
                          </div>
                          <div className="bg-green-50 rounded-lg p-3">
                            <p className="font-medium text-sm">Answer:</p>
                            <ReactMarkdown
                              className="text-sm prose prose-sm max-w-none"
                              remarkPlugins={[remarkMath]}
                              rehypePlugins={[rehypeKatex]}
                            >
                              {entry.answer}
                            </ReactMarkdown>
                          </div>
                          {entry.sources && entry.sources.length > 0 && (
                            <div className="bg-amber-50 rounded-lg p-3">
                              <p className="font-medium text-sm">Sources:</p>
                              <ul className="text-sm">
                                {entry.sources.map((src, i) => (
                                  <li key={i}>• {src}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          <div className="flex gap-4 text-xs text-gray-500">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" /> {formatTimestamp(entry.timestamp)}
                            </span>
                            {entry.total_tokens && <Badge variant="secondary">{entry.total_tokens} tokens</Badge>}
                            {entry.cost && (
                              <span className="flex items-center gap-1">
                                <DollarSign className="h-3 w-3" /> ${entry.cost.toFixed(4)}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <p className="text-center text-gray-500">
                        No conversation history yet. Upload documents and ask your first question!
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
