export default function CompareModal({ isOpen, onClose, selectedProfiles }) {
  if (!isOpen || !selectedProfiles || selectedProfiles.length < 2) return null;

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 sm:p-6 animate-fade-in">
      <div 
        className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" 
        onClick={onClose} 
      />
      <div className="relative w-full max-w-5xl bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-full ring-1 ring-gray-200">
        <div className="px-6 py-4 flex items-center justify-between border-b border-gray-100 bg-gray-50/50">
          <h2 className="text-xl font-bold tracking-tight text-gray-900">Compare Attributes</h2>
          <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-600 bg-white rounded-full border border-gray-200 hover:bg-gray-100 transition-colors">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr>
                  <th className="p-4 border-b border-gray-100 bg-white sticky left-0 z-10 w-48 shadow-[1px_0_0_0_#F3F4F6]">
                    Feature
                  </th>
                  {selectedProfiles.map(p => (
                    <th key={p.alumnus_id} className="p-4 border-b border-gray-200 w-64 min-w-[200px]">
                      <div className="flex flex-col items-start gap-1">
                        <div className="w-12 h-12 rounded-full border-2 border-indigo-100 bg-indigo-50 flex items-center justify-center text-indigo-700 font-bold text-lg">
                          {p.full_name?.charAt(0) || '?'}
                        </div>
                        <span className="font-bold text-gray-900 inline-block mt-2">{p.full_name}</span>
                        <span className="font-normal text-xs text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md">
                          {p.batch_year}
                        </span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="text-sm">
                
                {/* Role */}
                <tr className="hover:bg-gray-50/50 transition-colors">
                  <td className="p-4 border-b border-gray-100 bg-white sticky left-0 z-10 text-gray-500 font-medium shadow-[1px_0_0_0_#F3F4F6]">Role & Company</td>
                  {selectedProfiles.map(p => (
                    <td key={p.alumnus_id} className="p-4 border-b border-gray-100">
                      <span className="font-medium text-gray-800">{p.current_role}</span>
                      <br/>
                      <span className="text-gray-500 text-xs">at {p.current_company}</span>
                    </td>
                  ))}
                </tr>

                {/* Location */}
                <tr className="hover:bg-gray-50/50 transition-colors bg-gray-50/30">
                  <td className="p-4 border-b border-gray-100 shadow-[1px_0_0_0_#F3F4F6] bg-gray-50/30 sticky left-0 z-10 text-gray-500 font-medium">Location</td>
                  {selectedProfiles.map(p => (
                    <td key={p.alumnus_id} className="p-4 border-b border-gray-100">
                      <span className="inline-flex items-center gap-1.5 px-2 py-1 bg-white border border-gray-200 rounded-md text-xs text-gray-600">
                        📍 {p.city}
                      </span>
                    </td>
                  ))}
                </tr>
                
                {/* Department */}
                <tr className="hover:bg-gray-50/50 transition-colors">
                  <td className="p-4 border-b border-gray-100 bg-white sticky left-0 z-10 text-gray-500 font-medium shadow-[1px_0_0_0_#F3F4F6]">Department</td>
                  {selectedProfiles.map(p => (
                    <td key={p.alumnus_id} className="p-4 border-b border-gray-100 text-gray-700">
                      {p.department}
                    </td>
                  ))}
                </tr>

                {/* Skills */}
                <tr className="hover:bg-gray-50/50 transition-colors bg-gray-50/30">
                  <td className="p-4 border-b border-gray-100 shadow-[1px_0_0_0_#F3F4F6] bg-gray-50/30 sticky left-0 z-10 text-gray-500 font-medium">Top Skills</td>
                  {selectedProfiles.map(p => (
                    <td key={p.alumnus_id} className="p-4 border-b border-gray-100 align-top">
                      <div className="flex flex-wrap gap-1.5">
                        {(p.skills || []).slice(0, 5).map((skill, i) => (
                          <span key={i} className="px-2 py-1 bg-white border border-gray-200 rounded text-[10px] text-gray-600 shadow-sm">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </td>
                  ))}
                </tr>

                {/* Bio Summary */}
                <tr className="hover:bg-gray-50/50 transition-colors">
                  <td className="p-4 border-b border-gray-100 bg-white sticky left-0 z-10 text-gray-500 font-medium shadow-[1px_0_0_0_#F3F4F6] align-top">Summary Bio</td>
                  {selectedProfiles.map(p => (
                    <td key={p.alumnus_id} className="p-4 border-b border-gray-100 text-xs text-gray-600 leading-relaxed align-top">
                      <div className="line-clamp-4">
                        {p.bio || "No summary provided."}
                      </div>
                    </td>
                  ))}
                </tr>
                
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
