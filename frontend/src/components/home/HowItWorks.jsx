import React from 'react';
import { Brain, Network, GitMerge } from 'lucide-react';

export default function HowItWorks() {
  const pillars = [
    {
      title: "Semantic Vector Search",
      description: "We use SBERT to convert alumni profiles into 384-dimensional vectors, allowing users to search by true intent and meaning (not just rigid keywords).",
      icon: <Brain className="w-5 h-5 text-indigo-600" />,
      badge: "AI Embeddings",
    },
    {
      title: "Graph Relationship Traversal",
      description: "Alumni are mapped into a property graph (Neo4j) to track real-world connections—mentorships, batch years, and shared companies—scoring nodes based on network centrality.",
      icon: <Network className="w-5 h-5 text-indigo-600" />,
      badge: "Network Graph",
    },
    {
      title: "The Hybrid Reranker",
      description: "Our fusion model intelligently combines the semantic match score with the graph traversal score to deliver highly precise, context-aware, and ranked results.",
      icon: <GitMerge className="w-5 h-5 text-indigo-600" />,
      badge: "Scoring Engine",
    }
  ];

  return (
    <section className="py-20 px-4 bg-gray-50 border-t border-gray-100">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-sm font-bold text-indigo-600 tracking-wider uppercase mb-3">The Engine</h2>
          <h3 className="text-3xl font-bold text-gray-900 tracking-tight mb-4">How our search pipeline works</h3>
          <p className="text-base text-gray-500 leading-relaxed">
            We combine large language models with graph traversal algorithms to understand the nuance behind your queries and rank results based on real-world connections.
          </p>
        </div>

        {/* 3-Column Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {pillars.map((pillar, index) => (
            <div 
              key={index} 
              className="bg-white rounded-2xl p-8 border border-gray-100 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group"
            >
              {/* Subtle top border accent */}
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500/0 via-indigo-500/20 to-indigo-500/0 opacity-0 group-hover:opacity-100 transition-opacity" />
              
              <div className="flex items-center justify-between mb-6">
                <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-100/50 flex items-center justify-center">
                  {pillar.icon}
                </div>
                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider bg-gray-50 px-3 py-1 rounded-full">
                  {pillar.badge}
                </span>
              </div>
              
              <h4 className="text-lg font-bold text-gray-900 mb-3">{pillar.title}</h4>
              <p className="text-sm text-gray-500 leading-relaxed">
                {pillar.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
