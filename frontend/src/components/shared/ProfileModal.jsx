import { useState, useEffect } from 'react';
import { getAlumniProfile } from '../../api/client';

/**
 * ProfileModal — Full alumni profile detail overlay.
 * Shows bio, skills, contact info, and action buttons.
 */
export default function ProfileModal({ alumniId, onClose, onViewGraph, onFindSimilar }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!alumniId) return;
    setLoading(true);
    getAlumniProfile(alumniId)
      .then(data => setProfile(data))
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, [alumniId]);

  if (!alumniId) return null;

  const initials = profile?.full_name
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
        <div className="pointer-events-auto bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[85vh] overflow-y-auto animate-slide-up">
          {/* Close button */}
          <div className="sticky top-0 bg-white/90 backdrop-blur-sm flex justify-end p-3 border-b border-gray-100">
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {loading ? (
            <div className="p-8 space-y-4">
              <div className="skeleton h-16 w-16 rounded-full mx-auto" />
              <div className="skeleton h-5 w-48 mx-auto" />
              <div className="skeleton h-4 w-36 mx-auto" />
              <div className="skeleton h-20 w-full mt-6" />
            </div>
          ) : !profile ? (
            <div className="p-8 text-center text-gray-400">Failed to load profile.</div>
          ) : (
            <div className="p-6">
              {/* Header */}
              <div className="text-center mb-6">
                <div className="w-16 h-16 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center text-xl font-semibold mx-auto mb-3">
                  {initials}
                </div>
                <h2 className="text-xl font-semibold text-gray-900">{profile.full_name}</h2>
                <p className="text-sm text-gray-500 mt-1">{profile.current_role} at {profile.current_company}</p>
                <div className="flex items-center justify-center gap-4 mt-3 text-xs text-gray-400">
                  <span className="flex items-center gap-1">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></svg>
                    Batch {profile.batch_year}
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c0 2 4 3 6 3s6-1 6-3v-5" /></svg>
                    {profile.department}
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" /><circle cx="12" cy="10" r="3" /></svg>
                    {profile.city}
                  </span>
                </div>
              </div>

              <div className="h-px bg-gray-100 my-4" />

              {/* Bio */}
              {profile.bio && (
                <div className="mb-4">
                  <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">About</h4>
                  <p className="text-sm text-gray-600 leading-relaxed">{profile.bio}</p>
                </div>
              )}

              {/* Skills */}
              {profile.skills?.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Skills</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {profile.skills.map((skill, i) => (
                      <span key={i} className="px-2.5 py-1 text-xs font-medium bg-gray-50 text-gray-600 rounded-md border border-gray-100">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="h-px bg-gray-100 my-4" />

              {/* Contact */}
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Contact</h4>
                <div className="flex gap-2">
                  <a href={profile.phone ? `tel:${profile.phone}` : '#'}
                    className="flex-1 flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-50 hover:bg-gray-100 text-sm text-gray-600 transition-colors border border-gray-100">
                    <svg className="w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 A19.5 19.5 0 013.07 9.81 19.79 19.79 0 01.22 1.18 2 2 0 012.2 0h3a2 2 0 012 1.72c.127.96.36 1.903.7 2.81a2 2 0 01-.45 2.11L6.27 7.91a16 16 0 006.29 6.29l1.28-1.28a2 2 0 012.11-.45c.907.34 1.85.573 2.81.7A2 2 0 0122 16.92z" />
                    </svg>
                    {profile.phone || 'N/A'}
                  </a>
                  <a href={profile.email ? `mailto:${profile.email}` : '#'}
                    className="flex-1 flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-50 hover:bg-gray-100 text-sm text-gray-600 transition-colors border border-gray-100">
                    <svg className="w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6c0-1.1.9-2 2-2z" />
                      <polyline points="22,6 12,13 2,6" />
                    </svg>
                    {profile.email || 'N/A'}
                  </a>
                </div>
              </div>

              {/* Mentor */}
              {profile.mentor_id && (
                <div className="mb-4">
                  <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Mentor</h4>
                  <p className="text-sm text-gray-600">{profile.mentor_id}</p>
                </div>
              )}

              <div className="h-px bg-gray-100 my-4" />

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={() => { onClose(); onViewGraph?.(profile.alumnus_id, profile.full_name); }}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3" /><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4" /></svg>
                  View Graph
                </button>
                <button
                  onClick={() => { onClose(); onFindSimilar?.(profile.alumnus_id, profile.full_name); }}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-gray-200 text-gray-700 text-sm font-medium hover:bg-gray-50 transition-colors"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /><path d="M3 21v-2a4 4 0 013-3.87" /></svg>
                  Find Similar
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
