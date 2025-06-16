#!/usr/bin/env python3
"""
Setup script to populate the ride-sharing platform with demo data
"""

import json
from datetime import datetime, timedelta
from app import app, db
from models import User, Ride, Payment
import random

def create_demo_data():
    """Create demo riders, drivers, and rides for testing"""
    
    with app.app_context():
        print("Setting up demo data for RideShare platform...")
        
        # Sample rider data
        demo_riders = [
            {
                'id': 'rider_demo_1',
                'email': 'alice.rider@example.com',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'role': 'rider',
                'phone': '+1-555-0101',
                'rating': 4.9,
                'total_rides': 45
            },
            {
                'id': 'rider_demo_2', 
                'email': 'bob.rider@example.com',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'role': 'rider',
                'phone': '+1-555-0102',
                'rating': 4.7,
                'total_rides': 32
            },
            {
                'id': 'rider_demo_3',
                'email': 'carol.rider@example.com',
                'first_name': 'Carol',
                'last_name': 'Davis',
                'role': 'rider', 
                'phone': '+1-555-0103',
                'rating': 4.8,
                'total_rides': 67
            }
        ]
        
        # Sample driver data with locations around NYC
        demo_drivers = [
            {
                'id': 'driver_demo_1',
                'email': 'david.driver@example.com',
                'first_name': 'David',
                'last_name': 'Martinez',
                'role': 'driver',
                'phone': '+1-555-0201',
                'vehicle_info': json.dumps({
                    'make': 'Honda',
                    'model': 'Accord',
                    'year': '2021',
                    'license_plate': 'NYC-001',
                    'color': 'Silver'
                }),
                'is_available': True,
                'rating': 4.9,
                'total_rides': 234,
                'current_lat': 40.7505,
                'current_lng': -73.9934,
                'location_updated_at': datetime.now()
            },
            {
                'id': 'driver_demo_2',
                'email': 'emma.driver@example.com', 
                'first_name': 'Emma',
                'last_name': 'Thompson',
                'role': 'driver',
                'phone': '+1-555-0202',
                'vehicle_info': json.dumps({
                    'make': 'Toyota',
                    'model': 'Prius',
                    'year': '2020',
                    'license_plate': 'NYC-002',
                    'color': 'Blue'
                }),
                'is_available': True,
                'rating': 4.8,
                'total_rides': 189,
                'current_lat': 40.7614,
                'current_lng': -73.9776,
                'location_updated_at': datetime.now()
            },
            {
                'id': 'driver_demo_3',
                'email': 'frank.driver@example.com',
                'first_name': 'Frank',
                'last_name': 'Garcia',
                'role': 'driver',
                'phone': '+1-555-0203',
                'vehicle_info': json.dumps({
                    'make': 'Nissan',
                    'model': 'Sentra',
                    'year': '2019',
                    'license_plate': 'NYC-003',
                    'color': 'White'
                }),
                'is_available': False,
                'rating': 4.7,
                'total_rides': 145,
                'current_lat': 40.7282,
                'current_lng': -74.0776,
                'location_updated_at': datetime.now()
            }
        ]
        
        # Create demo users
        for rider_data in demo_riders:
            existing = User.query.get(rider_data['id'])
            if not existing:
                rider = User(**rider_data)
                db.session.add(rider)
                print(f"Created demo rider: {rider.first_name} {rider.last_name}")
        
        for driver_data in demo_drivers:
            existing = User.query.get(driver_data['id'])
            if not existing:
                driver = User(**driver_data)
                db.session.add(driver)
                print(f"Created demo driver: {driver.first_name} {driver.last_name}")
        
        db.session.commit()
        
        # Sample ride data
        demo_rides = [
            {
                'rider_id': 'rider_demo_1',
                'driver_id': 'driver_demo_1',
                'pickup_address': '350 5th Ave, New York, NY 10118, USA',  # Empire State Building
                'pickup_lat': 40.7484,
                'pickup_lng': -73.9857,
                'dropoff_address': '1 World Trade Center, New York, NY 10007, USA',  # One WTC
                'dropoff_lat': 40.7127,
                'dropoff_lng': -74.0134,
                'distance_km': 4.2,
                'estimated_duration': 18,
                'price': 15.60,
                'status': 'completed',
                'requested_at': datetime.now() - timedelta(hours=2),
                'accepted_at': datetime.now() - timedelta(hours=2, minutes=-5),
                'started_at': datetime.now() - timedelta(hours=1, minutes=45),
                'completed_at': datetime.now() - timedelta(hours=1, minutes=27),
                'notes': 'Please wait at the main entrance'
            },
            {
                'rider_id': 'rider_demo_2',
                'driver_id': 'driver_demo_2', 
                'pickup_address': 'Central Park, New York, NY, USA',
                'pickup_lat': 40.7829,
                'pickup_lng': -73.9654,
                'dropoff_address': 'Brooklyn Bridge, New York, NY, USA',
                'dropoff_lat': 40.7061,
                'dropoff_lng': -73.9969,
                'distance_km': 6.8,
                'estimated_duration': 25,
                'price': 22.40,
                'status': 'in_progress',
                'requested_at': datetime.now() - timedelta(minutes=30),
                'accepted_at': datetime.now() - timedelta(minutes=25),
                'started_at': datetime.now() - timedelta(minutes=15),
                'notes': None
            },
            {
                'rider_id': 'rider_demo_3',
                'driver_id': None,
                'pickup_address': 'Times Square, New York, NY, USA',
                'pickup_lat': 40.7580,
                'pickup_lng': -73.9855,
                'dropoff_address': 'Statue of Liberty, New York, NY, USA',
                'dropoff_lat': 40.6892,
                'dropoff_lng': -74.0445,
                'distance_km': 8.5,
                'estimated_duration': 35,
                'price': 28.75,
                'status': 'pending',
                'requested_at': datetime.now() - timedelta(minutes=5),
                'notes': 'Need large vehicle for luggage'
            }
        ]
        
        # Create demo rides
        for ride_data in demo_rides:
            ride = Ride(**ride_data)
            db.session.add(ride)
            print(f"Created demo ride from {ride.pickup_address[:30]}... to {ride.dropoff_address[:30]}...")
        
        db.session.commit()
        
        # Create demo payments for completed rides
        completed_rides = Ride.query.filter_by(status='completed').all()
        for ride in completed_rides:
            existing_payment = Payment.query.filter_by(ride_id=ride.id).first()
            if not existing_payment:
                payment = Payment(
                    ride_id=ride.id,
                    rider_id=ride.rider_id,
                    driver_id=ride.driver_id,
                    amount=ride.price,
                    status='completed',
                    payment_method='mock',
                    transaction_id=f"demo_{ride.id}_{random.randint(1000, 9999)}",
                    processed_at=ride.completed_at + timedelta(minutes=2)
                )
                db.session.add(payment)
                print(f"Created demo payment for ride #{ride.id}")
        
        db.session.commit()
        print("\nDemo data setup completed successfully!")
        print("\nDemo accounts created:")
        print("Riders: alice.rider@example.com, bob.rider@example.com, carol.rider@example.com")
        print("Drivers: david.driver@example.com, emma.driver@example.com, frank.driver@example.com")
        print("\nYou can now test the platform with realistic data!")

if __name__ == '__main__':
    create_demo_data()