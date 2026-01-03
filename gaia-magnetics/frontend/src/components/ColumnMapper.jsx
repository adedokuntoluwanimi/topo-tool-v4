import React from 'react'

function ColumnMapper({ headers, mapping, onMappingChange }) {
  const handleChange = (field, value) => {
    onMappingChange({
      ...mapping,
      [field]: value
    })
  }

  // Filter out already selected columns for each dropdown
  const getAvailableOptions = (currentField) => {
    const selected = Object.entries(mapping)
      .filter(([key, val]) => key !== currentField && val)
      .map(([, val]) => val)
    
    return headers.filter(h => !selected.includes(h))
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-white">Map Columns</h3>
      <p className="text-sm text-gray-400">
        Select which columns contain your coordinate and measurement data.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* X Column */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            X / Easting Column
          </label>
          <select
            value={mapping.x_column || ''}
            onChange={(e) => handleChange('x_column', e.target.value)}
            className="w-full px-3 py-2 bg-dark-secondary border border-dark-border rounded-md text-white focus:ring-geodev-500 focus:border-geodev-500"
          >
            <option value="">Select column...</option>
            {getAvailableOptions('x_column').map(header => (
              <option key={header} value={header}>{header}</option>
            ))}
          </select>
        </div>

        {/* Y Column */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Y / Northing Column
          </label>
          <select
            value={mapping.y_column || ''}
            onChange={(e) => handleChange('y_column', e.target.value)}
            className="w-full px-3 py-2 bg-dark-secondary border border-dark-border rounded-md text-white focus:ring-geodev-500 focus:border-geodev-500"
          >
            <option value="">Select column...</option>
            {getAvailableOptions('y_column').map(header => (
              <option key={header} value={header}>{header}</option>
            ))}
          </select>
        </div>

        {/* Value Column */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Measurement Value Column
          </label>
          <select
            value={mapping.value_column || ''}
            onChange={(e) => handleChange('value_column', e.target.value)}
            className="w-full px-3 py-2 bg-dark-secondary border border-dark-border rounded-md text-white focus:ring-geodev-500 focus:border-geodev-500"
          >
            <option value="">Select column...</option>
            {getAvailableOptions('value_column').map(header => (
              <option key={header} value={header}>{header}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Validation message */}
      {mapping.x_column && mapping.y_column && mapping.value_column && (
        <div className="p-2 bg-geodev-900/30 border border-geodev-700 rounded text-geodev-400 text-sm">
          ✓ All columns mapped
        </div>
      )}
    </div>
  )
}

export default ColumnMapper
