import React from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import HomePage from './pages/HomePage'
import JobPage from './pages/JobPage'
import HistoryPage from './pages/HistoryPage'

function Navigation() {
  const location = useLocation()
  
  const isActive = (path) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }
  
  return (
    <nav className="bg-dark-secondary border-b border-dark-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-3">
              <img 
                src="/geodev-logo.jpeg" 
                alt="GEODEV" 
                className="h-10 w-10 rounded-lg object-cover"
              />
              <span className="font-geodev text-2xl text-white tracking-wider">
                GEODEV
              </span>
            </Link>
          </div>
          
          {/* Navigation links */}
          <div className="flex items-center space-x-1">
            <Link
              to="/"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive('/') && location.pathname === '/'
                  ? 'bg-geodev-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-dark-card'
              }`}
            >
              New Job
            </Link>
            <Link
              to="/history"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive('/history')
                  ? 'bg-geodev-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-dark-card'
              }`}
            >
              History
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}

function Footer() {
  return (
    <footer className="bg-dark-secondary border-t border-dark-border mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-6 text-center">
        <p className="text-gray-500 text-sm">
          GEODEV © 2026 - Automated Survey Prediction
        </p>
      </div>
    </footer>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-dark-primary flex flex-col">
        <Navigation />
        
        <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/jobs/:jobId" element={<JobPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
        
        <Footer />
      </div>
    </BrowserRouter>
  )
}

export default App
