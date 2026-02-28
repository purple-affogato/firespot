import csv
import os
from datetime import datetime

INPUT_FILE = os.path.join(
    os.path.dirname(__file__),
    "data",
    "inform_fireoccurence_public_-7825632427851538956.csv",
)
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "data", "fires_clean.csv")

BOUNDS = [
    (24.5, 49.5, -125.0, -66.9),  # CONUS
    (51.0, 71.5, -180.0, -129.9),  # Alaska
    (18.9, 22.2, -160.2, -154.8),  # Hawaii
]

VALID_YEARS = range(2010, 2027)

OUTPUT_COLS = [
    "latitude",
    "longitude",
    "year",
    "month",
    "day_of_year",
]


def in_bounds(lat, lon):
    for lat_min, lat_max, lon_min, lon_max in BOUNDS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return True
    return False


def parse_date(date_str):
    """Try a few common formats, return (year, month, day_of_year) or None."""
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S+00"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.year, dt.month, dt.timetuple().tm_yday
        except ValueError:
            continue
    return None


def main():
    kept = 0
    dropped_no_coords = 0
    dropped_bad_bounds = 0
    dropped_bad_date = 0
    dropped_bad_year = 0
    dropped_bad_type = 0
    total = 0

    with (
        open(INPUT_FILE, newline="", encoding="utf-8-sig") as fin,
        open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as fout,
    ):
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=OUTPUT_COLS)
        writer.writeheader()

        for row in reader:
            total += 1

            lat_str = row.get("Initial Latitude", "").strip()
            lon_str = row.get("Initial Longitude", "").strip()
            if not lat_str or not lon_str:
                dropped_no_coords += 1
                continue
            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except ValueError:
                dropped_no_coords += 1
                continue

            if not in_bounds(lat, lon):
                dropped_bad_bounds += 1
                continue

            date_str = row.get("Fire Discovery Date Time", "").strip()
            parsed = parse_date(date_str)
            if parsed is None:
                dropped_bad_date += 1
                continue
            year, month, day_of_year = parsed

            if year not in VALID_YEARS:
                dropped_bad_year += 1
                continue

            incident_type = row.get("Incident Type Category", "").strip().upper()
            if incident_type != "WF":
                dropped_bad_type += 1
                continue

            writer.writerow(
                {
                    "latitude": round(lat, 5),
                    "longitude": round(lon, 5),
                    "year": year,
                    "month": month,
                    "day_of_year": day_of_year,
                }
            )
            kept += 1

    print(f"Total rows read        : {total:>10,}")
    print(f"Kept                   : {kept:>10,}  ({100 * kept / total:.1f}%)")
    print(f"Dropped - no coords    : {dropped_no_coords:>10,}")
    print(f"Dropped - out of bounds: {dropped_bad_bounds:>10,}")
    print(f"Dropped - bad date     : {dropped_bad_date:>10,}")
    print(f"Dropped - bad year     : {dropped_bad_year:>10,}")
    print(f"Dropped - bad type     : {dropped_bad_type:>10,}")
    print(f"\nOutput written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
