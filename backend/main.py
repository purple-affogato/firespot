from flask import Flask, make_response, request
from flask_cors import CORS
import simplekml
import xgboost as xgb

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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
    model.load_model('model.ubj')
    
    coordinates = []
    
    while lat <= latitude+0.1:
        while lon <= longitude+0.1:
            coordinates.append(())
            lon += 0.01
        lat += 0.01
        
    # infer to get fire rate
    # use fire rate in poisson distribution (intensity = 1-e^(-k))
    # k = rate * 5 years
    # # coords=[(lat, lon)]
    kml.newpoint(name="dummy", coords=[(lat, lon)], description=str(intensity))
    
    return make_response(kml.kml(), 200, {'Content-Type': 'application/xml'})
