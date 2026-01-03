import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FileUpload from '../components/FileUpload'
import ColumnMapper from '../components/ColumnMapper'
import JobConfig from '../components/JobConfig'
import { submitJob } from '../api'

function HomePage() {
  const navigate = useNavigate()
  
  const [file, setFile] = useState(null)
  const [headers, setHeaders] = useState([])
  const [mapping, setMapping] = useState({
    x_column: '',
    y_column: '',
    value_column: ''
  })
  const [config, setConfig] = useState({
    scenario: 'sparse',
    station_spacing: 10,
    coordinate_system: 'projected'
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const handleFileSelect = (selectedFile, parsedHeaders) => {
    setFile(selectedFile)
    setHeaders(parsedHeaders)
    setMapping({ x_column: '', y_column: '', value_column: '' })
    setError(null)
  }

  const isMappingComplete = () => {
    return mapping.x_column && mapping.y_column && mapping.value_column
  }

  const handleSubmit = async () => {
    if (!file || !isMappingComplete()) return

    setIsSubmitting(true)
    setError(null)

    try {
      const jobConfig = {
        ...config,
        ...mapping
      }

      const result = await submitJob(file, jobConfig)
      
      // Navigate to job page
      navigate(`/jobs/${result.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit job')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="font-geodev text-4xl text-white tracking-wide mb-2">
          GEOPHYSICAL MAGNETICS PREDICTION
        </h1>
        <p className="text-gray-400">
          Upload your sparse survey data and get predictions for the entire traverse
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
          <div className="flex items-center">
            <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        </div>
      )}

      {/* Step 1: File Upload */}
      <div className="card p-6 mb-6">
        <div className="flex items-center mb-4">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-geodev-600 text-white font-medium text-sm mr-3">
            1
          </span>
          <h2 className="text-lg font-medium text-white">Upload Survey Data</h2>
        </div>
        <FileUpload onFileSelect={handleFileSelect} />
      </div>

      {/* Step 2: Column Mapping */}
      {headers.length > 0 && (
        <div className="card p-6 mb-6">
          <div className="flex items-center mb-4">
            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-geodev-600 text-white font-medium text-sm mr-3">
              2
            </span>
            <h2 className="text-lg font-medium text-white">Map Columns</h2>
          </div>
          <ColumnMapper 
            headers={headers} 
            mapping={mapping} 
            onMappingChange={setMapping} 
          />
        </div>
      )}

      {/* Step 3: Configuration */}
      {isMappingComplete() && (
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-geodev-600 text-white font-medium text-sm mr-3">
              3
            </span>
            <h2 className="text-lg font-medium text-white">Configure & Submit</h2>
          </div>
          <JobConfig 
            config={config}
            onConfigChange={setConfig}
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
          />
        </div>
      )}

      {/* Help Text */}
      <div className="mt-8 text-center text-sm text-gray-500">
        <p>
          Supported format: CSV with X, Y coordinates and measurement values.
        </p>
        <p className="mt-1">
          Processing typically takes 3-5 minutes depending on data size.
        </p>
      </div>
    </div>
  )
}

export default HomePage
