import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import JobStatus from '../components/JobStatus'
import ResultChart from '../components/ResultChart'
import ResultTable from '../components/ResultTable'
import { getJob, getJobResult, getJobResultDownload } from '../api'

function JobPage() {
  const { jobId } = useParams()
  const [job, setJob] = useState(null)
  const [result, setResult] = useState(null)
  const [isComplete, setIsComplete] = useState(false)
  const [loadingResult, setLoadingResult] = useState(false)
  const [error, setError] = useState(null)

  // Load initial job data
  useEffect(() => {
    const loadJob = async () => {
      try {
        const data = await getJob(jobId)
        setJob(data)
        if (data.status === 'complete') {
          setIsComplete(true)
        }
      } catch (err) {
        setError('Failed to load job')
      }
    }
    loadJob()
  }, [jobId])

  // Load results when complete
  useEffect(() => {
    if (isComplete && !result) {
      loadResults()
    }
  }, [isComplete])

  const loadResults = async () => {
    setLoadingResult(true)
    try {
      const data = await getJobResult(jobId)
      setResult(data)
    } catch (err) {
      setError('Failed to load results')
    } finally {
      setLoadingResult(false)
    }
  }

  const handleComplete = () => {
    setIsComplete(true)
  }

  const handleDownload = async () => {
    try {
      const url = await getJobResultDownload(jobId)
      window.open(url, '_blank')
    } catch (err) {
      setError('Failed to generate download link')
    }
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-6 text-center">
          <svg className="mx-auto h-12 w-12 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-red-400">{error}</h3>
          <Link to="/" className="mt-4 inline-block text-geodev-400 hover:text-geodev-300">
            ← Back to Home
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link to="/" className="text-geodev-400 hover:text-geodev-300 text-sm">
            ← Back to Home
          </Link>
          <h1 className="mt-2 text-2xl font-bold text-white">Job: {jobId}</h1>
        </div>
        {job && (
          <div className="text-right text-sm text-gray-500">
            <p>Created: {new Date(job.created_at).toLocaleString()}</p>
            {job.completed_at && (
              <p>Completed: {new Date(job.completed_at).toLocaleString()}</p>
            )}
          </div>
        )}
      </div>

      {/* Job Status */}
      {!isComplete && (
        <div className="mb-6">
          <JobStatus 
            jobId={jobId} 
            onComplete={handleComplete}
            onError={(msg) => setError(msg)}
          />
        </div>
      )}

      {/* Job Info */}
      {job && (
        <div className="mb-6 card p-4">
          <h3 className="font-medium text-white mb-2">Job Configuration</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Scenario:</span>
              <span className="ml-2 text-gray-300">{job.scenario}</span>
            </div>
            <div>
              <span className="text-gray-500">Spacing:</span>
              <span className="ml-2 text-gray-300">{job.station_spacing || '-'}</span>
            </div>
            <div>
              <span className="text-gray-500">Input Rows:</span>
              <span className="ml-2 text-gray-300">{job.input_rows || '-'}</span>
            </div>
            <div>
              <span className="text-gray-500">Output Rows:</span>
              <span className="ml-2 text-gray-300">{job.output_rows || '-'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {isComplete && (
        <>
          {loadingResult ? (
            <div className="text-center py-12">
              <svg className="animate-spin h-8 w-8 mx-auto text-geodev-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="mt-2 text-gray-500">Loading results...</p>
            </div>
          ) : result ? (
            <div className="space-y-6">
              {/* Summary */}
              <div className="bg-geodev-900/30 border border-geodev-700 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-geodev-400">Results Ready</h3>
                    <p className="text-sm text-geodev-500">
                      {result.measured_count} measured points + {result.predicted_count} predicted points = {result.total_rows} total
                    </p>
                  </div>
                  <button
                    onClick={handleDownload}
                    className="px-4 py-2 bg-geodev-600 text-white rounded hover:bg-geodev-700"
                  >
                    Download CSV
                  </button>
                </div>
              </div>

              {/* Chart */}
              <ResultChart data={result.data} />

              {/* Table */}
              <ResultTable data={result.data} onDownload={handleDownload} />
            </div>
          ) : null}
        </>
      )}
    </div>
  )
}

export default JobPage
