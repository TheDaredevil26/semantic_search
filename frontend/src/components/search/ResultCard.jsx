import { useState } from 'react';
import { toggleBookmark, isBookmarked } from '../shared/BookmarksPanel';

/**
 * ResultCard — Individual search result card with full profile info,
 * score bars, explanation, and action buttons.
 */
export default function ResultCard({
  result,
  index,
  currentPage,
  onViewGraph,
  onFindSimilar,
  onOpenProfile,
  onConnect,
  onAddToCompare,
}) {
  const [bookmarked, setBookmarked] = useState(isBookmarked(result.id));
  const [showBreakdown, setShowBreakdown] = useState(false);
  const profile = result.profile;
  const skills = profile.skills || [];
  const explanation = result.explanation?.toLowerCase() || '';
  const rank = (currentPage - 1) * 20 + index + 1;
  const bio = profile.bio || '';
  const truncatedBio = bio.length > 100 ? bio.substring(0, 100) + '...' : bio;
  const explain = result.explain || {};

  function handleBookmark(e) {
    e.stopPropagation();
    const added = toggleBookmark(result.id, profile.full_name);
    setBookmarked(added);
  }

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-5 hover:shadow-md hover:border-gray-200 transition-all duration-200 animate-slide-up group"
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      {/* Top row: rank + score + bookmark */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] font-medium text-gray-300 uppercase tracking-wider">#{rank}</span>
        <div className="flex items-center gap-2">
          <button
            onClick={handleBookmark}
            className={`p-1 rounded-md transition-colors ${bookmarked ? 'text-amber-500 hover:text-amber-600' : 'text-gray-300 hover:text-gray-400'}`}
            title="Bookmark"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill={bookmarked ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 21 12 17.27 5.82 21 7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          </button>
          <span className="text-sm font-semibold text-indigo-600">{(result.score * 100).toFixed(1)}%</span>
        </div>
      </div>

      {/* Name */}
      <h4
        className="text-base font-semibold text-gray-900 hover:text-indigo-600 cursor-pointer transition-colors mb-1"
        onClick={() => onOpenProfile?.(result.id)}
      >
        {profile.full_name}
      </h4>

      {/* Role + Company */}
      <p className="text-sm text-gray-500 mb-2">{profile.current_role} at {profile.current_company}</p>

      {/* Bio excerpt */}
      {truncatedBio && <p className="text-xs text-gray-400 mb-3 leading-relaxed">{truncatedBio}</p>}

      {/* Meta row */}
      <div className="flex items-center gap-3 mb-3 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></svg>
          Batch {profile.batch_year}
        </span>
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c0 2 4 3 6 3s6-1 6-3v-5" /></svg>
          {profile.department}
        </span>
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" /><circle cx="12" cy="10" r="3" /></svg>
          {profile.city}
        </span>
      </div>

      {/* Skills */}
      <div className="flex flex-wrap gap-1 mb-3">
        {skills.slice(0, 6).map((skill, i) => {
          const matched = explanation.includes(skill.toLowerCase());
          return (
            <span key={i} className={`px-2 py-0.5 text-[11px] rounded-md border ${
              matched
                ? 'bg-indigo-50 border-indigo-100 text-indigo-600 font-medium'
                : 'bg-gray-50 border-gray-100 text-gray-500'
            }`}>
              {skill}
            </span>
          );
        })}
        {skills.length > 6 && (
          <span className="px-2 py-0.5 text-[11px] text-gray-400 bg-gray-50 border border-gray-100 rounded-md">+{skills.length - 6}</span>
        )}
      </div>

      {/* Score bars */}
      <div className="space-y-1.5 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-gray-400 w-10">Vector</span>
          <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-400 rounded-full score-bar-animated" style={{ width: `${(result.vector_score * 100).toFixed(0)}%` }} />
          </div>
          <span className="text-[10px] text-gray-400 w-8 text-right">{(result.vector_score * 100).toFixed(0)}%</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-gray-400 w-10">Graph</span>
          <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-400 rounded-full score-bar-animated" style={{ width: `${(result.graph_score * 100).toFixed(0)}%` }} />
          </div>
          <span className="text-[10px] text-gray-400 w-8 text-right">{(result.graph_score * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Cross-encoder score */}
      {result.cross_encoder_score != null && (
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[10px] text-gray-300 font-medium">CE Score</span>
          <span className="text-[10px] font-mono text-violet-600">{result.cross_encoder_score.toFixed(3)}</span>
        </div>
      )}

      {/* Explanation */}
      <div className="bg-gray-50/80 rounded-lg p-3 mb-3 border border-gray-50">
        <div className="text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-1">Why this result?</div>
        <p className="text-xs text-gray-600 leading-relaxed">{result.explanation}</p>
      </div>

      {/* Score breakdown toggle */}
      <button
        onClick={() => setShowBreakdown(!showBreakdown)}
        className="text-[11px] text-gray-400 hover:text-indigo-600 transition-colors mb-3"
      >
        {showBreakdown ? 'Hide score breakdown ▴' : 'Show score breakdown ▾'}
      </button>

      {showBreakdown && (
        <div className="bg-gray-50/80 rounded-lg p-3 mb-3 border border-gray-50 space-y-1.5 animate-fade-in">
          <div className="text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-1">Score Breakdown</div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">Semantic (SBERT)</span>
            <span className="font-mono text-gray-700">{(explain.semantic_score || 0).toFixed(3)}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">Graph (PPR)</span>
            <span className="font-mono text-gray-700">{(explain.graph_score || 0).toFixed(3)}</span>
          </div>
          {explain.cross_encoder_score != null && (
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Cross-Encoder</span>
              <span className="font-mono text-gray-700">{explain.cross_encoder_score.toFixed(3)}</span>
            </div>
          )}
          {explain.matched_keywords?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {explain.matched_keywords.map((kw, i) => (
                <span key={i} className="px-1.5 py-0.5 text-[10px] bg-indigo-50 text-indigo-600 rounded">{kw}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-2 border-t border-gray-50">
        <button
          onClick={() => onViewGraph?.(result.id, profile.full_name)}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3" /><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4" /></svg>
          Graph
        </button>
        <button
          onClick={() => onFindSimilar?.(result.id, profile.full_name)}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /><path d="M3 21v-2a4 4 0 013-3.87" /></svg>
          Similar
        </button>
        <button
          onClick={() => onConnect?.({
            name: profile.full_name,
            phone: profile.phone,
            email: profile.email,
            role: `${profile.current_role} at ${profile.current_company}`,
          })}
          className="flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 A19.5 19.5 0 013.07 9.81 19.79 19.79 0 01.22 1.18 2 2 0 012.2 0h3a2 2 0 012 1.72c.127.96.36 1.903.7 2.81a2 2 0 01-.45 2.11L6.27 7.91a16 16 0 006.29 6.29l1.28-1.28a2 2 0 012.11-.45c.907.34 1.85.573 2.81.7A2 2 0 0122 16.92z" />
          </svg>
          Connect
        </button>
        <button
          onClick={() => onAddToCompare?.(profile)}
          className="flex items-center justify-center p-2 text-xs font-medium border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
          title="Add to Compare"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" /><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
        </button>
      </div>
    </div>
  );
}
