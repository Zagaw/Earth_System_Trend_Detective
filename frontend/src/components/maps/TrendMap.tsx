import type { Layer } from 'leaflet'
import { GeoJSON, MapContainer, TileLayer } from 'react-leaflet'
import type { GridFeature } from '../../types/api'
import { statusColor } from '../ui/StatusPill'

export function TrendMap({ features, mapKey }: { features: GridFeature[]; mapKey: string }) {
  const collection = { type: 'FeatureCollection' as const, features }

  return (
    <div className="h-[640px] overflow-hidden rounded-2xl border border-line">
      <MapContainer center={[19.2, 96.7]} zoom={5} className="h-full w-full" scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <GeoJSON
          key={mapKey}
          data={collection}
          style={(feature) => {
            const status = String(feature?.properties?.trend_status ?? 'insufficient_data')
            return {
              color: '#101613',
              weight: 0.4,
              fillColor: statusColor[status] ?? statusColor.insufficient_data,
              fillOpacity: status === 'not_significant' ? 0.35 : status === 'insufficient_data' ? 0.2 : 0.72,
            }
          }}
          onEachFeature={(feature, layer: Layer) => {
            const properties = feature.properties ?? {}
            const slope = properties.sen_slope == null ? 'unavailable' : properties.sen_slope
            layer.bindPopup(
              `<strong>${properties.region_name ?? 'Unassigned cell'}</strong><br/>` +
                `${properties.latitude}, ${properties.longitude}<br/>` +
                `Slope: ${slope} ${properties.slope_unit ?? ''}<br/>` +
                `Status: ${properties.trend_status}<br/>` +
                `Adjusted p: ${properties.adjusted_p_value ?? 'n/a'}<br/>` +
                `Valid years: ${properties.valid_years}`,
            )
          }}
        />
      </MapContainer>
    </div>
  )
}
