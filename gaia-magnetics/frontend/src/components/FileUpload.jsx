import React, { useState, useCallback } from 'react'
import Papa from 'papaparse'

function FileUpload({ onFileSelect }) {
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [error, setError] = useState(null)

  const processFile = useCallback((file) => {
    setError(null)

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file')
      return
    }

    // Parse CSV headers
    Papa.parse(file, {
      preview: 1,
      complete: (results) => {
        if (results.data && results.data.length > 0) {
          const headers = results.data[0]
          setSelectedFile(file)
          onFileSelect(file, headers)
        } else {
          setError('Could not parse CSV headers')
        }
      },
      error: (err) => {
        setError(`Error parsing CSV: ${err.message}`)
      }
    })
  }, [onFileSelect])

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      processFile(files[0])
    }
  }

  const handleFileInput = (e) => {
    const files = e.target.files
    if (files.length > 0) {
      processFile(files[0])
    }
  }

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragging 
            ? 'border-geodev-500 bg-geodev-900/20' 
            : 'border-dark-border hover:border-geodev-400 hover:bg-dark-secondary'
          }
          ${selectedFile ? 'bg-geodev-900/20 border-geodev-500' : ''}
        `}
      >
        <input
          type="file"
          accept=".csv"
          onChange={handleFileInput}
          className="hidden"
          id="file-upload"
        />
        <label htmlFor="file-upload" className="cursor-pointer">
          {selectedFile ? (
            <div>
              <svg className="mx-auto h-12 w-12 text-geodev-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="mt-2 text-sm font-medium text-geodev-400">{selectedFile.name}</p>
              <p className="mt-1 text-xs text-gray-500">Click or drag to replace</p>
            </div>
          ) : (
            <div>
              <svg className="mx-auto h-12 w-12 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="mt-2 text-sm font-medium text-gray-300">
                Drop your CSV file here
              </p>
              <p className="mt-1 text-xs text-gray-500">or click to browse</p>
            </div>
          )}
        </label>
      </div>

      {error && (
        <div className="mt-2 p-2 bg-red-900/30 border border-red-700 rounded text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  )
}

export default FileUpload
