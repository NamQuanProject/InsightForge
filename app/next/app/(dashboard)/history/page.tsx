export default function History() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">History</h1>
        <p className="mt-1 text-gray-500">View and manage your past generated content</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Items</h2>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                placeholder="Search history..."
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <select className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <option>All Types</option>
                <option>Reports</option>
                <option>Content</option>
                <option>Analyses</option>
              </select>
            </div>
          </div>
        </div>

        <div className="divide-y divide-gray-100">
          <div className="px-6 py-4 hover:bg-gray-50 transition-colors">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex items-center space-x-4 flex-1">
                <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-lg">📄</span>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Q4 Sales Performance Report</h3>
                  <p className="text-sm text-gray-500">Generated on January 15, 2024 at 2:30 PM</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="px-2.5 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full">
                  Completed
                </span>
                <button className="text-indigo-600 hover:text-indigo-700 text-sm font-medium">
                  View
                </button>
              </div>
            </div>
          </div>

          <div className="px-6 py-4 hover:bg-gray-50 transition-colors">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex items-center space-x-4 flex-1">
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-lg">✍️</span>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Product Launch Blog Post - v2</h3>
                  <p className="text-sm text-gray-500">Generated on January 14, 2024 at 10:15 AM</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="px-2.5 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">
                  In Review
                </span>
                <button className="text-indigo-600 hover:text-indigo-700 text-sm font-medium">
                  View
                </button>
              </div>
            </div>
          </div>

          <div className="px-6 py-4 hover:bg-gray-50 transition-colors">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex items-center space-x-4 flex-1">
                <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-lg">📊</span>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Monthly User Analytics Summary</h3>
                  <p className="text-sm text-gray-500">Generated on January 12, 2024 at 4:45 PM</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="px-2.5 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full">
                  Completed
                </span>
                <button className="text-indigo-600 hover:text-indigo-700 text-sm font-medium">
                  View
                </button>
              </div>
            </div>
          </div>

          <div className="px-6 py-4 hover:bg-gray-50 transition-colors">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex items-center space-x-4 flex-1">
                <div className="w-10 h-10 bg-rose-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-lg">📄</span>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Competitor Analysis Report</h3>
                  <p className="text-sm text-gray-500">Generated on January 10, 2024 at 9:00 AM</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="px-2.5 py-1 bg-rose-100 text-rose-700 text-xs font-medium rounded-full">
                  Draft
                </span>
                <button className="text-indigo-600 hover:text-indigo-700 text-sm font-medium">
                  Continue
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
          <p className="text-sm text-gray-500">Showing 1-4 of 24 items</p>
          <div className="flex items-center space-x-2">
            <button className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-50 disabled:opacity-50">
              Previous
            </button>
            <button className="px-3 py-1 bg-indigo-600 text-white rounded-md text-sm">1</button>
            <button className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-50">2</button>
            <button className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-50">3</button>
            <button className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-50">
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}