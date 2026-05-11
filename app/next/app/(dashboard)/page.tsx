export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="px-6 py-8 bg-white shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">
            InsightForge
          </h1>
          <nav className="flex space-x-4">
            <a href="/dashboard" className="text-gray-600 hover:text-gray-900">
              Generate
            </a>
            <a href="/dashboard/history" className="text-gray-600 hover:text-gray-900">
              History
            </a>
            <a href="/dashboard/approvals" className="text-gray-600 hover:text-gray-900">
              Approvals
            </a>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="space-y-8">
          <div className="text-center py-16">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Welcome to InsightForge
            </h2>
            <p className="text-gray-600 max-w-xl mx-auto">
              Transform your data into actionable insights with our AI-powered analytics platform.
            </p>
            <div className="mt-8 flex justify-center space-x-4">
              <a href="/dashboard" className="px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors">
                Start Generating
              </a>
              <a href="/dashboard/history" className="px-6 py-3 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">
                View History
              </a>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
              <h3 className="font-semibold text-gray-900 mb-3">Generate Insights</h3>
              <p className="text-gray-600">
                Create custom reports and visualizations from your data sources.
              </p>
            </div>
            
            <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
              <h3 className="font-semibold text-gray-900 mb-3">Historical Analysis</h3>
              <p className="text-gray-600">
                Review past reports and track performance trends over time.
              </p>
            </div>
            
            <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
              <h3 className="font-semibold text-gray-900 mb-3">Approval Workflow</h3>
              <p className="text-gray-600">
                Collaborate with team members and approve reports before publishing.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}