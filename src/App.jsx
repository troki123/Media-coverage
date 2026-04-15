import { useState } from 'react'

function App() {
  const [darkMode, setDarkMode] = useState(() => {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
});
  const [newsList, setNewsList] = useState([
    {
      id: 1,
      title: "New AI Model Released",
      summary: "A new breakthrough in artificial intelligence has been announced today...",
      source: "TechDaily"
    },
    {
      id: 2,
      title: "Global Markets Update",
      summary: "Stock markets showing positive trends after the recent economic report...",
      source: "FinanceWeekly"
    }
  ]);

  return (
    <div className={darkMode ? 'dark' : ''}> 
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 ...">
        
        {/* --- NAVBAR --- */}
        <nav className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
          <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-blue-200 dark:shadow-none">
                M
              </div>
              <span className="text-xl font-bold tracking-tight text-gray-800 dark:text-white">
                Media<span className="text-blue-600">Analyzer</span>
              </span>
            </div>

            {/* Nav Links */}
            <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-600 dark:text-gray-400">
              <a href="#" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Dashboard</a>
              <a href="#" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Analytics</a>
              <a href="#" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Sources</a>
            </div>

            {/* Dark Mode Toggle - Zamjena za profil */}
            <button 
              onClick={() => setDarkMode(!darkMode)}
              className="bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 p-2.5 rounded-xl transition-all text-xl"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </nav>

        {/* --- MAIN CONTENT --- */}
        <main className="max-w-4xl mx-auto px-4 pt-12 pb-20">
          
          {/* Header & Search Bar */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-extrabold text-gray-900 dark:text-white mb-4">
              Discover Global Insights
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mb-8">Search and analyze news from around the world in real-time.</p>
            
            <div className="relative max-w-2xl mx-auto">
              <input 
                type="text" 
                placeholder="Search news, topics or sources..." 
                className="w-full p-4 pl-12 rounded-2xl bg-white dark:bg-gray-900 shadow-xl shadow-gray-100 dark:shadow-none border border-gray-100 dark:border-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              />
              <span className="absolute left-4 top-4.5 text-xl opacity-50">🔍</span>
            </div>
          </div>

          {/* News Feed */}
          <div className="grid gap-6">
            <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-2">Latest Updates</h2>
            {newsList.map((news) => (
              <div 
                key={news.id} 
                className="group bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-100 dark:border-gray-800 shadow-sm hover:shadow-xl dark:hover:shadow-blue-900/20 hover:-translate-y-1 transition-all duration-300"
              >
                <div className="flex justify-between items-start mb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950 px-3 py-1 rounded-full">
                    {news.source}
                  </span>
                  <span className="text-gray-400 dark:text-gray-500 text-xs">2h ago</span>
                </div>
                <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {news.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  {news.summary}
                </p>
                <div className="mt-4 flex items-center text-blue-600 dark:text-blue-400 font-semibold text-sm cursor-pointer">
                  Read Analysis <span className="ml-1 group-hover:ml-2 transition-all">→</span>
                </div>
              </div>
            ))}
          </div>
        </main>

      </div>
    </div>
  )
}

export default App