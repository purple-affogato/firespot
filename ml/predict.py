import csv
import sys
from datetime import UTC, datetime

import numpy as np
import xgboost as xgb

GRID_RES = 0.1
RATE_SCALE = 0.067
NON_BURNABLE = {11, 12, 31, 250}
MODEL_FILE = "model.ubj"
LAND_COVER_FILE = "data/land_cover.csv"


def load_land_cover(path):
    lc = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            lat = round(float(row["lat_cell"]), 6)
            lon = round(float(row["lon_cell"]), 6)
            lc[(lat, lon)] = int(row["land_cover"])
    return lc


def snap(lat, lon):
    return (
        round(round(lat / GRID_RES) * GRID_RES, 6),
        round(round(lon / GRID_RES) * GRID_RES, 6),
    )


def predict(lat, lon, years=1.0):
    model = xgb.XGBRegressor()
    model.load_model(MODEL_FILE)
    land_cover = load_land_cover(LAND_COVER_FILE)

    today = datetime.now(UTC)
    month = today.month
    day_of_year = today.timetuple().tm_yday

    slat, slon = snap(lat, lon)
    lc = land_cover.get((slat, slon), -1)

    if lc in NON_BURNABLE:
        return {"lat": lat, "lon": lon, "fire_rate": 0.0, "prob": 0.0}

    X = np.array([[lat, lon, month, day_of_year, lc]], dtype=np.float32)
    cell_rate = float(np.clip(model.predict(X), 0, None)[0])

    rate = cell_rate * RATE_SCALE
    prob = 1.0 - np.exp(-rate * years)

    return {"lat": lat, "lon": lon, "fire_rate": cell_rate, "prob": prob}


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print("Usage: python predict.py <lat> <lon> [years]")
        sys.exit(1)

    lat = float(sys.argv[1])
    lon = float(sys.argv[2])
    years = float(sys.argv[3]) if len(sys.argv) == 4 else 1.0
    print(predict(lat, lon, years))
