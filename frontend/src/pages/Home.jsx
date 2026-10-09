import { useEffect, useState } from 'react'
import { getHealth } from '../services/api'

function Home() {
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    let active = true

    getHealth()
      .then((data) => {
        if (active) setStatus(data.status)
      })
      .catch(() => {
        if (active) setStatus('offline')
      })

    return () => {
      active = false
    }
  }, [])

  return (
    <section className="space-y-6">
      <div className="space-y-3">
        <h1 className="text-4xl font-semibold tracking-tight text-white">
          Earth System Trend Detective
        </h1>
        <p className="max-w-2xl text-lg text-slate-300">
          React and Tailwind CSS frontend for exploring Earth system trends.
          The API client talks to the FastAPI backend through the Vite proxy.
        </p>
      </div>
      <div className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900 px-4 py-2 text-sm">
        <span
          className={`h-2 w-2 rounded-full ${
            status === 'ok' ? 'bg-emerald-400' : 'bg-amber-400'
          }`}
        />
        <span>API status: {status}</span>
      </div>
    </section>
  )
}

export default Home
