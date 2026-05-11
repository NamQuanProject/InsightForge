export default function Dashboard() {
  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Generate Content</h1>
          <p className="mt-1 text-gray-500">Create new AI-powered content and reports</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow border border-gray-100">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-2xl">📝</span>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 text-lg">New Report</h3>
              <p className="mt-1 text-gray-600 text-sm">
                Generate custom reports from your data sources with AI-powered insights.
              </p>
              <button className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors text-sm font-medium">
                Create Report
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow border border-gray-100">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-2xl">✍️</span>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 text-lg">Content Generator</h3>
              <p className="mt-1 text-gray-600 text-sm">
                Generate marketing copy, blog posts, and social media content.
              </p>
              <button className="mt-4 px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition-colors text-sm font-medium">
                Generate Content
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow border border-gray-100">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-2xl">📊</span>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 text-lg">Data Analysis</h3>
              <p className="mt-1 text-gray-600 text-sm">
                Upload datasets and get automated insights and visualizations.
              </p>
              <button className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 transition-colors text-sm font-medium">
                Analyze Data
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow border border-gray-100">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-rose-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-2xl">📋</span>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 text-lg">From Template</h3>
              <p className="mt-1 text-gray-600 text-sm">
                Use pre-built templates for common content types and reports.
              </p>
              <button className="mt-4 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors text-sm font-medium">
                Browse Templates
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-4">
          <div className="flex items-center space-x-4 p-3 rounded-lg hover:bg-gray-50 transition-colors">
            <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
              <span className="text-sm">📄</span>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">Q4 Sales Report</p>
              <p className="text-xs text-gray-500">Created 2 hours ago</p>
            </div>
            <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full">
              Completed
            </span>
          </div>
          <div className="flex items-center space-x-4 p-3 rounded-lg hover:bg-gray-50 transition-colors">
            <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center">
              <span className="text-sm">✍️</span>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">Product Launch Blog Post</p>
              <p className="text-xs text-gray-500">Created 5 hours ago</p>
            </div>
            <span className="px-2 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">
              Pending Review
            </span>
          </div>
          <div className="flex items-center space-x-4 p-3 rounded-lg hover:bg-gray-50 transition-colors">
            <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
              <span className="text-sm">📊</span>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">Monthly Analytics Summary</p>
              <p className="text-xs text-gray-500">Created yesterday</p>
            </div>
            <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full">
              Completed
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}