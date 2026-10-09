import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import xarray as xr
from shapely.geometry import Point
from shapely.prepared import prep


MASK_POLICY = "cell_center_covered_by"


def apply_boundaries(dataset: xr.Dataset, boundary_dir: Path) -> tuple[xr.Dataset, dict]:
    national_path = boundary_dir / "mmr-adm0.geojson"
    admin_path = boundary_dir / "mmr-adm1.geojson"
    if not national_path.exists() or not admin_path.exists():
        raise FileNotFoundError(
            "Myanmar boundary files are missing from the boundary directory."
        )

    national = gpd.read_file(national_path)
    admin = gpd.read_file(admin_path)
    national_geom = national.geometry.iloc[0]
    prepared_national = prep(national_geom)
    admin_records = []
    for row in admin.itertuples(index=False):
        admin_records.append(
            {
                "id": str(row.shapeID),
                "name": str(row.shapeName),
                "iso": str(row.shapeISO or ""),
                "level": "ADM1",
                "geometry": row.geometry,
                "prepared": prep(row.geometry),
            }
        )

    latitudes = dataset.latitude.values
    longitudes = dataset.longitude.values
    mask = np.zeros((len(latitudes), len(longitudes)), dtype=bool)
    region_index = np.full((len(latitudes), len(longitudes)), -1, dtype=np.int16)
    overlap = np.zeros(mask.shape, dtype=bool)

    for lat_index, latitude in enumerate(latitudes):
        for lon_index, longitude in enumerate(longitudes):
            point = Point(float(longitude), float(latitude))
            if not prepared_national.covers(point):
                continue
            mask[lat_index, lon_index] = True
            matches = [
                index
                for index, region in enumerate(admin_records)
                if region["prepared"].covers(point)
            ]
            if matches:
                region_index[lat_index, lon_index] = matches[0]
                if len(matches) > 1:
                    overlap[lat_index, lon_index] = True

    masked = dataset.copy()
    masked["myanmar_mask"] = (("latitude", "longitude"), mask)
    masked["region_index"] = (("latitude", "longitude"), region_index)
    for name in ("precipitation", "temperature", "relative_humidity"):
        if name in masked:
            masked[name] = masked[name].where(masked["myanmar_mask"])

    national_props = national.iloc[0]
    cell_counts = []
    for index, region in enumerate(admin_records):
        cell_counts.append(int(np.count_nonzero(region_index == index)))
    catalog = {
        "mask_policy": MASK_POLICY,
        "national": {
            "id": str(national_props.shapeID),
            "name": str(national_props.shapeName),
            "iso": "MMR",
            "level": "ADM0",
            "cell_count": int(mask.sum()),
        },
        "regions": [
            {
                "id": region["id"],
                "name": region["name"],
                "iso": region["iso"],
                "level": "ADM1",
                "cell_count": cell_counts[index],
            }
            for index, region in enumerate(admin_records)
        ],
        "boundary_overlap_cells": int(overlap.sum()),
        "unassigned_interior_cells": int(np.count_nonzero(mask & (region_index < 0))),
        "latitude_spacing": _spacing(latitudes, 0.5),
        "longitude_spacing": _spacing(longitudes, 0.625),
    }
    masked.attrs["mask_policy"] = MASK_POLICY
    return masked, catalog


def load_region_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _spacing(values: np.ndarray, fallback: float) -> float:
    if len(values) < 2:
        return fallback
    diffs = np.diff(np.sort(np.asarray(values, dtype=float)))
    positive = diffs[diffs > 0]
    if positive.size == 0:
        return fallback
    return float(np.median(positive))
