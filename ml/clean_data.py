import csv
import os
from collections import defaultdict
from datetime import datetime

import numpy as np
import rasterio
from rasterio.transform import rowcol
from rasterio.warp import transform as warp_transform

INPUT_FILE = os.path.join(
    os.path.dirname(__file__),
    "data",
    "InFORM_FireOccurrence_Public_-7825632427851538956.csv",
)
NLCD_FILE = os.path.join(
    os.path.dirname(__file__),
    "data",
    "Annual_NLCD_LndCov_2024_CU_C1V1.tif",
)
OUTPUT_FIRES = os.path.join(os.path.dirname(__file__), "data", "fires_clean.csv")
OUTPUT_DENSITY = os.path.join(os.path.dirname(__file__), "data", "fire_density.csv")
OUTPUT_LAND_COVER = os.path.join(os.path.dirname(__file__), "data", "land_cover.csv")

BOUNDS = [
    (24.5, 49.5, -130.0, -66.9),  # CONUS (extended west for offshore)
    (51.0, 71.5, -180.0, -129.9),  # Alaska
    (18.9, 22.2, -160.2, -154.8),  # Hawaii
]

VALID_YEARS = range(2010, 2027)

GRID_RES = 0.1

# NLCD classes considered non-burnable
NON_BURNABLE = {
    11,  # Open Water
    12,  # Perennial Ice/Snow
    21,  # Developed, Open Space
    22,  # Developed, Low Intensity
    23,  # Developed, Medium Intensity
    24,  # Developed, High Intensity
}

OUTPUT_FIRES_COLS = [
    "latitude",
    "longitude",
    "year",
    "month",
    "day_of_year",
    "land_cover",
    "fire_density",
]

OUTPUT_DENSITY_COLS = ["lat_cell", "lon_cell", "fire_count"]
OUTPUT_LAND_COVER_COLS = ["lat_cell", "lon_cell", "land_cover"]


def in_bounds(lat, lon):
    for lat_min, lat_max, lon_min, lon_max in BOUNDS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return True
    return False


def parse_date(date_str):
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S+00"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.year, dt.month, dt.timetuple().tm_yday
        except ValueError:
            continue
    return None


def snap_to_grid(lat, lon, res=GRID_RES):
    return (
        round(round(lat / res) * res, 6),
        round(round(lon / res) * res, 6),
    )


def sample_land_cover(dataset, lat, lon):
    try:
        xs, ys = warp_transform("EPSG:4326", dataset.crs, [lon], [lat])
        row, col = rowcol(dataset.transform, xs[0], ys[0])
        data = dataset.read(1, window=((row, row + 1), (col, col + 1)))
        return int(data[0, 0])
    except Exception:
        return -1


def main():
    print("Pass 1: reading fire records and computing fire density...")
    fire_density = defaultdict(int)
    raw_records = []

    kept = 0
    dropped_no_coords = 0
    dropped_bad_bounds = 0
    dropped_bad_date = 0
    dropped_bad_year = 0
    dropped_bad_type = 0
    total = 0

    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as fin:
        reader = csv.DictReader(fin)
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

            lat_c, lon_c = snap_to_grid(lat, lon)
            fire_density[(lat_c, lon_c)] += 1
            raw_records.append(
                {
                    "latitude": lat_c,
                    "longitude": lon_c,
                    "year": year,
                    "month": month,
                    "day_of_year": day_of_year,
                }
            )
            kept += 1

    print(f"  Read {total:,} rows, kept {kept:,} fire records")
    print(f"  Unique grid cells with fires: {len(fire_density):,}")

    print("Pass 2: sampling land cover from NLCD...")
    with (
        rasterio.open(NLCD_FILE) as nlcd,
        open(OUTPUT_FIRES, "w", newline="", encoding="utf-8") as fout,
    ):
        writer = csv.DictWriter(fout, fieldnames=OUTPUT_FIRES_COLS)
        writer.writeheader()

        for i, rec in enumerate(raw_records):
            if i % 50000 == 0:
                print(f"  {i:,} / {kept:,}")

            lat_c = rec["latitude"]
            lon_c = rec["longitude"]
            lc = sample_land_cover(nlcd, lat_c, lon_c)
            density = fire_density[(lat_c, lon_c)]

            writer.writerow(
                {
                    "latitude": lat_c,
                    "longitude": lon_c,
                    "year": rec["year"],
                    "month": rec["month"],
                    "day_of_year": rec["day_of_year"],
                    "land_cover": lc,
                    "fire_density": density,
                }
            )

    print(f"\nFire records written to: {OUTPUT_FIRES}")

    print("Writing fire density table...")
    with open(OUTPUT_DENSITY, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_DENSITY_COLS)
        writer.writeheader()
        for (lat_c, lon_c), count in sorted(fire_density.items()):
            writer.writerow({"lat_cell": lat_c, "lon_cell": lon_c, "fire_count": count})

    print(f"Fire density table written to: {OUTPUT_DENSITY}")

    print("Pass 3: precomputing land cover for entire US grid...")
    lat_min, lat_max, lon_min, lon_max = 24.5, 49.5, -130.0, -66.9
    lats = np.arange(lat_min, lat_max, GRID_RES)
    lons = np.arange(lon_min, lon_max, GRID_RES)
    total_cells = len(lats) * len(lons)
    print(f"  Total US grid cells: {total_cells:,}")

    with (
        rasterio.open(NLCD_FILE) as nlcd,
        open(OUTPUT_LAND_COVER, "w", newline="", encoding="utf-8") as f,
    ):
        writer = csv.DictWriter(f, fieldnames=OUTPUT_LAND_COVER_COLS)
        writer.writeheader()

        done = 0
        # batch reproject all points at once per lat row for speed
        for lat in lats:
            lat_col = [round(float(lat), 6)] * len(lons)
            lon_col = [round(float(lon), 6) for lon in lons]
            try:
                xs, ys = warp_transform("EPSG:4326", nlcd.crs, lon_col, lat_col)
                rows, cols = rowcol(nlcd.transform, xs, ys)
                for i, (r, c) in enumerate(zip(rows, cols)):
                    try:
                        val = int(nlcd.read(1, window=((r, r + 1), (c, c + 1)))[0, 0])
                    except Exception:
                        val = -1
                    writer.writerow(
                        {
                            "lat_cell": lat_col[i],
                            "lon_cell": lon_col[i],
                            "land_cover": val,
                        }
                    )
            except Exception:
                for lon in lon_col:
                    writer.writerow(
                        {
                            "lat_cell": round(float(lat), 6),
                            "lon_cell": lon,
                            "land_cover": -1,
                        }
                    )

            done += len(lons)
            if done % 50000 < len(lons):
                print(f"  {done:,} / {total_cells:,}")

    print(f"Land cover table written to: {OUTPUT_LAND_COVER}")

    print(f"\nTotal rows read        : {total:>10,}")
    print(f"Kept                   : {kept:>10,}  ({100 * kept / total:.1f}%)")
    print(f"Dropped - no coords    : {dropped_no_coords:>10,}")
    print(f"Dropped - out of bounds: {dropped_bad_bounds:>10,}")
    print(f"Dropped - bad date     : {dropped_bad_date:>10,}")
    print(f"Dropped - bad year     : {dropped_bad_year:>10,}")
    print(f"Dropped - bad type     : {dropped_bad_type:>10,}")


if __name__ == "__main__":
    main()
