export default function Approvals() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="px-6 py-8 bg-white shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">
            Approvals
          </h1>
          <a href="/dashboard" className="text-indigo-600 hover:text-indigo-700">
            ← Back to Dashboard
          </a>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Pending Approvals
            </h2>
            <p className="text-gray-600">
              Reports waiting for your review.
            </p>
          </div>
          
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Approval History
            </h2>
            <p className="text-gray-600">
              Track your past approvals and rejections.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}