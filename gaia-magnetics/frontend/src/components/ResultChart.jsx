import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Scatter
} from 'recharts'

function ResultChart({ data }) {
  const measuredData = data.filter(d => d.source === 'measured')
  const predictedData = data.filter(d => d.source === 'predicted')

  const chartData = data.map(d => ({
    distance: d.distance,
    value: d.value,
    measured: d.source === 'measured' ? d.value : null,
    predicted: d.source === 'predicted' ? d.value : null,
    uncertainty: d.uncertainty || 0
  }))

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const point = payload[0].payload
      return (
        <div className="bg-dark-card p-3 border border-dark-border rounded shadow-lg">
          <p className="font-medium text-white">Distance: {point.distance.toFixed(1)}</p>
          <p className="text-gray-300">Value: {point.value.toFixed(2)}</p>
          {point.uncertainty > 0 && (
            <p className="text-gray-400 text-sm">Uncertainty: +/-{point.uncertainty.toFixed(2)}</p>
          )}
          <p className={`text-sm ${point.measured !== null ? 'text-green-400' : 'text-blue-400'}`}>
            {point.measured !== null ? 'Measured' : 'Predicted'}
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="card p-4">
      <h3 className="text-lg font-medium text-white mb-4">Survey Results</h3>
      
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
            <XAxis 
              dataKey="distance" 
              label={{ value: 'Distance (m)', position: 'insideBottom', offset: -10, fill: '#a1a1aa' }}
              stroke="#a1a1aa"
              tick={{ fill: '#a1a1aa' }}
            />
            <YAxis 
              label={{ value: 'Magnetic Value (nT)', angle: -90, position: 'insideLeft', fill: '#a1a1aa' }}
              stroke="#a1a1aa"
              tick={{ fill: '#a1a1aa' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ color: '#a1a1aa' }} />
            
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              name="Predicted"
              connectNulls
            />
            
            <Scatter
              dataKey="measured"
              fill="#22c55e"
              name="Measured"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex justify-center space-x-6 text-sm">
        <div className="flex items-center">
          <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
          <span className="text-gray-400">Measured Points ({measuredData.length})</span>
        </div>
        <div className="flex items-center">
          <span className="w-8 h-0.5 bg-blue-500 mr-2"></span>
          <span className="text-gray-400">Predicted Values ({predictedData.length})</span>
        </div>
      </div>
    </div>
  )
}

export default ResultChart
