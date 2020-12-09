from flask_restplus import reqparse

apartment_parser = reqparse.RequestParser()
apartment_parser.add_argument('name', location='json', required=True)
apartment_parser.add_argument('address', location='json')

apartment_update_parser = reqparse.RequestParser()
apartment_update_parser.add_argument('id', type=int, location='json', required=True)
apartment_update_parser.add_argument('name', location='json', required=True)
apartment_update_parser.add_argument('address', location='json')

residents_parser = reqparse.RequestParser()
residents_parser.add_argument('fullName', location='json', required=True)
