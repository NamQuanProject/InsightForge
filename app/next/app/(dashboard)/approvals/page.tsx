export default function Approvals() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Approval Queue</h1>
        <p className="mt-1 text-gray-500">Review and manage content waiting for approval</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Pending Review</p>
              <p className="text-2xl font-bold text-amber-600 mt-1">3</p>
            </div>
            <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
              <span className="text-lg">⏳</span>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Approved This Week</p>
              <p className="text-2xl font-bold text-emerald-600 mt-1">12</p>
            </div>
            <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
              <span className="text-lg">✓</span>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Rejected This Week</p>
              <p className="text-2xl font-bold text-rose-600 mt-1">1</p>
            </div>
            <div className="w-10 h-10 bg-rose-100 rounded-full flex items-center justify-center">
              <span className="text-lg">✗</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Pending Your Review</h2>
        </div>

        <div className="divide-y divide-gray-100">
          <div className="px-6 py-5 hover:bg-gray-50 transition-colors">
            <div className="flex flex-col lg:flex-row lg:items-start gap-4">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">
                    Urgent
                  </span>
                  <span className="text-xs text-gray-500">Submitted 2 hours ago</span>
                </div>
                <h3 className="font-semibold text-gray-900 text-lg">Q4 Sales Performance Report - Final</h3>
                <p className="text-sm text-gray-600 mt-1 max-w-2xl">
                  Comprehensive sales analysis including revenue breakdown, top performing products, and regional comparisons. 
                  Ready for executive review.
                </p>
                <div className="flex items-center space-x-4 mt-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 bg-gray-200 rounded-full" />
                    <span className="text-sm text-gray-600">Submitted by John Doe</span>
                  </div>
                  <span className="text-sm text-gray-500">•</span>
                  <span className="text-sm text-gray-600">Type: Report</span>
                </div>
              </div>
              <div className="flex items-center space-x-3 lg:flex-col lg:items-end">
                <button className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition-colors text-sm font-medium">
                  Approve
                </button>
                <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors text-sm font-medium">
                  Review
                </button>
                <button className="px-4 py-2 text-rose-600 hover:text-rose-700 transition-colors text-sm font-medium">
                  Reject
                </button>
              </div>
            </div>
          </div>

          <div className="px-6 py-5 hover:bg-gray-50 transition-colors">
            <div className="flex flex-col lg:flex-row lg:items-start gap-4">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-xs text-gray-500">Submitted 5 hours ago</span>
                </div>
                <h3 className="font-semibold text-gray-900 text-lg">Product Launch Blog Post - "Introducing AI Features"</h3>
                <p className="text-sm text-gray-600 mt-1 max-w-2xl">
                  Blog post announcing the new AI-powered features. Includes product screenshots, customer testimonials, 
                  and technical overview.
                </p>
                <div className="flex items-center space-x-4 mt-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 bg-gray-200 rounded-full" />
                    <span className="text-sm text-gray-600">Submitted by Sarah Chen</span>
                  </div>
                  <span className="text-sm text-gray-500">•</span>
                  <span className="text-sm text-gray-600">Type: Content</span>
                </div>
              </div>
              <div className="flex items-center space-x-3 lg:flex-col lg:items-end">
                <button className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition-colors text-sm font-medium">
                  Approve
                </button>
                <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors text-sm font-medium">
                  Review
                </button>
                <button className="px-4 py-2 text-rose-600 hover:text-rose-700 transition-colors text-sm font-medium">
                  Reject
                </button>
              </div>
            </div>
          </div>

          <div className="px-6 py-5 hover:bg-gray-50 transition-colors">
            <div className="flex flex-col lg:flex-row lg:items-start gap-4">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-xs font-medium rounded-full">
                    New
                  </span>
                  <span className="text-xs text-gray-500">Submitted yesterday</span>
                </div>
                <h3 className="font-semibold text-gray-900 text-lg">Monthly User Analytics - December 2024</h3>
                <p className="text-sm text-gray-600 mt-1 max-w-2xl">
                  Key metrics dashboard including MAU, DAU, retention rates, and feature adoption analysis. 
                  Comparison with previous month included.
                </p>
                <div className="flex items-center space-x-4 mt-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 bg-gray-200 rounded-full" />
                    <span className="text-sm text-gray-600">Submitted by Mike Johnson</span>
                  </div>
                  <span className="text-sm text-gray-500">•</span>
                  <span className="text-sm text-gray-600">Type: Analysis</span>
                </div>
              </div>
              <div className="flex items-center space-x-3 lg:flex-col lg:items-end">
                <button className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition-colors text-sm font-medium">
                  Approve
                </button>
                <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors text-sm font-medium">
                  Review
                </button>
                <button className="px-4 py-2 text-rose-600 hover:text-rose-700 transition-colors text-sm font-medium">
                  Reject
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}