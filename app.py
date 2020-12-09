from flask import Flask, abort
from flask_restplus import Resource, Api, fields, reqparse
from models import app, db, Apartment, Residents, Transfer, Billing
import datetime

# app = Flask(__name__)
api = Api(app)

model_billing = api.model('Billing', {
    'id': fields.Integer,
    'billingDate': fields.Date,
})
model_transfer = api.model('Transfer', {
    'id': fields.Integer,
    'transferDate': fields.Date,
    'transferAmount': fields.Integer,
})

model_residents = api.model('Residents', {
    'id': fields.Integer,
    'fullName': fields.String,
    'transferAmount': fields.Integer,
    'transferSatisfiedMonth': fields.Date,
    'guaranteeCompany': fields.String,
    'roomNo': fields.String,
    'parkingLotNo': fields.String,
    # 'transfer': fields.Nested(model_transfer),
    # 'billing': fields.Nested(model_billing),
})
model_single_resident = model_residents.clone('Residents', {
    'transfer': fields.Nested(model_transfer),
    'billing': fields.Nested(model_billing),
})
model_apartment = api.model('Apartment', {
    'id': fields.Integer,
    'name': fields.String,
    'address': fields.String,
    # 'residents': fields.Nested(model_residents),
})

apartment_parser = reqparse.RequestParser()
apartment_parser.add_argument('name', location='json', required=True)
apartment_parser.add_argument('address', location='json')

apartment_update_parser = apartment_parser.copy()
apartment_update_parser.add_argument('id', type=int, location='json', required=True)

residents_parser = reqparse.RequestParser()
residents_parser.add_argument('fullName', location='json', required=True)
residents_parser.add_argument('transferAmount', type=int, location='json')
residents_parser.add_argument('transferSatisfiedMonth', location='json')
residents_parser.add_argument('guaranteeCompany', location='json')
residents_parser.add_argument('roomNo', location='json')
residents_parser.add_argument('parkingLotNo', location='json')
residents_parser.add_argument('apartment_id', type=int, location='json')

residents_update_parser = residents_parser.copy()
residents_update_parser.add_argument('id', type = int, location='json', required=True)

transfer_parser = reqparse.RequestParser()
transfer_parser.add_argument('transferDate', location='json', required=True)
transfer_parser.add_argument('transferAmount', type=int, location='json', required=True)
transfer_parser.add_argument('residents_id', type=int, location='json', required=True)

transfer_delete_parser = reqparse.RequestParser()
transfer_delete_parser.add_argument('id', type=int, location='json', required=True)

billing_parser = reqparse.RequestParser()
billing_parser.add_argument('billingDate', type=datetime, location='json', required=True)
billing_parser.add_argument('residents_id', type=int, location='json', required=True)

billing_delete_parser = reqparse.RequestParser()
billing_delete_parser.add_argument('id', type=int, location='json', required=True)

@api.route('/apartment')
class GetApartments(Resource):
    @api.marshal_with(model_apartment, envelope='resource')
    def get(self):
        ap = Apartment.query.all()
        return ap
    def post(self):
        args = apartment_parser.parse_args()
        ap = Apartment(**args)
        db.session.add(ap)
        db.session.commit()
        return "success"  
    def put(self):
        args = apartment_update_parser.parse_args()
        ap = Apartment.query.filter_by(id=args['id']).first()
        if ap == None:
            abort(400)
        ap.name = args['name']
        ap.address = args['address']
        db.session.add(ap)
        db.session.commit()
        return "success"


@api.route('/residents/<int:id>')
class GetResidentDetail(Resource):
    @api.marshal_with(model_single_resident)
    def get(self, id):
        res = Residents.query.filter_by(id=id).first()
        return res
@api.route('/residents')
class GetResidents(Resource):
    @api.marshal_with(model_residents)
    def get(self):
        res = Residents.query.all()
        return res
    # create
    def post(self):
        args = residents_parser.parse_args()
        res = Residents(**args)
        db.session.add(res)
        db.session.commit()
        return "success"
    # update
    def put(self):
        args = residents_update_parser.parse_args()
        res = Residents.query.filter_by(id=args["id"]).first()
        for key, value in args.items():
            setattr(res, key, value)                
        db.session.add(res)
        db.session.commit()
        return "success"

@api.route('/transfer')
class CreateTransfer(Resource):
    def post(self):
        args = transfer_parser.parse_args()
        tr = Transfer(**args)
        db.session.add(tr)
        db.session.commit()
        return "success"
    def delete(self):
        args = transfer_delete_parser.parse_args()
        tr = Transfer.query.filter_by(id=args['id']).first()
        db.session.delete(tr)
        db.session.commit()
        return "success", 204
@api.route('/billing')
class CreateBilling(Resource):
    def post(self):
        args = billing_parser.parse_args()
        br = Billing(**args)
        db.session.add(br)
        db.session.commit()
        return "success"
    def delete(self):
        args = billing_delete_parser.parse_args()
        br = Billing.query.filter_by(id=args['id']).first()
        db.session.delete(br)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)