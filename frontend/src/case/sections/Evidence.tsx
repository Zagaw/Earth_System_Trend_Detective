import { useCase } from '../context/CaseContext'
import { VARIABLE_ORDER } from '../lib/format'

export function Evidence() {
  const { file } = useCase()
  if (!file) return null
  const sections = [
    {
      title: 'Data source',
      body: `${file.source}, community ${file.community}. The series were retrieved ${file.evidence.retrieved_at}. Annual values cover ${file.start_year}–${file.end_year}. ${file.anomaly_reference}.`,
    },
    {
      title: 'Variables and units',
      body: VARIABLE_ORDER.map((id) => {
        const item = file.variables[id]
        return `${item.label} (${item.source_parameter}): source ${item.source_unit}, analysis ${item.unit}, slope ${item.slope_unit}. ${item.aggregation_rule}${item.conversion ? ` Conversion: ${item.conversion}.` : ''}`
      }).join('\n\n'),
    },
    {
      title: 'How regions are built',
      body: `National and state boundaries come from geoBoundaries gbOpen. A climate cell is kept when its centre is covered by Myanmar (${file.evidence.mask_policy}). ${file.evidence.masked_cell_count} cells are inside the country. Boundary overlaps: ${file.evidence.boundary_overlap_cells}. Interior cells without a state: ${file.evidence.unassigned_interior_cells}. Regional yearly values are area-weighted with ${file.evidence.spatial_weighting}. A regional year is kept when valid cells cover at least ${file.evidence.minimum_spatial_coverage} of that weight.`,
    },
    {
      title: 'How trends are measured',
      body: `${file.evidence.trend_method}. The slope per 10 years shown in the interface is that yearly slope multiplied by 10. ${file.evidence.significance_test} A trend needs at least ${file.evidence.minimum_valid_years} valid years.`,
    },
    {
      title: 'How significance works',
      body: `The threshold is ${file.significance_alpha}. ${file.evidence.multiple_testing_regions}. ${file.evidence.multiple_testing_national}. A hatched region did not meet that threshold. Grey means the series was too short to classify. The browser displays these statuses and does not recompute them.`,
    },
    {
      title: 'Limitations',
      body: file.evidence.limitations.join('\n\n'),
    },
    {
      title: 'Credits',
      body: 'NASA POWER provides the climate series. geoBoundaries gbOpen provides the Myanmar boundaries: ADM0 from OpenStreetMap under CC BY-SA 2.0, and ADM1 from the Myanmar Analytics Project under CC BY 4.0. Team Star Devs built EarthTrend Myanmar for NASA Space Apps.',
    },
  ]
  return (
    <section className="mx-auto max-w-3xl">
      <h2 className="font-display text-3xl font-bold">Evidence locker</h2>
      <p className="mt-2 text-sm text-muted">The notes below are generated from the case file, including the units and the tests that produced the verdicts.</p>
      <div className="mt-5 space-y-3">
        {sections.map((section) => (
          <details key={section.title} className="rounded-2xl border border-line bg-surface p-4" open={section.title === 'Data source'}>
            <summary className="cursor-pointer font-display font-semibold">{section.title}</summary>
            <p className="mt-3 text-sm leading-6 whitespace-pre-wrap text-muted">{section.body}</p>
          </details>
        ))}
      </div>
    </section>
  )
}
