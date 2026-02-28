import csv
import os
import pickle
import random
from collections import defaultdict

import numpy as np
import xgboost as xgb
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "fires_clean.csv")
MODEL_FILE = os.path.join(os.path.dirname(__file__), "model.ubj")

GRID_RES = 0.05

# for inference
CA_BOUNDS = (32.5, 42.0, -124.5, -114.1)

# for generating negatives during training
US_BOUNDS = (24.5, 49.5, -125.0, -66.9)

NEG_TO_POS_RATIO = 3

DEVICE = "cuda"


def snap_to_grid(lat, lon, res=GRID_RES):
    return (round(round(lat / res) * res, 6), round(round(lon / res) * res, 6))


def in_bounds(lat, lon, bounds):
    lat_min, lat_max, lon_min, lon_max = bounds
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def load_fire_cells(path):
    fire_cells = set()  # (lat_cell, lon_cell, month)
    records = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            month = int(row["month"])
            day_of_year = int(row["day_of_year"])
            year = int(row["year"])

            lat_c, lon_c = snap_to_grid(lat, lon)
            fire_cells.add((lat_c, lon_c, month))
            records.append(
                {
                    "latitude": lat_c,
                    "longitude": lon_c,
                    "month": month,
                    "day_of_year": day_of_year,
                    "year": year,
                    "label": 1,
                }
            )

    return fire_cells, records


def generate_negatives(fire_cells, n_samples, bounds=US_BOUNDS, seed=42):
    rng = random.Random(seed)
    lat_min, lat_max, lon_min, lon_max = bounds

    fire_locations = {(lat, lon) for lat, lon, _ in fire_cells}

    negatives = []
    attempts = 0
    max_attempts = n_samples * 20

    while len(negatives) < n_samples and attempts < max_attempts:
        attempts += 1

        lat = rng.uniform(lat_min, lat_max)
        lon = rng.uniform(lon_min, lon_max)
        lat_c, lon_c = snap_to_grid(lat, lon)

        if (lat_c, lon_c) in fire_locations:
            continue

        month = rng.randint(1, 12)
        day_of_year = (month - 1) * 30 + 15
        year = rng.randint(2010, 2025)

        negatives.append(
            {
                "latitude": lat_c,
                "longitude": lon_c,
                "month": month,
                "day_of_year": day_of_year,
                "year": year,
                "label": 0,
            }
        )

    return negatives


def records_to_arrays(records):
    X = np.array(
        [
            [r["latitude"], r["longitude"], r["month"], r["day_of_year"], r["year"]]
            for r in records
        ],
        dtype=np.float32,
    )

    y = np.array([r["label"] for r in records], dtype=np.float32)
    return X, y


def main():
    print("Loading fire records...")
    fire_cells, positives = load_fire_cells(DATA_FILE)
    n_pos = len(positives)
    print(f"  Positive samples (fire grid cells): {n_pos:,}")

    n_neg = n_pos * NEG_TO_POS_RATIO
    print(f"Generating {n_neg:,} negative samples ({NEG_TO_POS_RATIO}x positives)...")
    negatives = generate_negatives(fire_cells, n_samples=n_neg)
    print(f"  Negative samples generated: {len(negatives):,}")

    all_records = positives + negatives
    random.shuffle(all_records)

    print("Building feature matrix...")
    X, y = records_to_arrays(all_records)
    print(f"  Total samples: {len(y):,}  |  Features: {X.shape[1]}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Train: {len(y_train):,}  |  Test: {len(y_test):,}")

    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    print(f"  scale_pos_weight: {scale_pos_weight:.2f}")

    print(f"\nTraining XGBoost (device={DEVICE})...")
    model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        tree_method="hist",
        device=DEVICE,
        eval_metric="auc",
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
    y_prob = model.predict_proba(X_test)[:, 1]

    print(classification_report(y_test, y_pred, target_names=["no fire", "fire"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")

    feature_names = ["latitude", "longitude", "month", "day_of_year", "year"]
    importances = model.feature_importances_
    print("\nFeature importances:")
    for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
        print(f"  {name:<15} {imp:.4f}")

    print(f"\nSaving model to {MODEL_FILE}...")
    model.save_model(MODEL_FILE)
    print("Done.")


if __name__ == "__main__":
    main()
