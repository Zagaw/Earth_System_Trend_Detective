import argparse
import json

from app.core.variables import VARIABLES
from app.services.catalog import ClimateCatalog, clear_catalog
from app.services.nasa_power import NasaPowerClient
from app.services.normalization import parse_power_response


def main() -> None:
    parser = argparse.ArgumentParser(description="EarthTrend Myanmar data commands")
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser(
        "verify",
        help="Request one year from a single NASA POWER point and print parameter units.",
    )
    verify.add_argument("--latitude", type=float, default=16.8)
    verify.add_argument("--longitude", type=float, default=96.1)
    verify.add_argument("--year", type=int, default=2020)
    subparsers.add_parser("ingest", help="Download the Myanmar NASA POWER grid and build the analysis dataset.")
    args = parser.parse_args()

    if args.command == "verify":
        _verify(args.latitude, args.longitude, args.year)
    elif args.command == "ingest":
        _ingest()


def _verify(latitude: float, longitude: float, year: int) -> None:
    client = NasaPowerClient()
    for definition in VARIABLES.values():
        payload = client.fetch_point_monthly(
            definition.source_parameter,
            latitude=latitude,
            longitude=longitude,
            start_year=year,
            end_year=year,
        )
        parsed = parse_power_response(payload, definition.source_parameter)
        valid = sum(item.data_quality_status == "valid" for item in parsed.observations)
        print(
            json.dumps(
                {
                    "parameter": parsed.source_parameter,
                    "variable": parsed.variable,
                    "unit": parsed.source_unit,
                    "long_name": parsed.long_name,
                    "monthly_values": valid,
                    "annual_api_statistics": len(parsed.annual_statistics),
                    "sources": parsed.sources,
                }
            )
        )


def _ingest() -> None:
    clear_catalog()
    catalog = ClimateCatalog.build()
    info = catalog.metadata()
    print(json.dumps(info))


if __name__ == "__main__":
    main()
