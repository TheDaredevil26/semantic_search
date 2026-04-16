/**
 * ConnectModal — Contact options overlay for reaching out to an alumni.
 */
export default function ConnectModal({ alumni, onClose }) {
  if (!alumni) return null;

  const initials = alumni.name
    ?.split(' ')
    .map(n => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase() || '??';

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/20 z-50 animate-fade-in" onClick={onClose} />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div className="pointer-events-auto bg-white rounded-xl shadow-xl max-w-sm w-full animate-slide-up">
          {/* Close */}
          <div className="flex justify-end p-3">
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <div className="px-6 pb-6">
            {/* Header */}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center text-lg font-semibold">
                {initials}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{alumni.name}</h3>
                <p className="text-sm text-gray-500">{alumni.role}</p>
              </div>
            </div>

            <p className="text-sm text-gray-500 mb-4">Reach out and start a conversation:</p>

            {/* Contact options */}
            <div className="space-y-2">
              <a
                href={alumni.phone && alumni.phone !== 'N/A' ? `tel:${alumni.phone}` : '#'}
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 A19.5 19.5 0 013.07 9.81 19.79 19.79 0 01.22 1.18 2 2 0 012.2 0h3a2 2 0 012 1.72c.127.96.36 1.903.7 2.81a2 2 0 01-.45 2.11L6.27 7.91a16 16 0 006.29 6.29l1.28-1.28a2 2 0 012.11-.45c.907.34 1.85.573 2.81.7A2 2 0 0122 16.92z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-gray-400">Call</div>
                  <div className="text-sm text-gray-700 truncate">{alumni.phone || 'Not available'}</div>
                </div>
                <svg className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6" /></svg>
              </a>

              <a
                href={alumni.email && alumni.email !== 'N/A' ? `mailto:${alumni.email}` : '#'}
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6c0-1.1.9-2 2-2z" />
                    <polyline points="22,6 12,13 2,6" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-gray-400">Email</div>
                  <div className="text-sm text-gray-700 truncate">{alumni.email || 'Not available'}</div>
                </div>
                <svg className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6" /></svg>
              </a>
            </div>

            <p className="text-xs text-gray-400 mt-4 leading-relaxed">
              Always introduce yourself and mention your shared connection (batch, department, skill) when reaching out.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
