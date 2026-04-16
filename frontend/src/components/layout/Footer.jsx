/**
 * Footer — App footer with branding, tech stack, and links.
 */
export default function Footer() {
  const techStack = [
    { name: 'Sentence-BERT', color: '#4F46E5' },
    { name: 'FastAPI', color: '#059669' },
    { name: 'FAISS HNSW', color: '#3B82F6' },
    { name: 'NetworkX + PPR', color: '#D97706' },
    { name: 'Cross-Encoder', color: '#7C3AED' },
    { name: 'vis.js', color: '#EC4899' },
  ];

  return (
    <footer className="border-t border-gray-100 bg-white mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 rounded-md bg-indigo-600 flex items-center justify-center">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4" />
                </svg>
              </div>
              <span className="text-sm font-semibold text-gray-900">Alumni Graph Search</span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              AI-powered semantic search over alumni networks combining vector similarity and graph intelligence.
            </p>
          </div>

          {/* Tech Stack */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">Powered by</h4>
            <div className="flex flex-wrap gap-1.5">
              {techStack.map(tech => (
                <span key={tech.name} className="inline-flex items-center gap-1.5 text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded-md border border-gray-100">
                  <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: tech.color }} />
                  {tech.name}
                </span>
              ))}
            </div>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">Resources</h4>
            <div className="flex flex-col gap-1.5">
              <a href="/docs" target="_blank" rel="noopener noreferrer" className="text-xs text-gray-500 hover:text-indigo-600 transition-colors">
                API Documentation
              </a>
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-xs text-gray-500 hover:text-indigo-600 transition-colors">
                GitHub Repository
              </a>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-50 mt-6 pt-4 flex items-center justify-between">
          <p className="text-[11px] text-gray-300">Built with Semantic AI × Graph Intelligence × Cross-Encoder Reranking</p>
          <p className="text-[11px] text-gray-300">v2.0.0</p>
        </div>
      </div>
    </footer>
  );
}
