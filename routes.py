from flask import render_template, request, redirect, url_for, flash, jsonify, make_response, session
from flask_login import current_user
from app import app, db
from models import User, Ride, Payment
from replit_auth import require_login, make_replit_blueprint
from services.ride_service import RideService
from services.payment_service import PaymentService
from services.receipt_service import ReceiptService
from services.pricing_service import get_price_estimate
from services.location_service import LocationService
import json
import os
from datetime import datetime

# Register auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Landing page - redirect to appropriate dashboard if logged in"""
    if current_user.is_authenticated:
        if current_user.role == 'driver':
            return redirect(url_for('driver_dashboard'))
        else:
            return redirect(url_for('rider_dashboard'))
    return render_template('index.html')

@app.route('/setup_profile', methods=['GET', 'POST'])
@require_login
def setup_profile():
    """Setup user profile after first login"""
    if request.method == 'POST':
        role = request.form.get('role')
        phone = request.form.get('phone')
        
        current_user.role = role if role in ['rider', 'driver'] else 'rider'
        current_user.phone = phone
        
        if role == 'driver':
            vehicle_info = {
                'make': request.form.get('vehicle_make', ''),
                'model': request.form.get('vehicle_model', ''),
                'year': request.form.get('vehicle_year', ''),
                'license_plate': request.form.get('license_plate', ''),
                'color': request.form.get('vehicle_color', '')
            }
            current_user.vehicle_info = json.dumps(vehicle_info)
            current_user.is_available = True
        
        db.session.commit()
        flash('Profile setup complete!', 'success')
        
        if role == 'driver':
            return redirect(url_for('driver_dashboard'))
        else:
            return redirect(url_for('rider_dashboard'))
    
    return render_template('setup_profile.html')

@app.route('/rider_dashboard')
@require_login
def rider_dashboard():
    """Rider dashboard"""
    if not current_user.role:
        return redirect(url_for('setup_profile'))
    
    # Get recent rides
    recent_rides = RideService.get_user_rides(current_user.id, 'rider')[:5]
    
    return render_template('rider_dashboard.html', recent_rides=recent_rides)

@app.route('/driver_dashboard')
@require_login
def driver_dashboard():
    """Driver dashboard"""
    if current_user.role != 'driver':
        flash('Access denied. Driver account required.', 'error')
        return redirect(url_for('index'))
    
    # Get recent rides
    recent_rides = RideService.get_user_rides(current_user.id, 'driver')[:5]
    
    # Get pending rides (not assigned to any driver yet)
    pending_rides = Ride.query.filter_by(status='pending', driver_id=None).limit(10).all()
    
    return render_template('driver_dashboard.html', 
                         recent_rides=recent_rides, 
                         pending_rides=pending_rides,
                         is_available=current_user.is_available)

