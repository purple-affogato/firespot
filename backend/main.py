from flask import Flask, make_response, request
from flask_cors import CORS
import simplekml
import xgboost as xgb
import numpy as np
from datetime import datetime
import csv
import math

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
GRID_RES = 0.1
RATE_SCALE = 0.060
non_burnable = [11, 12, 31, 250]

def snap(lat, lon):
    return (
        round(round(lat / GRID_RES) * GRID_RES, 6),
        round(round(lon / GRID_RES) * GRID_RES, 6),
    )

def load_land_cover():
    land_cover = {}
    with open('land_cover.csv', newline="") as f:
        for row in csv.DictReader(f):
            lat = float(row["lat_cell"])
            lon = float(row["lon_cell"])
            lc = int(row["land_cover"])
            land_cover[(lat, lon)] = lc
    return land_cover

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/get-map", methods=["GET"])
def get_map():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    
    if latitude is None or longitude is None:
        return "Missing query parameters", 400
    
    try:
        latitude = round(float(latitude), 2)
        longitude = round(float(longitude), 2)
    except ValueError:
        return "Invalid query parameters", 400
    
    kml = simplekml.Kml()
    
    # kml.newpoint(name="dummy", coords=[(37.3483333333, -121.9353888889)], description="0.5")
    
    lat, lon = latitude-0.1, longitude-0.1
    
    model = xgb.XGBRegressor()
    model.load_model('model2.ubj')
    
    coordinates = []
    dt = datetime.now()
    land_cover = load_land_cover()
    
    while lat <= latitude+0.1:
        while lon <= longitude+0.1:
            slat, slon = snap(lat, lon)
            coordinates.append([lat, lon, dt.month, int(dt.strftime('%j')), land_cover.get((slat, slon), 250)])
            print(coordinates[-1])
            lon += 0.05
        lat += 0.05
        lon = longitude-0.1
    
    # infer to get fire rate
    x_infer = np.array(coordinates)
    pred = model.predict(x_infer)
    
    for i in range(len(pred)):
        # use fire rate in poisson distribution (intensity = 1-e^(-k))
        # k = rate * 5 years
        prob = 0
        if coordinates[i][4] not in non_burnable:
            prob = round(1 - math.exp(-pred[i]*RATE_SCALE*5), 3)
        lat, lon = coordinates[i][0:2]
        kml.newpoint(name=f"{lat},{lon}", coords=[(lat, lon)], description=str(prob))
    
    return make_response(kml.kml(), 200, {'Content-Type': 'application/xml'})
