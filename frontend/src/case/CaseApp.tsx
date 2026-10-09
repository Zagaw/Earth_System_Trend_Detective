import { CaseProvider, useCase } from './context/CaseContext'
import { Header } from './components/layout/Header'
import { SectionNav } from './components/layout/SectionNav'
import { GuidedTour } from './components/tour/GuidedTour'
import { CaseOverview } from './sections/CaseOverview'
import { CompareTwins } from './sections/CompareTwins'
import { Evidence } from './sections/Evidence'
import { Fingerprint } from './sections/Fingerprint'
import { InvestigationMap } from './sections/InvestigationMap'

function Shell() {
  const { isLoading, isError, refetch, section, file } = useCase()
  if (isLoading) {
    return (
      <div className="stars flex min-h-screen flex-col items-center justify-center bg-navy">
        <svg width="48" height="48" viewBox="0 0 28 28" aria-hidden="true">
          <path d="M14 2l2.4 7.2H24l-6 4.4 2.3 7.2L14 16.6 7.7 20.8 10 13.6 4 9.2h7.6z" fill="#FBBF24" />
        </svg>
        <p className="mt-6 font-display text-2xl">Opening the case files...</p>
        <div className="mt-6 h-1 w-64 overflow-hidden rounded-full bg-line">
          <div className="h-full w-1/2 animate-[load_1.1s_ease-in-out_infinite] bg-gold" />
        </div>
      </div>
    )
  }
  if (isError || !file) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-navy px-6 text-center">
        <h2 className="font-display text-3xl font-bold">Could not load the evidence.</h2>
        <button type="button" className="mt-6 rounded-full bg-gold px-5 py-2 font-semibold text-navy" onClick={refetch}>
          Try again
        </button>
      </div>
    )
  }
  return (
    <div className="min-h-screen bg-navy text-ink">
      {file.is_sample ? (
        <p className="bg-[#FBBF24] px-4 py-2 text-center text-sm font-semibold text-navy">SAMPLE DATA - NOT REAL NASA RESULTS</p>
      ) : null}
      <Header />
      <SectionNav />
      <main className="px-4 py-6 pb-24 md:pb-10">
        {section === 'overview' ? <CaseOverview /> : null}
        {section === 'map' ? <InvestigationMap /> : null}
        {section === 'fingerprint' ? <Fingerprint /> : null}
        {section === 'compare' ? <CompareTwins /> : null}
        {section === 'evidence' ? <Evidence /> : null}
      </main>
      <GuidedTour />
    </div>
  )
}

export function CaseApp() {
  return (
    <CaseProvider>
      <Shell />
    </CaseProvider>
  )
}
