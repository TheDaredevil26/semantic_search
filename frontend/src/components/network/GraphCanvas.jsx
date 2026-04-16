import { useEffect, useRef } from 'react';
import { Network } from 'vis-network';

/**
 * GraphCanvas — Interactive wrapper around vis.js for graph visualization.
 */
export default function GraphCanvas({ graphData, onNodeDoubleClick, clusterBy }) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    // Transform API graph data to vis.js format and apply light-theme styling
    const nodes = (graphData.nodes || []).map(entry => {
      const isAlumni = (entry.group || '').toLowerCase() === 'alumni';
      const colorMap = {
        alumni: { bg: '#EEF2FF', border: '#A5B4FC', hiBg: '#E0E7FF', hiBorder: '#818CF8' },
        company: { bg: '#ECFDF5', border: '#6EE7B7', hiBg: '#D1FAE5', hiBorder: '#34D399' },
        skill: { bg: '#FFFBEB', border: '#FCD34D', hiBg: '#FEF3C7', hiBorder: '#FBBF24' },
        department: { bg: '#FAF5FF', border: '#D8B4FE', hiBg: '#F3E8FF', hiBorder: '#C084FC' },
        batch: { bg: '#EFF6FF', border: '#93C5FD', hiBg: '#DBEAFE', hiBorder: '#60A5FA' },
        mentor: { bg: '#FDF2F8', border: '#F9A8D4', hiBg: '#FCE7F3', hiBorder: '#F472B6' },
        location: { bg: '#FEF2F2', border: '#FCA5A5', hiBg: '#FEE2E2', hiBorder: '#F87171' },
        default: { bg: '#F3F4F6', border: '#D1D5DB', hiBg: '#E5E7EB', hiBorder: '#9CA3AF' }
      };
      
      const c = colorMap[(entry.group || '').toLowerCase()] || colorMap.default;

      return {
        id: entry.id,
        label: isAlumni ? (entry.name || entry.label) : entry.id.substring(0, 15) + (entry.id.length > 15 ? '...' : ''),
        group: entry.group,
        title: entry.title || entry.id,
        // Override default styles for light theme
        color: {
          background: c.bg,
          border: c.border,
          highlight: {
            background: c.hiBg,
            border: c.hiBorder
          }
        },
        font: {
          color: '#374151',
          face: 'Inter, sans-serif'
        },
        size: isAlumni ? 25 : 15,
        borderWidth: 2,
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.05)',
          size: 10,
          x: 2,
          y: 2
        }
      };
    });

    const edges = (graphData.edges || []).map(entry => ({
      from: entry.from || entry.source, // allow either backend format
      to: entry.to || entry.target,
      label: entry.label || entry.relation,
      font: { 
        align: 'middle', 
        size: 10, 
        color: '#4B5563', 
        face: 'Inter',
        strokeWidth: 2,
        strokeColor: '#FFFFFF'
      },
      color: { color: '#9CA3AF', highlight: '#6366F1' },
      arrows: { to: { enabled: true, scaleFactor: 0.6 } },
      length: 200,
    }));

    const data = { nodes, edges };
    const options = {
      nodes: {
        shape: 'dot',
      },
      edges: {
        smooth: { type: 'continuous' }
      },
      physics: {
        barnesHut: {
          gravitationalConstant: -35000,
          centralGravity: 0.3,
          springLength: 250,
          springConstant: 0.04,
          damping: 0.09
        },
        stabilization: { iterations: 150 }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
        dragView: true
      }
    };

    networkRef.current = new Network(containerRef.current, data, options);

    // Double click event handling
    networkRef.current.on('doubleClick', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = nodes.find(n => n.id === nodeId);
        if (node && onNodeDoubleClick) {
          onNodeDoubleClick(nodeId, node.group);
        }
      }
    });

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [graphData, onNodeDoubleClick]);

  useEffect(() => {
    if (!networkRef.current) return;

    // First uncluster everything
    const clusterNodes = networkRef.current.body.nodeIndices.filter(id => id.toString().startsWith('cluster_'));
    for (const cid of clusterNodes) {
      if (networkRef.current.isCluster(cid)) {
        networkRef.current.openCluster(cid);
      }
    }

    if (clusterBy) {
       const clusterOptionsByData = {
          joinCondition: function (childOptions) {
             return (childOptions.group || '').toLowerCase() === clusterBy;
          },
          processProperties: function (clusterOptions, childNodes) {
             let totalMass = 0;
             for (let i = 0; i < childNodes.length; i++) {
                 totalMass += childNodes[i].mass;
             }
             clusterOptions.mass = totalMass;
             return clusterOptions;
          },
          clusterNodeProperties: {
             id: 'cluster_' + clusterBy + '_' + Math.random(),
             borderWidth: 3,
             shape: 'hexagon',
             color: {
                background: '#E0E7FF',
                border: '#6366F1'
             },
             label: `Grouped ${clusterBy}s`,
             size: 40,
             font: { size: 14, color: '#3730A3', bold: true }
          }
       };
       networkRef.current.cluster(clusterOptionsByData);
    }
  }, [clusterBy]);

  return (
    <div className="w-full h-full relative graph-canvas-container bg-white border border-gray-100 rounded-xl overflow-hidden shadow-sm">
      <div ref={containerRef} className="w-full h-full outline-none" />

      {/* Legend overlaid on canvas */}
      <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm border border-gray-100 rounded-lg p-3 text-[10px] shadow-sm pointer-events-none">
        <h4 className="font-semibold text-gray-700 mb-2 uppercase tracking-wide">Graph Legend</h4>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-indigo-100 border border-indigo-300" />
            <span className="text-gray-600">Alumni</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-emerald-100 border border-emerald-300" />
            <span className="text-gray-600">Company</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-blue-100 border border-blue-300" />
            <span className="text-gray-600">Skill</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-purple-100 border border-purple-300" />
            <span className="text-gray-600">Department</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-amber-100 border border-amber-300" />
            <span className="text-gray-600">Batch Year</span>
          </div>
        </div>
      </div>
    </div>
  );
}
