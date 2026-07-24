import { createPdf } from 'pdfmake/build/pdfmake'
import pdfFonts from 'pdfmake/build/vfs_fonts'
import type { TDocumentDefinitions } from 'pdfmake/interfaces'
import type { ScoutProfile } from '../App'

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-+)|(-+$)/g, '')
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10)
}

const LOW_CONFIDENCE_NOTE =
  'Low confidence: limited public information was found for this company. Treat this brief as a starting point, not a finished picture.'

export function downloadScoutReportPdf(profile: ScoutProfile, companyName: string): void {
  const date = todayIsoDate()
  const filename = `${slugify(companyName)}-scout-report-${date}.pdf`

  const docDefinition: TDocumentDefinitions = {
    defaultStyle: { font: 'Roboto', fontSize: 11 },
    content: [
      { text: companyName, style: 'title' },
      { text: `Generated ${date}`, style: 'subtitle' },
      ...(profile.low_confidence
        ? [{ text: LOW_CONFIDENCE_NOTE, style: 'warning' }]
        : []),
      { text: 'Classification', style: 'sectionHeader' },
      {
        text: `${profile.classification.service_line} (${Math.round(profile.classification.confidence * 100)}% confidence)`,
        margin: [0, 0, 0, 12] as [number, number, number, number],
      },
      { text: 'Brief', style: 'sectionHeader' },
      { text: profile.brief, margin: [0, 0, 0, 12] as [number, number, number, number] },
      { text: 'Why this angle fits', style: 'sectionHeader' },
      { text: profile.rationale, margin: [0, 0, 0, 12] as [number, number, number, number] },
      { text: 'Talking points', style: 'sectionHeader' },
      { ul: profile.talking_points, margin: [0, 0, 0, 12] as [number, number, number, number] },
    ],
    styles: {
      title: { fontSize: 20, bold: true, margin: [0, 0, 0, 4] },
      subtitle: { fontSize: 10, color: '#666666', margin: [0, 0, 0, 12] },
      warning: { fontSize: 10, color: '#92400e', margin: [0, 0, 0, 16] },
      sectionHeader: { fontSize: 13, bold: true, margin: [0, 8, 0, 4] },
    },
  }

  createPdf(docDefinition, undefined, undefined, pdfFonts).download(filename)
}
