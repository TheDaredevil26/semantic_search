import { useState } from 'react';

/**
 * FilterSidebar — Low-contrast sidebar for applying search filters.
 * Includes batch year, department, company, location, skills, and graph weight.
 */
export default function FilterSidebar({ filterOptions, activeFilters, onUpdateFilter, onClear, onApply }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  function toggleBatchYear(year) {
    const current = activeFilters.batchFilter || [];
    const updated = current.includes(year)
      ? current.filter(y => y !== year)
      : [...current, year];
    onUpdateFilter('batchFilter', updated);
  }

  function toggleDept(dept) {
    const current = activeFilters.deptFilter || [];
    const updated = current.includes(dept)
      ? current.filter(d => d !== dept)
      : [...current, dept];
    onUpdateFilter('deptFilter', updated);
  }

  function handleSkillsChange(value) {
    const skills = value.split(',').map(s => s.trim()).filter(Boolean);
    onUpdateFilter('skills', skills);
  }

  return (
    <aside className={`bg-white border border-gray-100 rounded-xl transition-all duration-300 ${isCollapsed ? 'w-12' : 'w-64'} flex-shrink-0`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-50">
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="4" y1="6" x2="20" y2="6" /><line x1="8" y1="12" x2="16" y2="12" /><line x1="10" y1="18" x2="14" y2="18" />
            </svg>
            <span className="text-sm font-medium text-gray-700">Filters</span>
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1 rounded hover:bg-gray-50 text-gray-400 transition-colors"
          title={isCollapsed ? 'Expand filters' : 'Collapse filters'}
        >
          <svg className={`w-4 h-4 transition-transform ${isCollapsed ? 'rotate-180' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>

      {!isCollapsed && (
        <div className="p-4 space-y-5 max-h-[calc(100vh-200px)] overflow-y-auto">
          {/* Batch Year */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Batch Year</h4>
            <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto">
              {filterOptions.batch_years?.map(year => {
                const isActive = (activeFilters.batchFilter || []).includes(year);
                return (
                  <button
                    key={year}
                    onClick={() => toggleBatchYear(year)}
                    className={`px-2 py-1 text-xs rounded-md border transition-colors ${
                      isActive
                        ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                        : 'border-gray-100 text-gray-500 hover:border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    {year}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Department */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Department</h4>
            <div className="space-y-1 max-h-36 overflow-y-auto">
              {filterOptions.departments?.map(dept => {
                const isActive = (activeFilters.deptFilter || []).includes(dept);
                return (
                  <label key={dept} className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-gray-50 cursor-pointer transition-colors">
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={() => toggleDept(dept)}
                      className="w-3.5 h-3.5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 focus:ring-1"
                    />
                    <span className="text-xs text-gray-600 truncate">{dept}</span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="h-px bg-gray-50" />

          {/* Company */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Company</h4>
            <input
              type="text"
              value={activeFilters.company || ''}
              onChange={(e) => onUpdateFilter('company', e.target.value)}
              placeholder="e.g. Google"
              className="w-full px-3 py-2 text-xs border border-gray-100 rounded-lg bg-gray-50/50 text-gray-700 placeholder:text-gray-300 focus:outline-none focus:border-indigo-200 focus:ring-1 focus:ring-indigo-100 transition-colors"
              list="company-datalist"
            />
            <datalist id="company-datalist">
              {filterOptions.companies?.slice(0, 50).map(c => <option key={c} value={c} />)}
            </datalist>
          </div>

          {/* Location */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Location</h4>
            <input
              type="text"
              value={activeFilters.location || ''}
              onChange={(e) => onUpdateFilter('location', e.target.value)}
              placeholder="e.g. Bangalore"
              className="w-full px-3 py-2 text-xs border border-gray-100 rounded-lg bg-gray-50/50 text-gray-700 placeholder:text-gray-300 focus:outline-none focus:border-indigo-200 focus:ring-1 focus:ring-indigo-100 transition-colors"
              list="location-datalist"
            />
            <datalist id="location-datalist">
              {filterOptions.locations?.slice(0, 50).map(l => <option key={l} value={l} />)}
            </datalist>
          </div>

          {/* Batch Year Range */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Batch Year / Range</h4>
            <input
              type="text"
              value={activeFilters.batchYear || ''}
              onChange={(e) => onUpdateFilter('batchYear', e.target.value)}
              placeholder="e.g. 2019 or 2015-2020"
              className="w-full px-3 py-2 text-xs border border-gray-100 rounded-lg bg-gray-50/50 text-gray-700 placeholder:text-gray-300 focus:outline-none focus:border-indigo-200 focus:ring-1 focus:ring-indigo-100 transition-colors"
            />
          </div>

          {/* Skills */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Skills</h4>
            <input
              type="text"
              value={(activeFilters.skills || []).join(', ')}
              onChange={(e) => handleSkillsChange(e.target.value)}
              placeholder="e.g. Python, ML"
              className="w-full px-3 py-2 text-xs border border-gray-100 rounded-lg bg-gray-50/50 text-gray-700 placeholder:text-gray-300 focus:outline-none focus:border-indigo-200 focus:ring-1 focus:ring-indigo-100 transition-colors"
            />
          </div>

          <div className="h-px bg-gray-50" />

          {/* Graph Weight Slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider">Graph Weight</h4>
              <span className="text-xs font-mono text-indigo-600">{(activeFilters.graphWeight || 0.4).toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={(activeFilters.graphWeight || 0.4) * 100}
              onChange={(e) => onUpdateFilter('graphWeight', parseInt(e.target.value) / 100)}
              className="w-full h-1.5 bg-gray-100 rounded-full appearance-none cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-[10px] text-gray-300 mt-1">
              <span>Vector Only</span>
              <span>Graph Only</span>
            </div>
          </div>

          <div className="h-px bg-gray-50" />

          {/* Action buttons */}
          <div className="flex gap-2">
            <button
              onClick={onApply}
              className="flex-1 px-3 py-2 text-xs font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Apply
            </button>
            <button
              onClick={onClear}
              className="flex-1 px-3 py-2 text-xs font-medium border border-gray-200 text-gray-500 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
