from flask import Flask, make_response
import simplekml
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
    
@app.route("/get-map", methods=["GET"])
def get_map():
    kml = simplekml.Kml()
    
    cred = credentials.Certificate("firespot-331a1-firebase-adminsdk-fbsvc-43fc2da019.json")
    firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    docs = db.collection("firepoints").stream()
    
    for d in docs:
        kml.newpoint(name=d.get('name'), coords=[(d.get('latitude'), d.get('longitude'))], description=str(d.get('intensity')))

    return make_response(kml.kml(), 200, {'Content-Type': 'application/xml'})