import React, { useState } from 'react'

const ROWS_PER_PAGE = 100

function ResultTable({ data, onDownload }) {
  const [page, setPage] = useState(0)
  const [filter, setFilter] = useState('all')

  const filteredData = filter === 'all' 
    ? data 
    : data.filter(d => d.source === filter)

  const totalPages = Math.ceil(filteredData.length / ROWS_PER_PAGE)
  const pageData = filteredData.slice(
    page * ROWS_PER_PAGE,
    (page + 1) * ROWS_PER_PAGE
  )

  return (
    <div className="card overflow-hidden">
      <div className="px-4 py-3 border-b border-dark-border flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-medium text-white">Data Table</h3>
          
          <select
            value={filter}
            onChange={(e) => { setFilter(e.target.value); setPage(0); }}
            className="text-sm bg-dark-secondary border border-dark-border rounded px-2 py-1 text-gray-300"
          >
            <option value="all">All ({data.length})</option>
            <option value="measured">Measured ({data.filter(d => d.source === 'measured').length})</option>
            <option value="predicted">Predicted ({data.filter(d => d.source === 'predicted').length})</option>
          </select>
        </div>

        <button
          onClick={onDownload}
          className="flex items-center px-3 py-1.5 text-sm bg-geodev-600 text-white rounded hover:bg-geodev-700"
        >
          <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download CSV
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-dark-border">
          <thead className="bg-dark-secondary">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Distance
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                X
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Y
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Value
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Source
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Uncertainty
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-border">
            {pageData.map((row, idx) => (
              <tr key={idx} className={row.source === 'measured' ? 'bg-green-900/10' : ''}>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-300">
                  {row.distance.toFixed(2)}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-300">
                  {row.x.toFixed(2)}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-300">
                  {row.y.toFixed(2)}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-white font-medium">
                  {row.value.toFixed(2)}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm">
                  <span className={`
                    px-2 py-1 rounded-full text-xs font-medium border
                    ${row.source === 'measured' 
                      ? 'bg-green-900/30 text-green-400 border-green-700' 
                      : 'bg-blue-900/30 text-blue-400 border-blue-700'
                    }
                  `}>
                    {row.source}
                  </span>
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                  {row.uncertainty ? `+/-${row.uncertainty.toFixed(2)}` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="px-4 py-3 border-t border-dark-border flex justify-between items-center">
          <span className="text-sm text-gray-500">
            Showing {page * ROWS_PER_PAGE + 1} - {Math.min((page + 1) * ROWS_PER_PAGE, filteredData.length)} of {filteredData.length}
          </span>
          <div className="flex space-x-2">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1 text-sm border border-dark-border rounded text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-dark-secondary"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="px-3 py-1 text-sm border border-dark-border rounded text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-dark-secondary"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ResultTable
