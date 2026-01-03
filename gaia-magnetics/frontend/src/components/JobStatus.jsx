import React, { useState, useEffect } from 'react'
import { getJobStatus } from '../api'

const POLL_INTERVAL = 5000 // 5 seconds

const STATUS_STEPS = [
  { key: 'pending', label: 'Pending' },
  { key: 'processing', label: 'Processing' },
  { key: 'training', label: 'Training' },
  { key: 'predicting', label: 'Predicting' },
  { key: 'merging', label: 'Merging' },
  { key: 'complete', label: 'Complete' }
]

function JobStatus({ jobId, onComplete, onError }) {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let interval = null

    const fetchStatus = async () => {
      try {
        const data = await getJobStatus(jobId)
        setStatus(data)

        if (data.status === 'complete') {
          if (interval) clearInterval(interval)
          onComplete && onComplete(data)
        } else if (data.status === 'failed') {
          if (interval) clearInterval(interval)
          setError(data.error_message || 'Job failed')
          onError && onError(data.error_message)
        }
      } catch (err) {
        setError('Failed to fetch job status')
      }
    }

    // Initial fetch
    fetchStatus()

    // Start polling
    interval = setInterval(fetchStatus, POLL_INTERVAL)

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [jobId, onComplete, onError])

  const getCurrentStepIndex = () => {
    if (!status) return -1
    return STATUS_STEPS.findIndex(s => s.key === status.status)
  }

  const currentIndex = getCurrentStepIndex()

  if (error) {
    return (
      <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
        <div className="flex items-center">
          <svg className="h-5 w-5 text-red-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-red-400 font-medium">Job Failed</span>
        </div>
        <p className="mt-2 text-sm text-red-400">{error}</p>
      </div>
    )
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-white">Job Progress</h3>
        <span className="text-sm text-gray-500">{jobId}</span>
      </div>

      {/* Progress Steps */}
      <div className="relative">
        <div className="flex justify-between">
          {STATUS_STEPS.map((step, index) => (
            <div key={step.key} className="flex flex-col items-center flex-1">
              {/* Step Circle */}
              <div className={`
                w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                ${index < currentIndex 
                  ? 'bg-geodev-500 text-white' 
                  : index === currentIndex 
                    ? 'bg-geodev-500 text-white animate-pulse progress-glow'
                    : 'bg-dark-border text-gray-500'
                }
              `}>
                {index < currentIndex ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>
              {/* Step Label */}
              <span className={`
                mt-2 text-xs
                ${index <= currentIndex ? 'text-geodev-400 font-medium' : 'text-gray-500'}
              `}>
                {step.label}
              </span>
            </div>
          ))}
        </div>

        {/* Progress Line */}
        <div className="absolute top-4 left-0 right-0 h-0.5 bg-dark-border -z-10 mx-8">
          <div 
            className="h-full bg-geodev-500 transition-all duration-500"
            style={{ width: `${(currentIndex / (STATUS_STEPS.length - 1)) * 100}%` }}
          />
        </div>
      </div>

      {/* Status Message */}
      {status && (
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-400">{status.progress}</p>
          {currentIndex >= 0 && currentIndex < STATUS_STEPS.length - 1 && (
            <div className="mt-2 flex items-center justify-center text-xs text-gray-500">
              <svg className="animate-spin h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default JobStatus
