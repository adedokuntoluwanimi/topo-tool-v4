import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listJobs, deleteJob } from '../api'

function HistoryPage() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    setLoading(true)
    try {
      const data = await listJobs()
      setJobs(data.jobs)
    } catch (err) {
      setError('Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (jobId) => {
    if (!confirm('Are you sure you want to delete this job?')) return

    try {
      await deleteJob(jobId)
      setJobs(jobs.filter(j => j.id !== jobId))
    } catch (err) {
      setError('Failed to delete job')
    }
  }

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-900/30 text-yellow-400 border-yellow-700',
      processing: 'bg-blue-900/30 text-blue-400 border-blue-700',
      training: 'bg-blue-900/30 text-blue-400 border-blue-700',
      predicting: 'bg-blue-900/30 text-blue-400 border-blue-700',
      merging: 'bg-blue-900/30 text-blue-400 border-blue-700',
      complete: 'bg-green-900/30 text-green-400 border-green-700',
      failed: 'bg-red-900/30 text-red-400 border-red-700'
    }

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${styles[status] || 'bg-gray-900/30 text-gray-400 border-gray-700'}`}>
        {status}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <svg className="animate-spin h-8 w-8 mx-auto text-geodev-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p className="mt-2 text-gray-500">Loading jobs...</p>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white">Job History</h1>
        <Link 
          to="/"
          className="px-4 py-2 bg-geodev-600 text-white rounded hover:bg-geodev-700"
        >
          New Job
        </Link>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-900/30 border border-red-700 rounded text-red-400">
          {error}
        </div>
      )}

      {jobs.length === 0 ? (
        <div className="text-center py-12 card">
          <svg className="mx-auto h-12 w-12 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-white">No jobs yet</h3>
          <p className="mt-1 text-gray-500">Get started by submitting your first survey data.</p>
          <Link 
            to="/"
            className="mt-4 inline-block px-4 py-2 bg-geodev-600 text-white rounded hover:bg-geodev-700"
          >
            Create New Job
          </Link>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="min-w-full divide-y divide-dark-border">
            <thead className="bg-dark-secondary">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Job ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Rows
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-border">
              {jobs.map(job => (
                <tr key={job.id} className="hover:bg-dark-secondary">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link 
                      to={`/jobs/${job.id}`}
                      className="text-geodev-400 hover:text-geodev-300 font-medium"
                    >
                      {job.id}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(job.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                    {job.input_rows || '-'} → {job.output_rows || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                    {new Date(job.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    <Link 
                      to={`/jobs/${job.id}`}
                      className="text-geodev-400 hover:text-geodev-300 mr-4"
                    >
                      View
                    </Link>
                    <button
                      onClick={() => handleDelete(job.id)}
                      className="text-red-400 hover:text-red-300"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default HistoryPage
