import csv
import os
import random

import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "fires_clean.csv")
LAND_COVER_FILE = os.path.join(os.path.dirname(__file__), "data", "land_cover.csv")
MODEL_FILE = os.path.join(os.path.dirname(__file__), "model.ubj")

GRID_RES = 0.1
CONUS_BOUNDS = (24.5, 49.5, -125.0, -66.9)
N_YEARS = 15  # 2010-2025
NON_BURNABLE = {11, 12, 21, 22, 23, 24, 250}
DEVICE = "cuda"

FEATURE_NAMES = [
    "latitude",
    "longitude",
    "month",
    "day_of_year",
    "land_cover",
]


def snap_to_grid(lat, lon, res=GRID_RES):
    return (round(round(lat / res) * res, 6), round(round(lon / res) * res, 6))


def load_density_table(path):
    """Count distinct years burned per cell to avoid inflating counts from multi-incident fires."""
    years_per_cell = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (round(float(row["latitude"]), 6), round(float(row["longitude"]), 6))
            year = int(row["year"])
            if key not in years_per_cell:
                years_per_cell[key] = set()
            years_per_cell[key].add(year)
    return {key: len(years) for key, years in years_per_cell.items()}


def load_land_cover_table(path):
    lc = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (round(float(row["lat_cell"]), 6), round(float(row["lon_cell"]), 6))
            lc[key] = int(row["land_cover"])
    return lc


def build_positives(density_table, land_cover_table):
    """
    One record per unique burnable grid cell that has fired at least once.
    Target = fire_count / N_YEARS (fires per year).
    We expand each cell across all 12 months so the model learns seasonality.
    """
    records = []
    for (lat, lon), count in density_table.items():
        lc = land_cover_table.get((lat, lon), -1)
        if lc in NON_BURNABLE or lc == -1:
            continue
        rate = count / N_YEARS
        for month in range(1, 13):
            day_of_year = (month - 1) * 30 + 15
            records.append([lat, lon, month, day_of_year, lc, rate])
    return records


def build_negatives(density_table, land_cover_table, n_samples, seed=42):
    rng = random.Random(seed)
    lat_min, lat_max, lon_min, lon_max = CONUS_BOUNDS

    fire_locations = set(density_table.keys())

    records = []
    attempts = 0
    max_attempts = n_samples * 20

    while len(records) < n_samples and attempts < max_attempts:
        attempts += 1

        lat = rng.uniform(lat_min, lat_max)
        lon = rng.uniform(lon_min, lon_max)
        lat_c, lon_c = snap_to_grid(lat, lon)

        if (lat_c, lon_c) in fire_locations:
            continue

        lc = land_cover_table.get((lat_c, lon_c), -1)
        month = rng.randint(1, 12)
        day_of_year = (month - 1) * 30 + 15
        records.append([lat_c, lon_c, month, day_of_year, lc, 0.0])

    return records


def main():
    print("Loading tables...")
    density_table = load_density_table(DATA_FILE)
    land_cover_table = load_land_cover_table(LAND_COVER_FILE)
    print(
        f"  {len(density_table):,} fire cells, {len(land_cover_table):,} land cover cells"
    )

    print("Building positives...")
    positives = build_positives(density_table, land_cover_table)
    print(f"  {len(positives):,} positive records")

    n_neg = len(positives)
    print(f"Building {n_neg:,} negatives...")
    negatives = build_negatives(density_table, land_cover_table, n_neg)
    print(f"  {len(negatives):,} negative records")

    all_records = positives + negatives
    random.shuffle(all_records)

    data = np.array(all_records, dtype=np.float32)
    X = data[:, :5]
    y = data[:, 5]

    print(f"\nDataset: {len(y):,} samples | Features: {X.shape[1]}")
    print(f"  Fire rate range: {y.min():.4f} - {y.max():.4f}, mean: {y.mean():.4f}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"  Train: {len(y_train):,} | Test: {len(y_test):,}")

    print(f"\nTraining XGBoost regressor (device={DEVICE})...")
    model = xgb.XGBRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        tree_method="hist",
        device=DEVICE,
        eval_metric="rmse",
        early_stopping_rounds=20,
        random_state=42,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=50,
    )

    print("\nEvaluating...")
    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0, None)

    print(f"  MAE  : {mean_absolute_error(y_test, y_pred):.6f} fires/year")
    print(f"  R²   : {r2_score(y_test, y_pred):.4f}")

    importances = model.feature_importances_
    print("\nFeature importances:")
    for name, imp in sorted(zip(FEATURE_NAMES, importances), key=lambda x: -x[1]):
        print(f"  {name:<15} {imp:.4f}")

    print(f"\nSaving model to {MODEL_FILE}...")
    model.save_model(MODEL_FILE)
    print("Done.")


if __name__ == "__main__":
    main()
