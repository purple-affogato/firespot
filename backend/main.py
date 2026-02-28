from flask import Flask, make_response
import simplekml

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
    
@app.route("/get-map", methods=["GET"])
def get_map():
    kml = simplekml.Kml()
    pnt = kml.newpoint(name="dummy", coords=[(37.3483333333, -121.9353888889)], description="10")
    return make_response(kml.kml(), 200, {'Content-Type': 'application/xml'})