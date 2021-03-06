from flask import Flask, abort
from flask_cors import CORS
from flask_restplus import Resource, Api, fields, reqparse
from models import app, db, Apartment, Residents, Transfer, Billing
import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import extract  

# app = Flask(__name__)
CORS(app)
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
    'lastTransferDate': fields.String,
    'lastTransferAmount':fields.Integer,
    'lastBillingDate': fields.String,
    # 'transfer': fields.Nested(model_transfer),
    # 'billing': fields.Nested(model_billing),
})
model_single_resident = model_residents.clone('Residents_Single', {
    'transfer': fields.Nested(model_transfer),
    'billing': fields.Nested(model_billing),
    'apartment_id': fields.Integer,
    'apartmentName': fields.String,
})
model_apartment = api.model('Apartment', {
    'id': fields.Integer,
    'name': fields.String,
    'address': fields.String,
    'residents': fields.Nested(model_residents),
    'transferSummary': fields.List(fields.Integer),

})

apartment_parser = reqparse.RequestParser()
apartment_parser.add_argument('name', location='json', required=True)
apartment_parser.add_argument('address', location='json')

apartment_update_parser = apartment_parser.copy()
apartment_update_parser.add_argument('id', type=int, location='json', required=True)

apartment_summary_parser = reqparse.RequestParser()
apartment_summary_parser.add_argument('id', type=int, location='args')
apartment_summary_parser.add_argument('startMonth', type=int, location='args')
apartment_summary_parser.add_argument('startYear', type=int, location='args')
apartment_summary_parser.add_argument('span', type=int, location='args')

residents_parser = reqparse.RequestParser()
residents_parser.add_argument('fullName', location='json', required=True)
residents_parser.add_argument('transferAmount', type=int, location='json')
residents_parser.add_argument('transferSatisfiedMonth', location='json')
residents_parser.add_argument('guaranteeCompany', location='json')
residents_parser.add_argument('roomNo', location='json')
residents_parser.add_argument('parkingLotNo', location='json')
residents_parser.add_argument('apartment_id', type=int, location='json')

residents_get_parser = reqparse.RequestParser()
residents_get_parser.add_argument('apartment_id', location='args')
residents_get_parser.add_argument('billing', location='args')
residents_get_parser.add_argument('id', location='args')

residents_delete_parser = reqparse.RequestParser()
residents_delete_parser.add_argument("id", location='args')

residents_update_parser = residents_parser.copy()
residents_update_parser.add_argument('id', type = int, location='json', required=True)

transfer_parser = reqparse.RequestParser()
transfer_parser.add_argument('transferDate', location='json', required=True)
transfer_parser.add_argument('transferAmount', type=int, location='json', required=True)
transfer_parser.add_argument('residents_id', type=int, location='json', required=True)

transfer_delete_parser = reqparse.RequestParser()
transfer_delete_parser.add_argument('id', type=int, location='args', required=True)

billing_parser = reqparse.RequestParser()
billing_parser.add_argument('billingDate', location='json', required=True)
billing_parser.add_argument('residents_id', type=int, location='json', required=True)

billing_delete_parser = reqparse.RequestParser()
billing_delete_parser.add_argument('id', type=int, location='args', required=True)

@api.route('/apartment')
class GetApartments(Resource):
    def calcSummary(self, id, month, year):
        apartment = Apartment.query.get(id)
        residentSum = []
        for resident in apartment.residents:
            transfer = (
                db.session.query(Transfer)
                .filter(extract('month',Transfer.transferDate)==month)
                .filter(extract('year',Transfer.transferDate)==year)
                .filter(Transfer.residents_id == resident.id)
                .all()
                )
            amounts = sum([tr.transferAmount for tr in transfer])
            residentSum.append(amounts)
        total = sum(residentSum)
        return total
    def calcMultipleSummary(self, ap, deltaDates):
        total = [self.calcSummary(ap.id, deltaMonth.month, deltaMonth.year) for deltaMonth in deltaDates]
        re = Residents.query.filter_by(apartment_id = ap.id).filter_by(delete=False).order_by(Residents.fullName).all()
        setattr(ap, 'residents', re)
        setattr(ap, 'transferSummary', total)
        return ap
    @api.marshal_with(model_apartment)
    def get(self):
        args= apartment_summary_parser.parse_args()
        if (args['id'] and args['startMonth'] and args['startYear'] and args['span']):
            # return month income summary 
            total = []
            deltas = [i for i in range(-args['span']+1, 1, 1)]
            now = datetime.date(args['startYear'], args['startMonth'], 1)
            deltaDates = [now + relativedelta(months=+delta) for delta in deltas]
            for deltaMonth in deltaDates:
                total.append(self.calcSummary(args['id'], deltaMonth.month, deltaMonth.year))
            ap = Apartment.query.get(args['id'])
            re = Residents.query.filter_by(apartment_id = args['id']).filter_by(delete=False).order_by(Residents.fullName).all()
            if (re):
                setattr(ap, 'residents', re)
            else:
                setattr(ap, 'residents', [])
            setattr(ap, 'transferSummary', total)
        elif (args['startMonth'] and args['startYear'] and args['span']):
            apbef = Apartment.query.all()
            deltas = [i for i in range(-args['span']+1, 1, 1)]
            now = datetime.date(args['startYear'], args['startMonth'], 1)
            deltaDates = [now + relativedelta(months=+delta) for delta in deltas]
            ap = []
            for idx,apartment in enumerate(apbef):
                ap.append(self.calcMultipleSummary(apartment, deltaDates))
        elif (args['id']):
            re = Residents.query.filter_by(apartment_id = args['id']).filter_by(delete=False).order_by(Residents.fullName).all()
            ap = Apartment.query.filter_by(id=args['id']).all()
            setattr(ap[0], 'residents', re)
        else:
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
        ap = Apartment.query.get(args['id'])
        if ap == None:
            abort(400)
        ap.name = args['name']
        ap.address = args['address']
        db.session.add(ap)
        db.session.commit()
        return "success"
    def delete(self):
        args = apartment_delete_parser.parse_args()
        ap = Apartment.query.get(args['id'])
        if ap == None:
            abort(400)
        ap.delete = True
        db.session.add(ap)
        db.session.commit()
        return "success"

