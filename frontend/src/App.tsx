import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

type Classification = {
  service_line: string
  confidence: number
  rationale: string
}

type ScoutProfile = {
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
    <div className="min-h-screen bg-background">
      <header className="border-b border-border px-4 py-3 sm:px-6">
        <div className="mx-auto flex max-w-2xl items-center gap-2">
          <img src="/favicon.svg" alt="" className="h-6 w-6" />
          <span className="text-sm font-semibold tracking-tight text-foreground">Scout</span>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-6 sm:py-10">
        <Card>
          <CardHeader>
            <CardTitle>Research a company</CardTitle>
            <CardDescription>
              Paste a company name to generate a research brief and discovery-call talking points.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="company_name">Company name</Label>
                <Input
                  id="company_name"
                  required
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Enter a company name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="note">Note (optional)</Label>
                <Input
                  id="note"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Inbound via HR contact, interested in Power BI training"
                />
              </div>
              <Button type="submit" disabled={loading} className="w-full sm:w-auto">
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Researching…
                  </>
                ) : (
                  'Run Scout'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {error && <p className="mt-6 text-sm text-red-400">{error}</p>}
        {profile && (
          <pre className="mt-6 whitespace-pre-wrap text-xs text-muted-foreground">
            {JSON.stringify(profile, null, 2)}
          </pre>
        )}
      </main>
    </div>
  )
}
