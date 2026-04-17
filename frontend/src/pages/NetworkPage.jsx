import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import GraphCanvas from '../components/network/GraphCanvas';
import SimilarPanel from '../components/network/SimilarPanel';
import PathFinder from '../components/network/PathFinder';
import { getAlumniGraph, getAlumniList } from '../api/client';
import { useToast } from '../components/shared/Toast';

export default function NetworkPage({ onOpenProfile }) {
  const [searchParams] = useSearchParams();
  const initialId = searchParams.get('id');
  const initialName = searchParams.get('name');

  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [centerNode, setCenterNode] = useState({ id: initialId, name: initialName });
  const { addToast } = useToast();

  const [rootQuery, setRootQuery] = useState('');
  const [rootList, setRootList] = useState([]);
  const [clusterBy, setClusterBy] = useState('');

  useEffect(() => {
    if (rootQuery.length > 2) {
      getAlumniList(rootQuery).then(data => setRootList(data.alumni || [])).catch(() => {});
    } else {
      setRootList([]);
    }
  }, [rootQuery]);

  useEffect(() => {
    if (initialId) {
      loadGraph(initialId);
    }
  }, [initialId]);

  async function loadGraph(id) {
    setLoading(true);
    try {
      const data = await getAlumniGraph(id);
      setGraphData(data);
    } catch (err) {
      addToast(`Failed to load graph: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  }

  function handleNodeDoubleClick(nodeId, type) {
    if (type === 'Alumni') {
      onOpenProfile(nodeId);
    } else {
      // For skill/company nodes, we could navigate to search page
      // navigate(`/search?q=${encodeURIComponent(nodeId)}`);
      addToast(`Showing connections for ${nodeId}`, 'info');
    }
  }

  function handleViewGraphFromPath(data) {
     setGraphData(data);
     setCenterNode({ id: null, name: 'Custom Path' });
  }

  return (
    <div className="flex flex-col h-[calc(100vh-57px)] max-w-1600px mx-auto px-4 py-4 gap-4 animate-fade-in">
      <div className="flex items-center justify-between" style={{ position: 'relative', zIndex: 99999 }}>
        <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
          Network Graph
          {centerNode.name && (
            <>
              <svg className="w-4 h-4 text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="9 18 15 12 9 6" />
              </svg>
              <span className="text-indigo-600 font-normal">{centerNode.name}</span>
            </>
          )}
        </h2>
        
        <div className="flex items-center gap-6">
          <select 
            value={clusterBy}
            onChange={(e) => setClusterBy(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-indigo-400 bg-white"
          >
             <option value="">No Clustering</option>
             <option value="company">Cluster by Company</option>
             <option value="department">Cluster by Department</option>
             <option value="skill">Cluster by Skill</option>
             <option value="batch">Cluster by Batch</option>
          </select>
          <div className="relative w-80 z-50">
            <input
              type="text"
              value={rootQuery}
              onChange={e => setRootQuery(e.target.value)}
              placeholder="Search alumni to center graph..."
              className="w-full px-4 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-100 placeholder:text-gray-400 bg-white shadow-sm"
            />
            {rootList.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-100 rounded-lg shadow-md max-h-64 overflow-y-auto z-50">
                {rootList.map(item => (
                  <div
                    key={item.id}
                    className="px-4 py-3 text-sm hover:bg-gray-50 cursor-pointer border-b border-gray-50 last:border-0 transition-colors"
                    onClick={() => {
                      setCenterNode({ id: item.id, name: item.name });
                      loadGraph(item.id);
                      setRootQuery('');
                      setRootList([]);
                    }}
                  >
                    <div className="font-medium text-gray-800">{item.name}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {item.department || 'Unknown Dept'} • {item.batch}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {loading && (
            <div className="flex items-center gap-2 text-sm text-gray-400 w-36">
              <div className="w-4 h-4 border-2 border-gray-200 border-t-indigo-600 rounded-full animate-spin" />
              Generating Network...
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-4 flex-1 min-h-0" style={{ position: 'relative', zIndex: 1 }}>
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          {/* Path Finder */}
          <PathFinder onViewGraph={handleViewGraphFromPath} />

          {/* Canvas */}
          <div className="flex-1 bg-white border border-gray-100 rounded-xl overflow-hidden shadow-sm relative min-h-[400px]">
            {graphData ? (
              <GraphCanvas graphData={graphData} onNodeDoubleClick={handleNodeDoubleClick} clusterBy={clusterBy} />
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-400 bg-gray-50/50">
                <svg className="w-16 h-16 text-gray-200 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                  <circle cx="18" cy="5" r="3" />
                  <circle cx="6" cy="12" r="3" />
                  <circle cx="18" cy="19" r="3" />
                  <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
                  <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
                </svg>
                <p>Search for an alumni or use PathFinder to construct a network graph.</p>
              </div>
            )}
          </div>
        </div>

        {/* Similar Sidebar */}
        <SimilarPanel
          alumniId={centerNode.id}
          onOpenProfile={onOpenProfile}
          onViewGraph={(id, name) => {
            setCenterNode({ id, name });
            loadGraph(id);
          }}
        />
      </div>
    </div>
  );
}