@api.route('/residents/<int:id>')
class GetResidentDetail(Resource):
    @api.marshal_with(model_single_resident)
    def get(self, id):
        res = Residents.query.filter_by(id=id).filter_by(delete=False).all()
        if(res):
            setattr(res[0], 'apartment_id', res[0].apartment.id)
            setattr(res[0], 'apartmentName', res[0].apartment.name)
        return res
@api.route('/residents')
class GetResidents(Resource):
    @api.marshal_with(model_residents)
    def get(self):
        req = residents_get_parser.parse_args()
        if (req['apartment_id']):
            # if apartment id is specified
            res = Residents.query.filter_by(apartment_id=req['apartment_id']).order_by(Residents.fullName).all()
        elif (req['id']):
            # if id is specified
            res = Residents.query.filter_by(id=req['id']).filter_by(delete=False).all()
        elif (req['billing']):
            # if billing mode, return all residents who uses billing company
            res = Residents.query.filter(Residents.guaranteeCompany != None).filter_by(delete=False).order_by(Residents.fullName).all()
        else:
            # or get all
            res = Residents.query.filter_by(delete=False).order_by(Residents.fullName).all()
        
        for idx, re in enumerate(res):
            # get latest treansfer and set to res
            if(re.transfer):
                setattr(res[idx], 'lastTransferDate', re.transfer[0].transferDate)
                setattr(res[idx], 'lastTransferAmount', re.transfer[0].transferAmount)
            if(re.billing):
                setattr(res[idx], 'lastBillingDate', re.billing[0].billingDate)
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
        res = Residents.query.get(args["id"])
        for key, value in args.items():
            setattr(res, key, value)                
        db.session.add(res)
        db.session.commit()
        return "success"
    def delete(self):
        args = residents_delete_parser.parse_args()
        res = Residents.query.get(args["id"])
        res.delete = True
        db.session.add(res)
        db.session.commit()
        return "success"

@api.route('/transfer')
class CreateTransfer(Resource):
    # create new transfer
    def post(self):
        args = transfer_parser.parse_args()
        
        # if same date record has alredy been existing
        if(Transfer.query.filter_by(transferDate=args['transferDate']).filter_by(residents_id=args['residents_id'])).all():
            # return "resource already exists", 409, {'Access-Control-Allow-Origin':'*'}
            abort(409)
        tr = Transfer(**args)
        # get latest transfer and compare 
        newDate = datetime.datetime.strptime(args['transferDate'], "%Y-%m-%d").date()
        trBefore = Transfer.query.filter_by(residents_id=args['residents_id']).order_by(Transfer.transferDate.desc()).first()
        if (trBefore and newDate > trBefore.transferDate):
            # increment resident's transferSatisfiedMonth
            re = Residents.query.get(args['residents_id'])
            if(re.transferSatisfiedMonth):
                re.transferSatisfiedMonth = re.transferSatisfiedMonth + relativedelta(months=+1)
                db.session.add(re)

        db.session.add(tr)
        db.session.commit()
        return "success"
        
    def delete(self):
        args = transfer_delete_parser.parse_args()
        tr = Transfer.query.get(args['id'])
        db.session.delete(tr)
        db.session.commit()
        return "success", 204
    # def option(self):
    #     return "", 200, {'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers', '*'}

@api.route('/billing')
class CreateBilling(Resource):
    def post(self):
        args = billing_parser.parse_args()
        # if same date record has alredy been existing
        if(Billing.query.filter_by(billingDate=args['billingDate']).filter_by(residents_id=args['residents_id'])).all():
            abort(409)
        br = Billing(**args)
        db.session.add(br)
        db.session.commit()
        return "success"
    def delete(self):
        args = billing_delete_parser.parse_args()
        br = Billing.query.get(args['id'])
        db.session.delete(br)
        db.session.commit()
        return "success"
if __name__ == '__main__':
    app.run(debug=True)