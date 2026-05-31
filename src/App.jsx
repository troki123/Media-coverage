import { useState, useEffect } from 'react'

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [query, setQuery] = useState(''); 
  const [loading, setLoading] = useState(false); 
  const [newsList, setNewsList] = useState([]);

  // --- NEW STATE FOR SQLITE REAL METRICS ---
  const [analytics, setAnalytics] = useState({
    totalSearches: 0,
    totalSources: 0,
    status: 'Loading...'
  });
  const [dbHistory, setDbHistory] = useState([]);

  // --- FETCH REAL-TIME ANALYTICS FROM FLASK ---
  const fetchAnalyticsData = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/analytics');
      const data = await response.json();
      if (data) {
        setAnalytics({
          totalSearches: data.total_searches ?? 0,
          totalSources: data.total_sources ?? 0,
          status: data.status || 'Connected'
        });
      }
    } catch (error) {
      console.error("Error connecting to analytics API:", error);
      setAnalytics(prev => ({ ...prev, status: 'Connection Failed' }));
    }
  };

  // --- FETCH HISTORICAL CLI QUERY LOGS ---
  const fetchSourcesHistory = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/sources');
      const data = await response.json();
      if (Array.isArray(data)) {
        setDbHistory(data);
      }
    } catch (error) {
      console.error("Error connecting to sources API:", error);
    }
  };

  // Trigger data synchronization when structural tabs mount
  useEffect(() => {
    fetchAnalyticsData();
    fetchSourcesHistory();
  }, [activeTab]);

  // --- LIVE WEB SEARCH LOGIC (DASHBOARD) ---
  const handleSearch = async (e) => {
    if (e) e.preventDefault(); 
    if (!query.trim()) return; 

    setLoading(true); 
    try {
      const response = await fetch(`http://127.0.0.1:5000/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      
      if (data && data.articles) {
        const formattedArticles = data.articles.map((art, index) => ({
          id: index,
          title: art.title || "Analyzed Article",
          summary: art.description || "No summary available for this article.",
          source: art.source || "Media Source",
          url: art.url || "#"
        }));
        
        setNewsList(formattedArticles);
        // Silently refresh numbers after a successful dashboard hit
        fetchAnalyticsData();
      }
    } catch (error) {
      console.error("Error fetching data from backend:", error);
    } finally {
      setLoading(false); 
    }
  };

  return (
    <div className={darkMode ? 'dark' : ''}> 
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors duration-300">
        
        {/* --- NAVBAR --- */}
        <nav className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
          <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-blue-200 dark:shadow-none">
                M
              </div>
              <span className="text-xl font-bold tracking-tight text-gray-800 dark:text-white">
                Media<span className="text-blue-600">Analyzer</span>
              </span>
            </div>

            <div className="hidden md:flex items-center gap-8 text-sm font-medium">
              {['Dashboard', 'Analytics', 'Sources'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`cursor-pointer transition-colors ${
                    activeTab === tab 
                      ? 'text-blue-600 dark:text-blue-400' 
                      : 'text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <button 
              onClick={() => setDarkMode(!darkMode)}
              className="cursor-pointer bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 p-2.5 rounded-xl transition-all text-xl"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </nav>

        {/* --- MAIN CONTENT --- */}
        <main className="max-w-4xl mx-auto px-4 pt-12 pb-20">
          
          {/* 1. DASHBOARD VIEW */}
          {activeTab === 'Dashboard' && (
            <>
              <div className="text-center mb-12">
                <h1 className="text-4xl font-extrabold text-gray-900 dark:text-white mb-4">Discover Global Insights</h1>
                <p className="text-gray-500 dark:text-gray-400 mb-8">Search and analyze news from around the world in real-time.</p>
                
                <form onSubmit={handleSearch} className="relative max-w-2xl mx-auto">
                  <input 
                    type="text" 
                    placeholder="Search news and trigger Gemini analysis..." 
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={loading}
                    className="w-full p-4 pl-12 pr-24 rounded-2xl bg-white dark:bg-gray-900 shadow-xl border border-gray-100 dark:border-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all disabled:opacity-50" 
                  />
                  <span className="absolute left-4 top-4 text-xl opacity-50">🔍</span>
                  
                  <button 
                    type="submit" 
                    disabled={loading}
                    className={`absolute right-3 top-3 text-white text-xs font-semibold px-4 py-2 rounded-xl transition-all ${
                      loading ? 'bg-gray-400 dark:bg-gray-700 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 cursor-pointer'
                    }`}
                  >
                    {loading ? 'Analyzing...' : 'Search'}
                  </button>
                </form>
              </div>

              <div className="grid gap-6">
                <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-2">Latest Updates</h2>
                
                {loading ? (
                  <div className="text-center py-16 bg-white dark:bg-gray-900 rounded-3xl border border-gray-100 dark:border-gray-800 shadow-sm flex flex-col items-center justify-center">
                    <div className="w-10 h-10 border-4 border-blue-600/20 border-l-blue-600 rounded-full animate-spin mb-4"></div>
                    <p className="text-gray-900 dark:text-white font-medium">Scanning the web...</p>
                    <p className="text-gray-400 dark:text-gray-500 text-xs mt-1">Gemini AI is generating structured article analysis</p>
                  </div>
                ) : newsList.length === 0 ? (
                  <div className="text-center py-12 bg-white dark:bg-gray-900 rounded-3xl border border-gray-100 dark:border-gray-800">
                    <p className="text-gray-500 dark:text-gray-400">Enter a query to stream and structure media reports.</p>
                  </div>
                ) : (
                  newsList.map((news) => (
                    <div key={news.id} className="group bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-100 dark:border-gray-800 shadow-sm hover:shadow-xl dark:hover:shadow-blue-900/20 hover:-translate-y-1 transition-all duration-300">
                      <div className="flex justify-between items-start mb-3">
                        <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950 px-3 py-1 rounded-full">{news.source}</span>
                        <span className="text-gray-400 dark:text-gray-500 text-xs">Verified Result</span>
                      </div>
                      <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{news.title}</h3>
                      <p className="text-gray-600 dark:text-gray-400 leading-relaxed whitespace-pre-line text-sm">{news.summary}</p>
                      <a 
                        href={news.url} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="mt-4 inline-flex items-center text-blue-600 dark:text-blue-400 font-semibold text-sm hover:underline"
                      >
                        Read Full Article <span className="ml-1 group-hover:ml-2 transition-all">→</span>
                      </a>
                    </div>
                  ))
                )}
              </div>
            </>
          )}

          {/* 2. ANALYTICS VIEW */}
          {activeTab === 'Analytics' && (
            <div className="animate-fadeIn">
              <h2 className="text-3xl font-bold mb-8">System Analytics</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-100 dark:border-gray-800">
                  <p className="text-gray-500 text-sm font-medium">Total SQLite Searches</p>
                  <p className="text-4xl font-extrabold text-blue-600 mt-2"> {analytics.totalSearches} </p>
                </div>
                <div className="bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-100 dark:border-gray-800">
                  <p className="text-gray-500 text-sm font-medium">Gemini Filtered Sources</p>
                  <p className="text-4xl font-extrabold text-green-500 mt-2"> {analytics.totalSources} </p>
                </div>
                <div className="bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-100 dark:border-gray-800">
                  <p className="text-gray-500 text-sm font-medium">Database Status</p>
                  <p className={`text-2xl font-extrabold mt-3 ${analytics.status === 'Connected' ? 'text-purple-500' : 'text-red-500'}`}>
                    {analytics.status}
                  </p>
                </div>
              </div>
              <div className="mt-12 p-8 bg-white dark:bg-gray-900 rounded-3xl border border-gray-100 dark:border-gray-800 text-center shadow-sm">
                <p className="text-gray-400 dark:text-gray-500 text-sm">✓ Live database synchronization active with SQLite engine.</p>
              </div>
            </div>
          )}

          {/* 3. SOURCES & ECOSYSTEM VIEW */}
          {activeTab === 'Sources' && (
            <div className="animate-fadeIn">
              <div className="mb-8">
                <h2 className="text-3xl font-bold mb-2">Data & AI Ecosystem</h2>
                <p className="text-gray-500 dark:text-gray-400">MediaAnalyzer aggregates data and processes intelligence using world-class providers.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <div className="bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-100 dark:border-gray-800 shadow-sm">
                  <div className="w-12 h-12 bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 rounded-2xl flex items-center justify-center text-xl mb-4">🌐</div>
                  <h3 className="font-bold text-lg mb-1">NewsAPI Index</h3>
                  <p className="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-3">Data Ingestion</p>
                  <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">
                    Provides live access to global outlets, aggregating unstructured news data in real time based on user criteria.
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-100 dark:border-gray-800 shadow-sm">
                  <div className="w-12 h-12 bg-green-50 dark:bg-green-950 text-green-600 dark:text-green-400 rounded-2xl flex items-center justify-center text-xl mb-4">🤖</div>
                  <h3 className="font-bold text-lg mb-1">Google Gemini AI</h3>
                  <p className="text-xs font-semibold text-green-500 mb-3">Intelligence Layer</p>
                  <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">
                    Utilizes the <code className="text-xs bg-gray-100 dark:bg-gray-800 p-1 rounded">gemini-2.5-flash</code> model to evaluate descriptions and filter clickbait.
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-100 dark:border-gray-800 shadow-sm">
                  <div className="w-12 h-12 bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400 rounded-2xl flex items-center justify-center text-xl mb-4">📦</div>
                  <h3 className="font-bold text-lg mb-1">SQLite Cache</h3>
                  <p className="text-xs font-semibold text-purple-500 mb-3">Persistence Layer</p>
                  <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">
                    Handles relational data persistence, storing execution metadata inside local <code className="text-xs bg-gray-100 dark:bg-gray-800 p-1 rounded">database/app.db</code> logs.
                  </p>
                </div>
              </div>

              {/* --- DYNAMIC LIVE RECORDS FROM SQLITE --- */}
              <div className="bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-100 dark:border-gray-800 shadow-sm">
                <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Recent Database Queries (CLI History)</h3>
                
                {dbHistory.length === 0 ? (
                  <p className="text-gray-500 dark:text-gray-400 text-sm italic">No search execution logs found inside SQLite. Run news_search.py first!</p>
                ) : (
                  <div className="space-y-6">
                    {dbHistory.map((batch) => (
                      <div key={batch.id} className="border-l-2 border-blue-500 pl-4 py-1">
                        <div className="flex justify-between items-center mb-2">
                          <h4 className="font-bold text-gray-800 dark:text-gray-200">{batch.query}</h4>
                          <span className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-gray-500">{batch.sources_count} links saved</span>
                        </div>
                        <ul className="space-y-2">
                          {batch.articles.map((art, idx) => (
                            <li key={idx} className="text-sm">
                              <a 
                                href={art.url} 
                                target="_blank" 
                                rel="noopener noreferrer" 
                                className="text-blue-500 hover:underline inline-block truncate max-w-2xl"
                              >
                                {art.title}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>
          )}

        </main>
      </div>
    </div>
  )
}

export default App