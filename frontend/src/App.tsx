import { useState } from 'react'
import { downloadScoutReportPdf } from './lib/exportReport'

export type Classification = {
  service_line: string
  confidence: number
  rationale: string
}

export type ScoutProfile = {
  id: string | null
  company_name: string
  note: string | null
  classification: Classification
  brief: string
  talking_points: string[]
  rationale: string
  reference_doc_ids: string[]
  low_confidence: boolean
}

export default function App() {
  const [companyName, setCompanyName] = useState('')
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [profile, setProfile] = useState<ScoutProfile | null>(null)

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setProfile(null)
    try {
      const response = await fetch('/scout/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_name: companyName, note: note || null }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail ?? `Request failed with status ${response.status}`)
      }
      setProfile(await response.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 py-10">
      <div className="mx-auto max-w-2xl px-4">
        <h1 className="text-2xl font-semibold text-slate-900">Scout</h1>
        <p className="mt-1 text-sm text-slate-500">
          Paste a company name to generate a research brief and discovery-call talking points.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="company_name" className="block text-sm font-medium text-slate-700">
              Company name
            </label>
            <input
              id="company_name"
              required
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-slate-500 focus:outline-none"
              placeholder="Enter a company name"
            />
          </div>
          <div>
            <label htmlFor="note" className="block text-sm font-medium text-slate-700">
              Note (optional)
            </label>
            <input
              id="note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-slate-500 focus:outline-none"
              placeholder="Inbound via HR contact, interested in Power BI training"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {loading ? 'Researching…' : 'Run Scout'}
          </button>
        </form>

        {error && (
          <div className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {profile && (
          <div className="mt-8 space-y-6">
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => downloadScoutReportPdf(profile, companyName)}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
              >
                Download PDF
              </button>
            </div>
            {profile.low_confidence && (
              <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                Low confidence: limited public information was found for this company. Treat this
                brief as a starting point, not a finished picture.
              </div>
            )}

            <div>
              <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500">Classification</h2>
              <p className="mt-1 text-base text-slate-900">
                {profile.classification.service_line}{' '}
                <span className="text-sm text-slate-500">
                  ({Math.round(profile.classification.confidence * 100)}% confidence)
                </span>
              </p>
            </div>

            <div>
              <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500">Brief</h2>
              <p className="mt-1 whitespace-pre-line text-sm text-slate-800">{profile.brief}</p>
            </div>

            <div>
              <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500">Why this angle fits</h2>
              <p className="mt-1 whitespace-pre-line text-sm text-slate-800">{profile.rationale}</p>
            </div>

            <div>
              <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500">Talking points</h2>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-800">
                {profile.talking_points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
