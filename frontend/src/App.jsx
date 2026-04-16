import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import NetworkPage from './pages/NetworkPage';
import ProfileModal from './components/shared/ProfileModal';
import ConnectModal from './components/shared/ConnectModal';
import BookmarksPanel from './components/shared/BookmarksPanel';
import CommandPalette from './components/shared/CommandPalette';
import CompareTray from './components/shared/CompareTray';
import CompareModal from './components/shared/CompareModal';
import { ToastProvider, useToast } from './components/shared/Toast';
import { useStats } from './hooks/useStats';

function AppContent() {
  const [profileId, setProfileId] = useState(null);
  const [connectAlumni, setConnectAlumni] = useState(null);
  const [bookmarksOpen, setBookmarksOpen] = useState(false);
  const [compareQueue, setCompareQueue] = useState([]);
  const [compareModalOpen, setCompareModalOpen] = useState(false);
  const navigate = useNavigate();
  const { stats } = useStats();
  const { addToast } = useToast();

  // Navigation handlers to pass to deep components
  const handleViewGraph = (id, name) => {
    navigate(`/network?id=${id}&name=${encodeURIComponent(name)}`);
  };

  const handleFindSimilar = (id, name) => {
    navigate(`/network?id=${id}&name=${encodeURIComponent(name)}`);
  };

  const handleAddToCompare = (profile) => {
    setCompareQueue(prev => {
      if (prev.find(p => p.alumnus_id === profile.alumnus_id)) return prev;
      if (prev.length >= 3) {
        addToast('You can only compare up to 3 profiles at once.', 'info');
        return prev;
      }
      addToast(`Added ${profile.full_name} to comparison.`, 'success');
      return [...prev, profile];
    });
  };

  return (
    <div className="flex flex-col min-h-screen text-gray-900 selection:bg-indigo-100 selection:text-indigo-900">
      <Header stats={stats} onOpenBookmarks={() => setBookmarksOpen(true)} />

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/search"
            element={
              <SearchPage
                onOpenProfile={setProfileId}
                onViewGraph={handleViewGraph}
                onFindSimilar={handleFindSimilar}
                onConnect={setConnectAlumni}
                onAddToCompare={handleAddToCompare}
              />
            }
          />
          <Route
            path="/network"
            element={<NetworkPage onOpenProfile={setProfileId} />}
          />
        </Routes>
      </main>

      <Footer />

      {/* Global Modals/Panels */}
      <ProfileModal
        alumniId={profileId}
        onClose={() => setProfileId(null)}
        onViewGraph={handleViewGraph}
        onFindSimilar={handleFindSimilar}
      />

      <ConnectModal
        alumni={connectAlumni}
        onClose={() => setConnectAlumni(null)}
      />

      <BookmarksPanel
        isOpen={bookmarksOpen}
        onClose={() => setBookmarksOpen(false)}
        onOpenProfile={setProfileId}
      />

      <CommandPalette onOpenProfile={setProfileId} />

      <CompareTray
        selected={compareQueue.map(p => ({ id: p.alumnus_id, name: p.full_name }))}
        onRemove={(id) => setCompareQueue(prev => prev.filter(p => p.alumnus_id !== id))}
        onClear={() => setCompareQueue([])}
        onCompare={() => setCompareModalOpen(true)}
      />

      <CompareModal
        isOpen={compareModalOpen}
        onClose={() => setCompareModalOpen(false)}
        selectedProfiles={compareQueue}
      />
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </Router>
  );
}
