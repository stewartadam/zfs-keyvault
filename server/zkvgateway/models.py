import datetime
from zkvgateway import db

class KeyRequest(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  pin = db.Column(db.Integer, unique=True, nullable=False)
  approved = db.Column(db.Boolean, default=False, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  approved_at = db.Column(db.DateTime, nullable=True, default=None)

# Create the database tables.
db.create_all()
