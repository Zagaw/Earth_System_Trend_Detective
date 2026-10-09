from pathlib import Path

from shapely.geometry import Point
from shapely.prepared import prep

import geopandas as gpd

BOUNDARY = Path(__file__).parents[2] / "data" / "boundaries" / "mmr-adm0.geojson"


def test_cell_centre_mask_accepts_yangon_and_rejects_bangkok() -> None:
    national = gpd.read_file(BOUNDARY)
    geometry = prep(national.geometry.iloc[0])
    yangon = Point(96.1, 16.8)
    bangkok = Point(100.5, 13.75)
    assert geometry.covers(yangon)
    assert not geometry.covers(bangkok)
