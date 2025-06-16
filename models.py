from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    
    # Ride-sharing specific fields
    role = db.Column(db.String(20), nullable=False, default='rider')  # 'rider' or 'driver'
    phone = db.Column(db.String(20), nullable=True)
    vehicle_info = db.Column(db.Text, nullable=True)  # JSON string for driver vehicle details
    is_available = db.Column(db.Boolean, default=True)  # For drivers
    rating = db.Column(db.Float, default=5.0)
    total_rides = db.Column(db.Integer, default=0)
    
    # Location tracking for drivers
    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)
    location_updated_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    rider_rides = db.relationship('Ride', foreign_keys='Ride.rider_id', backref='rider', lazy='dynamic')
    driver_rides = db.relationship('Ride', foreign_keys='Ride.driver_id', backref='driver', lazy='dynamic')

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

class Ride(db.Model):
    __tablename__ = 'rides'
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    driver_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    
    pickup_address = db.Column(db.String(500), nullable=False)
    pickup_lat = db.Column(db.Float, nullable=True)
    pickup_lng = db.Column(db.Float, nullable=True)
    
    dropoff_address = db.Column(db.String(500), nullable=False)
    dropoff_lat = db.Column(db.Float, nullable=True)
    dropoff_lng = db.Column(db.Float, nullable=True)
    
    distance_km = db.Column(db.Float, nullable=True)
    estimated_duration = db.Column(db.Integer, nullable=True)  # in minutes
    
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, accepted, in_progress, completed, cancelled
    
    requested_at = db.Column(db.DateTime, default=datetime.now)
    accepted_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Special requests or notes
    notes = db.Column(db.Text, nullable=True)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    rider_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    driver_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed, refunded
    payment_method = db.Column(db.String(50), default='mock')  # mock, stripe, etc.
    transaction_id = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    ride = db.relationship('Ride', backref='payment')
    rider = db.relationship('User', foreign_keys=[rider_id])
    driver = db.relationship('User', foreign_keys=[driver_id])
