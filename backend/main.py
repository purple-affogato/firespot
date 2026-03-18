import csv
import math
from datetime import datetime

import numpy as np
import simplekml
import xgboost as xgb
from flask import Flask, make_response, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/*": {"origins": "*"}})
GRID_RES = 0.1
GRIDMET_VARS = ["erc", "fm100", "fm1000", "tmmx", "vpd", "vs"]
RATE_SCALE = 0.060
non_burnable = [11, 12, 31, 250]


def snap(lat, lon):
    return (
        round(round(lat / GRID_RES) * GRID_RES, 6),
        round(round(lon / GRID_RES) * GRID_RES, 6),
    )


def load_land_cover():
    land_cover = {}
    with open("land_cover.csv", newline="") as f:
        for row in csv.DictReader(f):
            lat = float(row["lat_cell"])
            lon = float(row["lon_cell"])
            lc = int(row["land_cover"])
            land_cover[(lat, lon)] = lc
    return land_cover

def load_gridmet():
    gridmet = {}
    with open("gridmet.csv", newline="") as f:
        for row in csv.DictReader(f):
            lat = round(float(row["lat_cell"]), 6)
            lon = round(float(row["lon_cell"]), 6)
            gridmet[(lat, lon)] = [float(row[v]) if row[v] != "" else 0.0 for v in GRIDMET_VARS]
    return gridmet

@app.route("/")
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route("/get-map", methods=["GET"])
def get_map():
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")

    if latitude is None or longitude is None:
        return "Missing query parameters", 400

    try:
        latitude = round(float(latitude), 2)
        longitude = round(float(longitude), 2)
    except ValueError:
        return "Invalid query parameters", 400

    kml = simplekml.Kml()

    # kml.newpoint(name="dummy", coords=[(37.3483333333, -121.9353888889)], description="0.5")

    lat, lon = latitude - 0.1, longitude - 0.1
    gridmet = load_gridmet()
    default_gm = [0.0] * 6


    model = xgb.XGBRegressor()
    model.load_model("model2.ubj")

    coordinates = []
    dt = datetime.now()
    land_cover = load_land_cover()

    while lat <= latitude + 0.1:
        while lon <= longitude + 0.1:
            slat, slon = snap(lat, lon)
            gm = gridmet.get((slat, slon), default_gm)
            coordinates.append(
                [
                    slat,
                    slon,
                    dt.month,
                    int(dt.strftime("%j")),
                    land_cover.get((slat, slon), 250),
                ] + gm
            )
            print(coordinates[-1])
            lon += 0.05
        lat += 0.05
        lon = longitude - 0.1

    # infer to get fire rate
    x_infer = np.array(coordinates)
    pred = model.predict(x_infer)

    for i in range(len(pred)):
        # use fire rate in poisson distribution (intensity = 1-e^(-k))
        # k = rate * 5 years
        prob = 0
        if coordinates[i][4] not in non_burnable:
            prob = round(1 - math.exp(-pred[i] * RATE_SCALE * 5), 3)
        slat, slon = coordinates[i][0:2]
        kml.newpoint(
            name=f"{slat},{slon}", coords=[(slat, slon)], description=str(prob)
        )

    return make_response(kml.kml(), 200, {"Content-Type": "application/xml"})
