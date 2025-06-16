def calculate_ride_price(distance_km, duration_minutes):
    """
    Calculate ride price based on distance and time
    Pricing structure:
    - Base fare: $5.00
    - Per kilometer: $1.50
    - Per minute: $0.30
    """
    BASE_FARE = 5.00
    RATE_PER_KM = 1.50
    RATE_PER_MINUTE = 0.30
    
    distance_cost = distance_km * RATE_PER_KM
    time_cost = duration_minutes * RATE_PER_MINUTE
    
    total_price = BASE_FARE + distance_cost + time_cost
    
    # Round to 2 decimal places
    return round(total_price, 2)

def get_price_estimate(distance_km, duration_minutes):
    """Get price estimate with breakdown"""
    BASE_FARE = 5.00
    RATE_PER_KM = 1.50
    RATE_PER_MINUTE = 0.30
    
    distance_cost = distance_km * RATE_PER_KM
    time_cost = duration_minutes * RATE_PER_MINUTE
    total_price = BASE_FARE + distance_cost + time_cost
    
    return {
        'base_fare': BASE_FARE,
        'distance_cost': round(distance_cost, 2),
        'time_cost': round(time_cost, 2),
        'total_price': round(total_price, 2),
        'distance_km': distance_km,
        'duration_minutes': duration_minutes
    }
