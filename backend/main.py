from flask import Flask, make_response
from flask_cors import CORS
import simplekml
# import firebase_admin
# from firebase_admin import credentials, firestore

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/get-map", methods=["GET"])
def get_map():
    kml = simplekml.Kml()
<<<<<<< HEAD
    pnt = kml.newpoint(
        name="dummy", coords=[(37.3483333333, -121.9353888889)], description="10"
    )
    return make_response(kml.kml(), 200, {"Content-Type": "application/xml"})
=======

    kml.newpoint(name="dummy", coords=[(37.3483333333, -121.9353888889)], description="0.5")

    return make_response(kml.kml(), 200, {'Content-Type': 'application/xml'})
>>>>>>> 457d152472b9b3170f83434c4a0715bfd7d71205