@app.route('/book_ride', methods=['GET', 'POST'])
@require_login
def book_ride():
    """Book a new ride"""
    if current_user.role != 'rider':
        flash('Only riders can book rides.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        pickup_address = request.form.get('pickup_address')
        dropoff_address = request.form.get('dropoff_address')
        notes = request.form.get('notes', '')
        
        if not pickup_address or not dropoff_address:
            flash('Please provide both pickup and dropoff addresses.', 'error')
            return render_template('book_ride.html', google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY'))
        
        # Create ride
        ride = RideService.create_ride(
            rider_id=current_user.id,
            pickup_address=pickup_address,
            dropoff_address=dropoff_address,
            notes=notes
        )
        
        flash(f'Ride booked successfully! Ride ID: {ride.id}', 'success')
        return redirect(url_for('ride_details', ride_id=ride.id))
    
    return render_template('book_ride.html', google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY'))

@app.route('/ride/<int:ride_id>')
@require_login
def ride_details(ride_id):
    """View ride details"""
    ride = Ride.query.get_or_404(ride_id)
    
    # Check if user has access to this ride
    if current_user.id not in [ride.rider_id, ride.driver_id]:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    payment = PaymentService.get_payment_by_ride(ride_id)
    
    return render_template('ride_details.html', ride=ride, payment=payment)

@app.route('/accept_ride/<int:ride_id>', methods=['POST'])
@require_login
def accept_ride(ride_id):
    """Driver accepts a ride"""
    if current_user.role != 'driver':
        flash('Only drivers can accept rides.', 'error')
        return redirect(url_for('index'))
    
    ride = Ride.query.get_or_404(ride_id)
    
    if ride.driver_id:
        flash('This ride has already been accepted.', 'error')
        return redirect(url_for('driver_dashboard'))
    
    # Assign driver
    ride.driver_id = current_user.id
    ride.status = 'accepted'
    current_user.is_available = False
    
    db.session.commit()
    
    flash('Ride accepted successfully!', 'success')
    return redirect(url_for('ride_details', ride_id=ride.id))

@app.route('/update_ride_status/<int:ride_id>', methods=['POST'])
@require_login
def update_ride_status(ride_id):
    """Update ride status"""
    ride = Ride.query.get_or_404(ride_id)
    
    # Check permissions
    if current_user.id not in [ride.rider_id, ride.driver_id]:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    new_status = request.form.get('status')
    
    if RideService.update_ride_status(ride_id, new_status, current_user.id):
        flash(f'Ride status updated to {new_status}.', 'success')
    else:
        flash('Failed to update ride status.', 'error')
    
    return redirect(url_for('ride_details', ride_id=ride.id))

@app.route('/pay_ride/<int:ride_id>', methods=['POST'])
@require_login
def pay_ride(ride_id):
    """Process payment for a ride"""
    ride = Ride.query.get_or_404(ride_id)
    
    # Check if user is the rider
    if current_user.id != ride.rider_id:
        flash('Only the rider can pay for this ride.', 'error')
        return redirect(url_for('index'))
    
    # Check if ride is completed
    if ride.status != 'completed':
        flash('Can only pay for completed rides.', 'error')
        return redirect(url_for('ride_details', ride_id=ride.id))
    
    # Process payment
    result = PaymentService.process_payment(ride_id, ride.price)
    
    if result['success']:
        flash('Payment processed successfully!', 'success')
    else:
        flash(f'Payment failed: {result["error"]}', 'error')
    
    return redirect(url_for('ride_details', ride_id=ride.id))

@app.route('/download_receipt/<int:ride_id>')
@require_login
def download_receipt(ride_id):
    """Download PDF receipt"""
    ride = Ride.query.get_or_404(ride_id)
    payment = PaymentService.get_payment_by_ride(ride_id)
    
    # Check permissions
    if current_user.id not in [ride.rider_id, ride.driver_id]:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    if not payment or payment.status != 'completed':
        flash('Receipt not available. Payment must be completed first.', 'error')
        return redirect(url_for('ride_details', ride_id=ride.id))
    
    # Generate PDF
    pdf_data = ReceiptService.generate_receipt_pdf(ride, payment)
    
    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=receipt_{ride.id}.pdf'
    
    return response

@app.route('/ride_history')
@require_login
def ride_history():
    """View ride history"""
    rides = RideService.get_user_rides(current_user.id, current_user.role)
    return render_template('ride_history.html', rides=rides)

@app.route('/toggle_availability', methods=['POST'])
@require_login
def toggle_availability():
    """Toggle driver availability"""
    if current_user.role != 'driver':
        flash('Only drivers can toggle availability.', 'error')
        return redirect(url_for('index'))
    
    current_user.is_available = not current_user.is_available
    db.session.commit()
    
    status = 'available' if current_user.is_available else 'unavailable'
    flash(f'You are now {status}.', 'success')
    
    return redirect(url_for('driver_dashboard'))

@app.route('/driver_location')
@require_login
def driver_location():
    """Driver location tracking page"""
    if current_user.role != 'driver':
        flash('Access denied. Driver account required.', 'error')
        return redirect(url_for('index'))
    
    return render_template('driver_location.html', google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY'))

@app.route('/api/price_estimate', methods=['POST'])
@require_login
def api_price_estimate():
    """API endpoint for price estimation using Google Maps"""
    data = request.get_json()
    
    pickup_coords = data.get('pickup_coords')
    dropoff_coords = data.get('dropoff_coords')
    
    if not pickup_coords or not dropoff_coords:
        return jsonify({'error': 'Both pickup and dropoff coordinates required'}), 400
    
    # Use Google Maps Distance Matrix API for real distance calculation
    distance_data = LocationService.calculate_distance_matrix(
        [pickup_coords], [dropoff_coords]
    )
    
    if distance_data and distance_data['status'] == 'OK':
        element = distance_data['rows'][0]['elements'][0]
        if element['status'] == 'OK':
            distance_km = element['distance']['value'] / 1000  # Convert meters to km
            duration_minutes = element['duration']['value'] / 60  # Convert seconds to minutes
        else:
            # Fallback to haversine distance if API fails
            distance_km = LocationService._calculate_haversine_distance(
                pickup_coords['lat'], pickup_coords['lng'],
                dropoff_coords['lat'], dropoff_coords['lng']
            )
            duration_minutes = max(15, int(distance_km * 2.5))
    else:
        # Fallback calculation
        distance_km = LocationService._calculate_haversine_distance(
            pickup_coords['lat'], pickup_coords['lng'],
            dropoff_coords['lat'], dropoff_coords['lng']
        )
        duration_minutes = max(15, int(distance_km * 2.5))
    
    estimate = get_price_estimate(distance_km, duration_minutes)
    
    return jsonify(estimate)

@app.route('/api/geocode', methods=['POST'])
@require_login
def api_geocode():
    """Geocode an address using Google Maps API"""
    data = request.get_json()
    address = data.get('address')
    
    if not address:
        return jsonify({'error': 'Address is required'}), 400
    
    result = LocationService.geocode_address(address)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Unable to geocode address'}), 400

@app.route('/api/autocomplete', methods=['POST'])
@require_login
def api_autocomplete():
    """Get place autocomplete suggestions"""
    data = request.get_json()
    input_text = data.get('input')
    location = data.get('location')  # Optional location bias
    
    if not input_text or len(input_text) < 3:
        return jsonify({'predictions': []})
    
    suggestions = LocationService.get_place_autocomplete(input_text, location)
    return jsonify({'predictions': suggestions})

@app.route('/api/place_details', methods=['POST'])
@require_login
def api_place_details():
    """Get place details from place_id"""
    data = request.get_json()
    place_id = data.get('place_id')
    
    if not place_id:
        return jsonify({'error': 'Place ID is required'}), 400
    
    result = LocationService.get_place_details(place_id)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Unable to get place details'}), 400

@app.route('/api/nearby_drivers', methods=['POST'])
@require_login
def api_nearby_drivers():
    """Get nearby available drivers"""
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    radius_km = data.get('radius_km', 10)
    
    if not lat or not lng:
        return jsonify({'error': 'Location coordinates required'}), 400
    
    drivers = LocationService.find_nearby_drivers(lat, lng, radius_km)
    return jsonify({'drivers': drivers})

@app.route('/api/update_location', methods=['POST'])
@require_login
def api_update_location():
    """Update driver's current location"""
    if current_user.role != 'driver':
        return jsonify({'error': 'Only drivers can update location'}), 403
    
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    
    if not lat or not lng:
        return jsonify({'error': 'Location coordinates required'}), 400
    
    success = LocationService.update_driver_location(current_user.id, lat, lng)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to update location'}), 400
