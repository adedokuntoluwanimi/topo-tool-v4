import React from 'react'

function JobConfig({ config, onConfigChange, onSubmit, isSubmitting }) {
  const handleChange = (field, value) => {
    onConfigChange({
      ...config,
      [field]: value
    })
  }

  const isValid = () => {
    if (config.scenario === 'sparse' && !config.station_spacing) {
      return false
    }
    return true
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-white">Job Configuration</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Scenario */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Prediction Scenario
          </label>
          <select
            value={config.scenario || 'sparse'}
            onChange={(e) => handleChange('scenario', e.target.value)}
            className="w-full px-3 py-2 bg-dark-secondary border border-dark-border rounded-md text-white focus:ring-geodev-500 focus:border-geodev-500"
          >
            <option value="sparse">Sparse (generate prediction stations)</option>
            <option value="explicit">Explicit (use existing geometry)</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            {config.scenario === 'sparse' 
              ? 'Generate evenly spaced prediction points along traverse'
              : 'Predict at locations with empty values in your CSV'
            }
          </p>
        </div>

        {/* Station Spacing - only for sparse */}
        {config.scenario === 'sparse' && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Station Spacing
            </label>
            <div className="relative">
              <input
                type="number"
                value={config.station_spacing || ''}
                onChange={(e) => handleChange('station_spacing', parseFloat(e.target.value) || '')}
                placeholder="10"
                min="0.1"
                step="0.1"
                className="w-full px-3 py-2 bg-dark-secondary border border-dark-border rounded-md text-white focus:ring-geodev-500 focus:border-geodev-500"
              />
              <span className="absolute right-3 top-2 text-gray-500 text-sm">
                {config.coordinate_system === 'geographic' ? '°' : 'm'}
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Distance between prediction stations
            </p>
          </div>
        )}

        {/* Coordinate System */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Coordinate System
          </label>
          <select
            value={config.coordinate_system || 'projected'}
            onChange={(e) => handleChange('coordinate_system', e.target.value)}
            className="w-full px-3 py-2 bg-dark-secondary border border-dark-border rounded-md text-white focus:ring-geodev-500 focus:border-geodev-500"
          >
            <option value="projected">Projected (meters, UTM)</option>
            <option value="geographic">Geographic (lat/lon)</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            {config.coordinate_system === 'projected'
              ? 'Coordinates are in meters (e.g., UTM)'
              : 'Coordinates are latitude/longitude'
            }
          </p>
        </div>
      </div>

      {/* Submit Button */}
      <div className="pt-4">
        <button
          onClick={onSubmit}
          disabled={!isValid() || isSubmitting}
          className={`
            w-full md:w-auto px-6 py-3 rounded-md font-medium text-white
            ${isValid() && !isSubmitting
              ? 'bg-geodev-600 hover:bg-geodev-700 cursor-pointer'
              : 'bg-gray-700 cursor-not-allowed'
            }
            transition-colors
          `}
        >
          {isSubmitting ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Submitting...
            </span>
          ) : (
            'Submit Job'
          )}
        </button>
      </div>
    </div>
  )
}

export default JobConfig
