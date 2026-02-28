import firebase_admin
from firebase_admin import credentials, firestore

def read_data():
    print("--- Reading Data from Firestore")
    
    cred = credentials.Certificate("firespot-331a1-firebase-adminsdk-fbsvc-43fc2da019.json")
    firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    docs = db.collection("firepoints").stream()
    
    for d in docs:
        print(d.to_dict())
        
        
read_data()