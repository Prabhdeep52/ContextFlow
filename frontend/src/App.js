import React, { useState, useEffect } from 'react';
import axios from 'axios';

import './App.css';

function App() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({});

  const API_BASE_URL = 'http://localhost:8000'; // backend runs on port 8000  

  useEffect(() => {
    // Fetch chat history when component mounts
    fetchChatHistory();
    // Fetch documents when component mounts
    fetchDocuments();
  }, []);

  const fetchChatHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/history`);
      // Backend returns {conversations: [...], total: ...}
      const conversations = response.data?.conversations || [];
      setChatHistory(conversations);
    } catch (error) {
      console.error('Error fetching chat history:', error);
      setChatHistory([]); // Set empty array on error
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents`);
      // Backend returns {total_documents: ..., total_chunks: ..., documents: [...]}
      const documents = response.data?.documents || [];
      setDocuments(documents);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setDocuments([]); // Set empty array on error
    }
  };

  const handleFileChange = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
    
    // Initialize upload progress for each file
    const progress = {};
    files.forEach(file => {
      progress[file.name] = 0;
    });
    setUploadProgress(progress);
  };

  const handleFileUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      alert('Please select PDF files to upload.');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    
    // Add all selected files
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          // Update progress for all files
          const progress = {};
          selectedFiles.forEach(file => {
            progress[file.name] = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          });
          setUploadProgress(progress);
        }
      });
      
      const message = response.data?.message || 'Files uploaded successfully';
      alert(message);
      
      // Clear selected files and refresh documents
      setSelectedFiles([]);
      setUploadProgress({});
      fetchDocuments();
      
    } catch (error) {
      console.error('Error uploading files:', error);
      alert('Error uploading files. Please check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuestionChange = (event) => {
    setQuestion(event.target.value);
  };

  const handleAskQuestion = async () => {
    if (!question || !question.trim()) {
      alert('Please enter a question.');
      return;
    }
    
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/ask`, {
        question: question,
        top_k: 4,
        include_context: false,
        context_length: 3
      });
      // The response contains the answer, but we need to refresh the chat history
      // to get the updated conversation list
      await fetchChatHistory();
      setQuestion('');
    } catch (error) {
      console.error('Error asking question:', error);
      alert('Error asking question. Please check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const handleApiKeyChange = (event) => {
    setApiKey(event.target.value);
  };

  const handleConfigureApiKey = async () => {
    if (!apiKey || !apiKey.trim()) {
      alert('Please enter your Google API Key.');
      return;
    }
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/configure_api_key`, {
        api_key: apiKey
      });
      const message = response.data?.message || 'API key configured successfully';
      alert(message);
      setApiKeyConfigured(true);
    } catch (error) {
      console.error('Error configuring API key:', error);
      alert('Error configuring API key. Please check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>RAG-based Research Paper Q&A</h1>
        <p>Upload multiple PDFs and ask questions with context tracking</p>
      </header>

      <main className="App-main">
        {/* API Key Configuration */}
        <section className="api-key-section">
          <h2>Configure API Key</h2>
          <div className="api-key-input">
            <input
              type="password"
              placeholder="Enter your Google API Key"
              value={apiKey}
              onChange={handleApiKeyChange}
              disabled={loading}
            />
            <button onClick={handleConfigureApiKey} disabled={loading || !apiKey.trim()}>
              {loading ? 'Configuring...' : 'Configure API Key'}
            </button>
          </div>
        </section>

        {/* File Upload Section */}
        <section className="upload-section">
          <h2>Upload PDF Documents</h2>
          <div className="file-input">
            <input
              type="file"
              multiple
              accept=".pdf"
              onChange={handleFileChange}
              disabled={loading}
            />
          </div>
          
          {selectedFiles && selectedFiles.length > 0 && (
            <div className="selected-files">
              <h3>Selected Files ({selectedFiles.length})</h3>
              <ul>
                {selectedFiles.map((file, index) => (
                  <li key={index}>
                    <span className="filename">{file.name}</span>
                    <span className="filesize">({formatFileSize(file.size)})</span>
                    {uploadProgress[file.name] !== undefined && (
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{width: `${uploadProgress[file.name]}%`}}
                        ></div>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
              <button 
                onClick={handleFileUpload} 
                disabled={loading}
                className="upload-button"
              >
                {loading ? 'Uploading...' : `Upload ${selectedFiles.length} PDF${selectedFiles.length > 1 ? 's' : ''}`}
              </button>
            </div>
          )}
        </section>

        {/* Document Management Section */}
        <section className="documents-section">
          <h2>Uploaded Documents ({documents?.length || 0})</h2>
          {documents && documents.length > 0 ? (
            <div className="documents-grid">
              {documents.map((doc, index) => (
                <div key={index} className="document-card">
                  <h3>{doc.filename || 'Unknown'}</h3>
                  <div className="document-info">
                    <p><strong>Chunks:</strong> {doc.chunk_count || 0}</p>
                    <p><strong>Uploaded:</strong> {formatTimestamp(doc.upload_date)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-documents">No documents uploaded yet.</p>
          )}
        </section>

        {/* Q&A Section */}
        <section className="qa-section">
          <h2>Ask Questions</h2>
          <div className="question-input">
            <textarea
              placeholder="Ask a question about your uploaded documents..."
              value={question}
              onChange={handleQuestionChange}
              disabled={loading || !documents || documents.length === 0}
              rows={3}
            />
            <button 
              onClick={handleAskQuestion} 
              disabled={loading || !question.trim() || !documents || documents.length === 0}
            >
              {loading ? 'Processing...' : 'Ask Question'}
            </button>
          </div>
        </section>

        {/* Chat History Section */}
        <section className="chat-history-section">
          <h2>Conversation History</h2>
          {chatHistory && chatHistory.length > 0 ? (
            <div className="chat-history">
              {chatHistory.map((entry, index) => (
                <div key={index} className="chat-entry">
                  <div className="question">
                    <strong>Q:</strong> {entry.question || 'Unknown question'}
                  </div>
                  <div className="answer">
                    <strong>A:</strong> {entry.answer || 'No answer available'}
                  </div>
                  {entry.sources && Array.isArray(entry.sources) && entry.sources.length > 0 && (
                    <div className="sources">
                      <strong>Sources:</strong>
                      <ul>
                        {entry.sources.map((source, sourceIndex) => (
                          <li key={sourceIndex}>
                            {source}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="metadata">
                    <small>
                      Time: {formatTimestamp(entry.timestamp)} | 
                      Tokens: {entry.total_tokens || 'N/A'} | 
                      Cost: ${(entry.cost || 0).toFixed(4)}
                    </small>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-history">No conversation history yet.</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;