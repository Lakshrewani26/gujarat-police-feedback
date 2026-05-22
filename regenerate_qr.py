from app import app, generate_qr_for_station
from models import db, PoliceStation

with app.app_context():
    stations = PoliceStation.query.all()
    for s in stations:
        generate_qr_for_station(s)
    db.session.commit()
    print("QR codes regenerated!")