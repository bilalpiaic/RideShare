import requests
import os
from datetime import datetime
from app import db
from models import User
import math

class LocationService:
    @staticmethod
    def get_google_maps_api_key():
        """Get Google Maps API key from environment"""
        return os.environ.get('GOOGLE_MAPS_API_KEY')
    
    @staticmethod
    def geocode_address(address):
        """Geocode an address using Google Maps API"""
        api_key = LocationService.get_google_maps_api_key()
        if not api_key:
            return None
            
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location = result['geometry']['location']
                return {
                    'lat': location['lat'],
                    'lng': location['lng'],
                    'formatted_address': result['formatted_address'],
                    'place_id': result.get('place_id')
                }
        except Exception as e:
            print(f"Geocoding error: {e}")
            
        return None
    
    @staticmethod
    def calculate_distance_matrix(origins, destinations):
        """Calculate distance and duration between origins and destinations"""
        api_key = LocationService.get_google_maps_api_key()
        if not api_key:
            return None
            
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        
        # Format origins and destinations
        origins_str = "|".join([f"{o['lat']},{o['lng']}" for o in origins])
        destinations_str = "|".join([f"{d['lat']},{d['lng']}" for d in destinations])
        
        params = {
            'origins': origins_str,
            'destinations': destinations_str,
            'units': 'metric',
            'mode': 'driving',
            'key': api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK':
                return data
        except Exception as e:
            print(f"Distance matrix error: {e}")
            
        return None
    
    @staticmethod
    def update_driver_location(driver_id, lat, lng):
        """Update driver's current location"""
        driver = User.query.get(driver_id)
        if driver and driver.role == 'driver':
            driver.current_lat = lat
            driver.current_lng = lng
            driver.location_updated_at = datetime.now()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def find_nearby_drivers(lat, lng, radius_km=10):
        """Find available drivers within specified radius"""
        # Get all available drivers with location data
        drivers = User.query.filter_by(
            role='driver',
            is_available=True
        ).filter(
            User.current_lat.isnot(None),
            User.current_lng.isnot(None)
        ).all()
        
        nearby_drivers = []
        
        for driver in drivers:
            distance = LocationService._calculate_haversine_distance(
                lat, lng, driver.current_lat, driver.current_lng
            )
            
            if distance <= radius_km:
                nearby_drivers.append({
                    'driver_id': driver.id,
                    'name': f"{driver.first_name or ''} {driver.last_name or ''}".strip(),
                    'lat': driver.current_lat,
                    'lng': driver.current_lng,
                    'distance_km': round(distance, 2),
                    'rating': driver.rating,
                    'total_rides': driver.total_rides,
                    'vehicle_info': driver.vehicle_info
                })
        
        # Sort by distance
        nearby_drivers.sort(key=lambda x: x['distance_km'])
        return nearby_drivers
    
    @staticmethod
    def _calculate_haversine_distance(lat1, lng1, lat2, lng2):
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def get_place_autocomplete(input_text, location=None):
        """Get place autocomplete suggestions from Google Places API"""
        api_key = LocationService.get_google_maps_api_key()
        if not api_key:
            return []
            
        url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
        params = {
            'input': input_text,
            'key': api_key,
            'types': 'establishment|geocode'
        }
        
        # Add location bias if provided
        if location:
            params['location'] = f"{location['lat']},{location['lng']}"
            params['radius'] = 50000  # 50km radius
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK':
                suggestions = []
                for prediction in data.get('predictions', []):
                    suggestions.append({
                        'place_id': prediction['place_id'],
                        'description': prediction['description'],
                        'main_text': prediction['structured_formatting'].get('main_text', ''),
                        'secondary_text': prediction['structured_formatting'].get('secondary_text', '')
                    })
                return suggestions
        except Exception as e:
            print(f"Autocomplete error: {e}")
            
        return []
    
    @staticmethod
    def get_place_details(place_id):
        """Get detailed information about a place using place_id"""
        api_key = LocationService.get_google_maps_api_key()
        if not api_key:
            return None
            
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'place_id': place_id,
            'fields': 'geometry,formatted_address,name',
            'key': api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and 'result' in data:
                result = data['result']
                location = result['geometry']['location']
                return {
                    'lat': location['lat'],
                    'lng': location['lng'],
                    'formatted_address': result.get('formatted_address'),
                    'name': result.get('name')
                }
        except Exception as e:
            print(f"Place details error: {e}")
            
        return None