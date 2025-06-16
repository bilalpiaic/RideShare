from app import db
from models import Ride, User
from services.pricing_service import calculate_ride_price
import random
from datetime import datetime

class RideService:
    @staticmethod
    def create_ride(rider_id, pickup_address, dropoff_address, pickup_coords=None, dropoff_coords=None, notes=None):
        """Create a new ride request"""
        # Mock distance calculation (in real app, use Google Maps API)
        distance_km = RideService._calculate_mock_distance(pickup_coords, dropoff_coords)
        estimated_duration = max(15, int(distance_km * 2.5))  # Mock estimation
        
        # Calculate price
        price = calculate_ride_price(distance_km, estimated_duration)
        
        ride = Ride(
            rider_id=rider_id,
            pickup_address=pickup_address,
            dropoff_address=dropoff_address,
            pickup_lat=pickup_coords[0] if pickup_coords else None,
            pickup_lng=pickup_coords[1] if pickup_coords else None,
            dropoff_lat=dropoff_coords[0] if dropoff_coords else None,
            dropoff_lng=dropoff_coords[1] if dropoff_coords else None,
            distance_km=distance_km,
            estimated_duration=estimated_duration,
            price=price,
            notes=notes
        )
        
        db.session.add(ride)
        db.session.commit()
        
        # Try to assign a driver
        RideService.assign_driver(ride.id)
        
        return ride
    
    @staticmethod
    def assign_driver(ride_id):
        """Assign an available driver to the ride"""
        ride = Ride.query.get(ride_id)
        if not ride or ride.driver_id:
            return False
        
        # Find available drivers
        available_drivers = User.query.filter_by(
            role='driver',
            is_available=True
        ).all()
        
        if available_drivers:
            # Simple assignment - pick random driver (in real app, use location-based matching)
            driver = random.choice(available_drivers)
            ride.driver_id = driver.id
            ride.status = 'accepted'
            ride.accepted_at = datetime.now()
            
            # Mark driver as busy
            driver.is_available = False
            
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def update_ride_status(ride_id, status, user_id=None):
        """Update ride status"""
        ride = Ride.query.get(ride_id)
        if not ride:
            return False
        
        # Verify user has permission to update this ride
        if user_id and user_id not in [ride.rider_id, ride.driver_id]:
            return False
        
        ride.status = status
        
        if status == 'in_progress':
            ride.started_at = datetime.now()
        elif status == 'completed':
            ride.completed_at = datetime.now()
            # Make driver available again
            if ride.driver:
                ride.driver.is_available = True
                ride.driver.total_rides += 1
            if ride.rider:
                ride.rider.total_rides += 1
        elif status == 'cancelled':
            # Make driver available again if assigned
            if ride.driver:
                ride.driver.is_available = True
        
        db.session.commit()
        return True
    
    @staticmethod
    def get_user_rides(user_id, role='rider'):
        """Get rides for a user"""
        if role == 'driver':
            return Ride.query.filter_by(driver_id=user_id).order_by(Ride.requested_at.desc()).all()
        else:
            return Ride.query.filter_by(rider_id=user_id).order_by(Ride.requested_at.desc()).all()
    
    @staticmethod
    def _calculate_mock_distance(pickup_coords, dropoff_coords):
        """Mock distance calculation (replace with Google Maps API in production)"""
        if pickup_coords and dropoff_coords:
            # Simple Euclidean distance approximation
            lat_diff = pickup_coords[0] - dropoff_coords[0]
            lng_diff = pickup_coords[1] - dropoff_coords[1]
            distance = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111  # Rough km conversion
            return max(1.0, round(distance, 2))
        else:
            # Random distance for mock purposes
            return round(random.uniform(2.0, 25.0), 2)
