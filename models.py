from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import os
 
app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:114514YjU@localhost/residential"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app,session_options={"autoflush": False})
migrate=Migrate(app,db) #Initializing migrate.
manager = Manager(app)
manager.add_command('db',MigrateCommand)
 
class Apartment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    address = db.Column(db.String, unique=False, nullable=True)
    delete = db.Column(db.Boolean, unique=False, nullable=True, default=True)
    residents = db.relationship('Residents', backref='apartment', lazy=True, order_by='Residents.fullName')
    def __repr__(self):
            return '<Apartment %r>' % self.name
class Residents(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String, unique=True, nullable=False)
    transferAmount = db.Column(db.Integer, unique=False, nullable=True)
    transferSatisfiedMonth = db.Column(db.Date, unique=False, nullable=True)
    guaranteeCompany = db.Column(db.String, unique=False, nullable=True)
    roomNo = db.Column(db.String, unique=False, nullable=True)
    parkingLotNo = db.Column(db.String, unique=False, nullable=True)
    apartment_id = db.Column(db.Integer, db.ForeignKey('apartment.id'), nullable=False)
    delete = db.Column(db.Boolean, unique=False, nullable=True, default=True)
    transfer = db.relationship('Transfer', backref='residents', lazy=True, order_by='desc(Transfer.transferDate)')
    billing = db.relationship('Billing', backref='residents', lazy=True, order_by='desc(Billing.billingDate)')
    def __repr__(self):
            return '<Residents %r>' % self.fullName
 
class Transfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transferDate = db.Column(db.Date, unique=False, nullable=False)
    transferAmount = db.Column(db.Integer, unique=False, nullable=False)
    residents_id = db.Column(db.Integer, db.ForeignKey('residents.id'), nullable=False)

class Billing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    billingDate = db.Column(db.Date, unique=False, nullable=False)
    residents_id = db.Column(db.Integer, db.ForeignKey('residents.id'), nullable=False)

if __name__ == "__main__":
     manager.run()
