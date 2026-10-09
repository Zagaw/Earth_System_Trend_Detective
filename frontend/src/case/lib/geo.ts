import { geoCentroid, geoMercator, geoPath, type GeoPermissibleObjects } from 'd3-geo'

export function makeProjection(collection: GeoPermissibleObjects, width: number, height: number) {
  const projection = geoMercator().fitExtent(
    [
      [12, 12],
      [Math.max(width - 12, 24), Math.max(height - 12, 24)],
    ],
    collection,
  )
  return { projection, path: geoPath(projection) }
}

export function featureCentroid(
  feature: GeoPermissibleObjects,
  projection: ReturnType<typeof geoMercator>,
) {
  const geographic = geoCentroid(feature)
  const point = projection(geographic)
  return point ?? [Number.NaN, Number.NaN]
}
