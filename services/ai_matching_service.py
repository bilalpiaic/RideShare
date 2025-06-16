import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
from app import db
from models import User, Ride
from services.location_service import LocationService

class AIMatchingService:
    """AI-powered driver matching using Google Gemini 2.0"""
    
    def __init__(self):
        # Configure Gemini API
        api_key = os.environ.get('GOOGLE_AI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
            logging.warning("Google AI API key not found. AI matching will use basic algorithm.")
    
    def find_optimal_driver(self, ride_request: Dict) -> Optional[User]:
        """
        Find the optimal driver for a ride request using AI analysis
        """
        # Get available drivers near pickup location
        nearby_drivers = LocationService.find_nearby_drivers(
            ride_request['pickup_lat'], 
            ride_request['pickup_lng'],
            radius_km=15
        )
        
        if not nearby_drivers:
            return None
        
        # Use AI to analyze and rank drivers if available
        if self.model:
            return self._ai_driver_selection(ride_request, nearby_drivers)
        else:
            return self._basic_driver_selection(ride_request, nearby_drivers)
    
    def _ai_driver_selection(self, ride_request: Dict, drivers: List[User]) -> Optional[User]:
        """
        Use Gemini AI to intelligently select the best driver
        """
        try:
            # Prepare driver data for AI analysis
            driver_data = []
            for driver in drivers:
                # Get driver's recent performance
                recent_rides = db.session.query(Ride).filter(
                    Ride.driver_id == driver.id,
                    Ride.completed_at >= datetime.now() - timedelta(days=30),
                    Ride.status == 'completed'
                ).limit(10).all()
                
                # Calculate distance to pickup
                distance = LocationService._calculate_haversine_distance(
                    driver.current_lat, driver.current_lng,
                    ride_request['pickup_lat'], ride_request['pickup_lng']
                )
                
                # Parse vehicle info
                vehicle_info = json.loads(driver.vehicle_info) if driver.vehicle_info else {}
                
                driver_profile = {
                    'driver_id': driver.id,
                    'rating': float(driver.rating),
                    'total_rides': driver.total_rides,
                    'recent_rides_count': len(recent_rides),
                    'distance_to_pickup_km': round(distance, 2),
                    'vehicle_type': vehicle_info.get('type', 'sedan'),
                    'vehicle_year': vehicle_info.get('year', 2020),
                    'is_available': driver.is_available,
                    'location_updated_minutes_ago': self._get_location_freshness(driver),
                    'acceptance_rate': self._calculate_acceptance_rate(driver)
                }
                driver_data.append(driver_profile)
            
            # Create AI prompt for driver selection
            prompt = self._create_matching_prompt(ride_request, driver_data)
            
            # Get AI recommendation
            response = self.model.generate_content(prompt)
            result = self._parse_ai_response(response.text)
            
            if result and 'selected_driver_id' in result:
                selected_driver = next(
                    (d for d in drivers if d.id == result['selected_driver_id']), 
                    None
                )
                if selected_driver:
                    logging.info(f"AI selected driver {selected_driver.id} with reasoning: {result.get('reasoning', 'No reasoning provided')}")
                    return selected_driver
            
            # Fallback to basic selection if AI fails
            return self._basic_driver_selection(ride_request, drivers)
            
        except Exception as e:
            logging.error(f"AI driver selection failed: {e}")
            return self._basic_driver_selection(ride_request, drivers)
    
    def _create_matching_prompt(self, ride_request: Dict, driver_data: List[Dict]) -> str:
        """
        Create a detailed prompt for Gemini AI to analyze driver matching
        """
        prompt = f"""
You are an AI system for a ride-sharing platform. Analyze the following ride request and available drivers to select the optimal match.

RIDE REQUEST:
- Pickup Location: ({ride_request['pickup_lat']}, {ride_request['pickup_lng']})
- Dropoff Location: ({ride_request['dropoff_lat']}, {ride_request['dropoff_lng']})
- Pickup Address: {ride_request['pickup_address']}
- Dropoff Address: {ride_request['dropoff_address']}
- Estimated Distance: {ride_request.get('distance_km', 'Unknown')} km
- Request Time: {datetime.now().strftime('%H:%M on %A')}
- Special Notes: {ride_request.get('notes', 'None')}

AVAILABLE DRIVERS:
{json.dumps(driver_data, indent=2)}

SELECTION CRITERIA (in order of importance):
1. Driver availability and location freshness
2. Distance to pickup location (minimize rider wait time)
3. Driver rating and reliability
4. Recent activity and acceptance rate
5. Vehicle suitability for the trip
6. Overall driver performance metrics

Please analyze each driver and provide your recommendation in the following JSON format:
{{
    "selected_driver_id": "driver_id_here",
    "confidence_score": 0.85,
    "reasoning": "Detailed explanation of why this driver was selected",
    "alternative_driver_id": "backup_option_if_available",
    "key_factors": ["factor1", "factor2", "factor3"]
}}

Consider factors like:
- Proximity to reduce pickup time
- Driver reliability and rating
- Recent activity patterns
- Vehicle condition and type appropriateness
- Acceptance rate and completion history
- Location data freshness (prefer drivers with recent location updates)

Respond only with the JSON object, no additional text.
"""
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Optional[Dict]:
        """
        Parse the AI response to extract driver selection
        """
        try:
            # Extract JSON from response
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse AI response: {e}")
            return None
    
    def _basic_driver_selection(self, ride_request: Dict, drivers: List[User]) -> Optional[User]:
        """
        Fallback basic driver selection algorithm
        """
        if not drivers:
            return None
        
        # Score drivers based on multiple factors
        scored_drivers = []
        
        for driver in drivers:
            distance = LocationService._calculate_haversine_distance(
                driver.current_lat, driver.current_lng,
                ride_request['pickup_lat'], ride_request['pickup_lng']
            )
            
            # Calculate composite score
            distance_score = max(0, 10 - distance)  # Closer is better
            rating_score = driver.rating  # 1-5 scale
            experience_score = min(5, driver.total_rides / 20)  # Up to 5 points for experience
            freshness_score = self._get_location_freshness_score(driver)
            
            total_score = (distance_score * 0.4 + 
                          rating_score * 0.3 + 
                          experience_score * 0.2 + 
                          freshness_score * 0.1)
            
            scored_drivers.append((driver, total_score, distance))
        
        # Sort by score (highest first)
        scored_drivers.sort(key=lambda x: x[1], reverse=True)
        
        # Return the highest scoring available driver
        for driver, score, distance in scored_drivers:
            if driver.is_available:
                logging.info(f"Basic algorithm selected driver {driver.id} with score {score:.2f}")
                return driver
        
        return None
    
    def _get_location_freshness(self, driver: User) -> int:
        """
        Get how many minutes ago the driver's location was updated
        """
        if not driver.location_updated_at:
            return 999  # Very stale
        
        delta = datetime.now() - driver.location_updated_at
        return int(delta.total_seconds() / 60)
    
    def _get_location_freshness_score(self, driver: User) -> float:
        """
        Score location freshness (0-5 scale)
        """
        minutes_ago = self._get_location_freshness(driver)
        if minutes_ago <= 2:
            return 5.0
        elif minutes_ago <= 5:
            return 4.0
        elif minutes_ago <= 10:
            return 3.0
        elif minutes_ago <= 30:
            return 2.0
        elif minutes_ago <= 60:
            return 1.0
        else:
            return 0.0
    
    def _calculate_acceptance_rate(self, driver: User) -> float:
        """
        Calculate driver's acceptance rate for recent ride requests
        """
        # This would require tracking ride request offers vs acceptances
        # For now, use a mock calculation based on rating and total rides
        base_rate = min(0.95, driver.rating / 5.0 * 0.9)
        experience_bonus = min(0.1, driver.total_rides / 100 * 0.1)
        return round(base_rate + experience_bonus, 2)
    
    def analyze_matching_performance(self, time_period_days: int = 30) -> Dict:
        """
        Analyze the performance of the AI matching system
        """
        try:
            # Get recent completed rides
            recent_rides = db.session.query(Ride).filter(
                Ride.completed_at >= datetime.now() - timedelta(days=time_period_days),
                Ride.status == 'completed'
            ).all()
            
            if not recent_rides:
                return {"error": "No completed rides in the specified period"}
            
            # Calculate metrics
            total_rides = len(recent_rides)
            avg_pickup_time = sum(
                (ride.accepted_at - ride.requested_at).total_seconds() / 60 
                for ride in recent_rides if ride.accepted_at
            ) / total_rides
            
            avg_rating = sum(ride.driver.rating for ride in recent_rides) / total_rides
            
            # Use AI to analyze patterns if available
            if self.model:
                return self._ai_performance_analysis(recent_rides, avg_pickup_time, avg_rating)
            else:
                return {
                    "total_rides": total_rides,
                    "average_pickup_time_minutes": round(avg_pickup_time, 2),
                    "average_driver_rating": round(avg_rating, 2),
                    "analysis_method": "basic"
                }
                
        except Exception as e:
            logging.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}
    
    def _ai_performance_analysis(self, rides: List[Ride], avg_pickup_time: float, avg_rating: float) -> Dict:
        """
        Use AI to analyze matching performance and provide insights
        """
        try:
            # Prepare data for AI analysis
            ride_data = []
            for ride in rides[:50]:  # Limit to recent 50 rides for analysis
                pickup_time = (ride.accepted_at - ride.requested_at).total_seconds() / 60 if ride.accepted_at else None
                ride_data.append({
                    'pickup_time_minutes': pickup_time,
                    'driver_rating': ride.driver.rating,
                    'distance_km': ride.distance_km,
                    'price': ride.price,
                    'day_of_week': ride.requested_at.strftime('%A'),
                    'hour_of_day': ride.requested_at.hour
                })
            
            prompt = f"""
Analyze the following ride-sharing matching performance data and provide insights:

SUMMARY METRICS:
- Total rides analyzed: {len(rides)}
- Average pickup time: {avg_pickup_time:.2f} minutes
- Average driver rating: {avg_rating:.2f}

DETAILED RIDE DATA:
{json.dumps(ride_data, indent=2, default=str)}

Please provide analysis in JSON format:
{{
    "overall_performance": "excellent/good/fair/poor",
    "key_insights": ["insight1", "insight2", "insight3"],
    "pickup_time_analysis": "analysis of pickup times",
    "driver_quality_analysis": "analysis of driver ratings",
    "recommendations": ["recommendation1", "recommendation2"],
    "performance_score": 0.85,
    "areas_for_improvement": ["area1", "area2"]
}}

Focus on:
1. Pickup time efficiency
2. Driver quality consistency
3. Peak hour performance
4. Day-of-week patterns
5. Distance vs time correlations
6. Specific actionable recommendations

Respond only with the JSON object.
"""
            
            response = self.model.generate_content(prompt)
            result = self._parse_ai_response(response.text)
            
            if result:
                result.update({
                    "total_rides": len(rides),
                    "average_pickup_time_minutes": round(avg_pickup_time, 2),
                    "average_driver_rating": round(avg_rating, 2),
                    "analysis_method": "ai_powered"
                })
                return result
            else:
                return {"error": "Failed to parse AI analysis"}
                
        except Exception as e:
            logging.error(f"AI performance analysis failed: {e}")
            return {"error": str(e)}