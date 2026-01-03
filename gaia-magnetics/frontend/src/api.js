import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * Submit a new prediction job
 * @param {File} file - CSV file
 * @param {Object} config - Job configuration
 * @returns {Promise<Object>} - Job status response
 */
export async function submitJob(file, config) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('scenario', config.scenario)
  formData.append('x_column', config.x_column)
  formData.append('y_column', config.y_column)
  formData.append('value_column', config.value_column)
  formData.append('coordinate_system', config.coordinate_system)
  
  if (config.station_spacing) {
    formData.append('station_spacing', config.station_spacing)
  }

  const response = await api.post('/jobs', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  
  return response.data
}

/**
 * Get job details
 * @param {string} jobId - Job identifier
 * @returns {Promise<Object>} - Full job details
 */
export async function getJob(jobId) {
  const response = await api.get(`/jobs/${jobId}`)
  return response.data
}

/**
 * Get job status (lightweight)
 * @param {string} jobId - Job identifier
 * @returns {Promise<Object>} - Job status
 */
export async function getJobStatus(jobId) {
  const response = await api.get(`/jobs/${jobId}/status`)
  return response.data
}

/**
 * Get job result as JSON (for visualization)
 * @param {string} jobId - Job identifier
 * @returns {Promise<Object>} - Result data
 */
export async function getJobResult(jobId) {
  const response = await api.get(`/jobs/${jobId}/result.json`)
  return response.data
}

/**
 * Get download URL for result CSV
 * @param {string} jobId - Job identifier
 * @returns {Promise<string>} - Download URL
 */
export async function getJobResultDownload(jobId) {
  const response = await api.get(`/jobs/${jobId}/result`)
  return response.data.download_url
}

/**
 * List all jobs
 * @returns {Promise<Object>} - Jobs list response
 */
export async function listJobs() {
  const response = await api.get('/jobs')
  return response.data
}

/**
 * Delete a job
 * @param {string} jobId - Job identifier
 * @returns {Promise<Object>} - Deletion confirmation
 */
export async function deleteJob(jobId) {
  const response = await api.delete(`/jobs/${jobId}`)
  return response.data
}

/**
 * Check API health
 * @returns {Promise<Object>} - Health status
 */
export async function checkHealth() {
  const response = await api.get('/health')
  return response.data
}

export default api
