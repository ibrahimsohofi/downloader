import { useState } from 'react';
import Header from './components/Header';
import SearchBar from './components/SearchBar';
import VideoGrid from './components/VideoGrid';
import DownloadHistory from './components/DownloadHistory';

function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [platform, setPlatform] = useState('youtube');

  const handleSearch = async (query) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/search/${platform}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, page: 1 }),
      });

      const data = await response.json();
      setVideos(data.data?.items || []);
    } catch (error) {
      console.error('Search error:', error);
      setVideos([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (video) => {
    try {
      const response = await fetch('/api/download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: video.url,
          title: video.title,
          thumbnail: video.thumbnail,
          platform: platform,
          videoId: video.id,
          duration: video.duration,
          viewCount: video.view_count,
        }),
      });

      const data = await response.json();

      if (data.success) {
        alert('Download started! Check the History tab for progress.');
      } else {
        alert('Download failed: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Download error:', error);
      alert('Download failed: ' + error.message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="container mx-auto px-4 py-8">
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab('search')}
            className={`px-6 py-2 rounded-lg font-medium transition ${
              activeTab === 'search'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Search
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-6 py-2 rounded-lg font-medium transition ${
              activeTab === 'history'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Download History
          </button>
        </div>

        {activeTab === 'search' ? (
          <>
            <SearchBar
              onSearch={handleSearch}
              loading={loading}
              platform={platform}
              setPlatform={setPlatform}
            />
            <VideoGrid
              videos={videos}
              onDownload={handleDownload}
              loading={loading}
            />
          </>
        ) : (
          <DownloadHistory />
        )}
      </div>
    </div>
  );
}

export default App;
