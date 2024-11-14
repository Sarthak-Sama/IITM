from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    fullname = db.Column(db.String(150))
    address = db.Column(db.String(250))
    pincode = db.Column(db.String(6))

    is_blacklisted = db.Column(db.Boolean, default=False)


class ServiceProfessional(db.Model):
    __tablename__ = 'professionals'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    fullname = db.Column(db.String(150))
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    service_type = db.Column(db.String(100))
    experience = db.Column(db.Integer)
    address = db.Column(db.String(250))
    pincode = db.Column(db.String(6))
    is_verified = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    
    is_blacklisted = db.Column(db.Boolean, default=False)

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(250))
    time_required = db.Column(db.String(50))

class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    date_of_request = db.Column(db.DateTime, default=db.func.now())
    date_of_completion = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='requested')
    rating = db.Column(db.Integer)
    remarks = db.Column(db.String(250))

    service = db.relationship('Service', backref='requests')
    customer = db.relationship('Customer', backref='requests')
    professional = db.relationship('ServiceProfessional', backref='requests')
