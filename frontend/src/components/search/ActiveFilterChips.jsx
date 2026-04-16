/**
 * ActiveFilterChips — Displays active filters as removable chips above search results.
 */
export default function ActiveFilterChips({ filters, onRemove }) {
  const chips = [];

  if (filters.company) chips.push({ label: `🏢 ${filters.company}`, key: 'company' });
  if (filters.location) chips.push({ label: `📍 ${filters.location}`, key: 'location' });
  if (filters.batchYear) chips.push({ label: `🎓 ${filters.batchYear}`, key: 'batchYear' });

  if (filters.skills && filters.skills.length > 0) {
    filters.skills.forEach(s => {
      chips.push({ label: `⚡ ${s}`, key: 'skills', value: s });
    });
  }

  if (filters.batchFilter && filters.batchFilter.length > 0) {
    filters.batchFilter.forEach(b => {
      chips.push({ label: `Batch: ${b}`, key: 'batchFilter', value: b });
    });
  }

  if (filters.deptFilter && filters.deptFilter.length > 0) {
    filters.deptFilter.forEach(d => {
      chips.push({ label: `Dept: ${d}`, key: 'deptFilter', value: d });
    });
  }

  if (chips.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2 mb-4 animate-fade-in">
      <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">Active:</span>
      {chips.map((chip, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1.5 px-2 py-1 bg-white border border-indigo-100 rounded-md text-xs text-indigo-700 shadow-sm"
        >
          {chip.label}
          <button
            onClick={() => onRemove(chip.key, chip.value)}
            className="p-0.5 rounded text-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </span>
      ))}
    </div>
  );
}
