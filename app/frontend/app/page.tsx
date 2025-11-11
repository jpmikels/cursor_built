import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="max-w-5xl w-full text-center">
        <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
          Valuation Workbench
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Professional financial statement consolidation and business valuation platform
        </p>
        
        <div className="flex gap-4 justify-center">
          <Link href="/auth/login" className="btn-primary">
            Sign In
          </Link>
          <Link href="/auth/register" className="btn-secondary">
            Get Started
          </Link>
        </div>
        
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
          <div className="card">
            <h3 className="text-lg font-semibold mb-2">📄 Intelligent Document Processing</h3>
            <p className="text-gray-600">
              AI-powered parsing and normalization of financial statements from PDFs and Excel files.
            </p>
          </div>
          
          <div className="card">
            <h3 className="text-lg font-semibold mb-2">📊 Formula-Rich Workbooks</h3>
            <p className="text-gray-600">
              Generate consolidated Excel workbooks with linked schedules and audit trails.
            </p>
          </div>
          
          <div className="card">
            <h3 className="text-lg font-semibold mb-2">💰 Comprehensive Valuations</h3>
            <p className="text-gray-600">
              DCF, Guideline Public Company, and Guideline Transaction methodologies with market data.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}

