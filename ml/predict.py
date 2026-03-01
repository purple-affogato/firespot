import csv
from datetime import UTC, datetime

import numpy as np
import xgboost as xgb

GRID_RES = 0.1
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


def predict(lat, lon, years=1):
    model = xgb.XGBRegressor()
    model.load_model(MODEL_FILE)
    land_cover = load_land_cover(LAND_COVER_FILE)

    today = datetime.now(UTC)
    month = today.month
    day_of_year = today.timetuple().tm_yday

    slat, slon = snap(lat, lon)
    lc = land_cover.get((slat, slon), -1)

    X = np.array([[lat, lon, month, day_of_year, lc]], dtype=np.float32)
    rate = float(np.clip(model.predict(X), 0, None)[0])
    prob = 1.0 - np.exp(-rate * years)

    return {"lat": lat, "lon": lon, "fire_rate": rate, "prob": prob}


if __name__ == "__main__":
    import sys

    lat = float(sys.argv[1])
    lon = float(sys.argv[2])
    years = float(sys.argv[3]) if len(sys.argv) > 3 else 1
    print(predict(lat, lon, years))
