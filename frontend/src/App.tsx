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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'

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

        {error && (
          <Alert variant="destructive" className="mt-6">
            <AlertTitle>Something went wrong</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {loading && (
          <Card className="mt-6">
            <CardHeader>
              <Skeleton className="h-5 w-40" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </CardContent>
          </Card>
        )}

        {profile && !loading && (
          <Card className="mt-6">
            <CardContent className="pt-6">
              {profile.low_confidence && (
                <Alert className="mb-4 border-amber-500/50 text-amber-400 [&>svg]:text-amber-400">
                  <AlertTitle>Low confidence</AlertTitle>
                  <AlertDescription>
                    Limited public information was found for this company. Treat this brief as a
                    starting point, not a finished picture.
                  </AlertDescription>
                </Alert>
              )}

              <Tabs defaultValue="overview">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="rationale">Rationale</TabsTrigger>
                  <TabsTrigger value="talking-points">Talking Points</TabsTrigger>
                </TabsList>
                <TabsContent value="overview" className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Badge>{profile.classification.service_line}</Badge>
                    <span className="text-sm text-muted-foreground">
                      {Math.round(profile.classification.confidence * 100)}% confidence
                    </span>
                  </div>
                  <p className="whitespace-pre-line text-sm text-foreground">{profile.brief}</p>
                </TabsContent>
                <TabsContent value="rationale">
                  <p className="whitespace-pre-line text-sm text-foreground">{profile.rationale}</p>
                </TabsContent>
                <TabsContent value="talking-points">
                  <ul className="list-disc space-y-1 pl-5 text-sm text-foreground">
                    {profile.talking_points.map((point) => (
                      <li key={point}>{point}</li>
                    ))}
                  </ul>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
