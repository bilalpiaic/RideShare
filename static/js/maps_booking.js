// Google Maps integration for ride booking with live location and nearby drivers
let map;
let directionsService;
let directionsRenderer;
let pickupMarker;
let dropoffMarker;
let currentLocationMarker;
let driverMarkers = [];
let autocompletePickup;
let autocompleteDropoff;
let pickupCoords = null;
let dropoffCoords = null;
let currentLocation = null;

// Initialize map when Google Maps API loads
function initMap() {
    // Default location (New York City)
    const defaultLocation = { lat: 40.7128, lng: -74.0060 };
    
    // Initialize map
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 13,
        center: defaultLocation,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        styles: [
            {
                featureType: 'poi',
                elementType: 'labels',
                stylers: [{ visibility: 'off' }]
            }
        ]
    });
    
    // Initialize directions service and renderer
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
        draggable: false,
        suppressMarkers: true
    });
    directionsRenderer.setMap(map);
    
    // Get user's current location
    getCurrentLocation();
    
    // Setup autocomplete
    setupAutocomplete();
    
    // Setup event listeners
    setupEventListeners();
}

function getCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                currentLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                // Center map on user location
                map.setCenter(currentLocation);
                
                // Add current location marker
                currentLocationMarker = new google.maps.Marker({
                    position: currentLocation,
                    map: map,
                    title: 'Your Location',
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 8,
                        fillColor: '#4285F4',
                        fillOpacity: 1,
                        strokeColor: '#ffffff',
                        strokeWeight: 2
                    }
                });
                
                // Load nearby drivers
                loadNearbyDrivers(currentLocation);
                
                // Reverse geocode to get address
                reverseGeocode(currentLocation, (address) => {
                    if (address) {
                        document.getElementById('pickup_address').value = address;
                        pickupCoords = currentLocation;
                    }
                });
            },
            (error) => {
                console.warn('Geolocation error:', error);
                // Fallback to IP-based location or default
            }
        );
    }
}

function setupAutocomplete() {
    const pickupInput = document.getElementById('pickup_address');
    const dropoffInput = document.getElementById('dropoff_address');
    
    // Setup custom autocomplete with Places API
    setupCustomAutocomplete(pickupInput, 'pickup');
    setupCustomAutocomplete(dropoffInput, 'dropoff');
}

function setupCustomAutocomplete(input, type) {
    let timeout;
    
    input.addEventListener('input', function() {
        clearTimeout(timeout);
        const query = this.value.trim();
        
        if (query.length < 3) {
            hideAutocompleteDropdown(type);
            return;
        }
        
        timeout = setTimeout(() => {
            fetchAutocompleteSuggestions(query, type);
        }, 300);
    });
    
    input.addEventListener('blur', function() {
        // Hide dropdown after a short delay to allow clicking on suggestions
        setTimeout(() => hideAutocompleteDropdown(type), 200);
    });
}

function fetchAutocompleteSuggestions(query, type) {
    const data = {
        input: query,
        location: currentLocation
    };
    
    fetch('/api/autocomplete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        showAutocompleteSuggestions(data.predictions || [], type);
    })
    .catch(error => {
        console.error('Autocomplete error:', error);
    });
}

function showAutocompleteSuggestions(suggestions, type) {
    const dropdownId = type + 'Dropdown';
    const dropdown = document.getElementById(dropdownId);
    
    dropdown.innerHTML = '';
    
    if (suggestions.length === 0) {
        hideAutocompleteDropdown(type);
        return;
    }
    
    suggestions.forEach(suggestion => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `
            <div class="fw-bold">${suggestion.main_text}</div>
            <div class="text-muted small">${suggestion.secondary_text}</div>
        `;
        
        item.addEventListener('click', () => {
            selectPlace(suggestion, type);
        });
        
        dropdown.appendChild(item);
    });
    
    dropdown.style.display = 'block';
}

function hideAutocompleteDropdown(type) {
    const dropdownId = type + 'Dropdown';
    const dropdown = document.getElementById(dropdownId);
    dropdown.style.display = 'none';
}

function selectPlace(suggestion, type) {
    const inputId = type + '_address';
    const input = document.getElementById(inputId);
    
    input.value = suggestion.description;
    hideAutocompleteDropdown(type);
    
    // Get place details
    fetch('/api/place_details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ place_id: suggestion.place_id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.lat && data.lng) {
            const coords = { lat: data.lat, lng: data.lng };
            
            if (type === 'pickup') {
                pickupCoords = coords;
                updatePickupMarker(coords);
            } else {
                dropoffCoords = coords;
                updateDropoffMarker(coords);
            }
            
            // Update route if both locations are set
            if (pickupCoords && dropoffCoords) {
                updateRoute();
            }
        }
    })
    .catch(error => {
        console.error('Place details error:', error);
    });
}

function updatePickupMarker(coords) {
    if (pickupMarker) {
        pickupMarker.setMap(null);
    }
    
    pickupMarker = new google.maps.Marker({
        position: coords,
        map: map,
        title: 'Pickup Location',
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 10,
            fillColor: '#28a745',
            fillOpacity: 1,
            strokeColor: '#ffffff',
            strokeWeight: 2
        }
    });
    
    // Adjust map bounds to include pickup
    const bounds = new google.maps.LatLngBounds();
    bounds.extend(coords);
    if (dropoffCoords) bounds.extend(dropoffCoords);
    map.fitBounds(bounds);
}

function updateDropoffMarker(coords) {
    if (dropoffMarker) {
        dropoffMarker.setMap(null);
    }
    
    dropoffMarker = new google.maps.Marker({
        position: coords,
        map: map,
        title: 'Destination',
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 10,
            fillColor: '#dc3545',
            fillOpacity: 1,
            strokeColor: '#ffffff',
            strokeWeight: 2
        }
    });
    
    // Adjust map bounds to include dropoff
    const bounds = new google.maps.LatLngBounds();
    if (pickupCoords) bounds.extend(pickupCoords);
    bounds.extend(coords);
    map.fitBounds(bounds);
}

function updateRoute() {
    if (!pickupCoords || !dropoffCoords) return;
    
    const request = {
        origin: pickupCoords,
        destination: dropoffCoords,
        travelMode: google.maps.TravelMode.DRIVING,
    };
    
    directionsService.route(request, (result, status) => {
        if (status === 'OK') {
            directionsRenderer.setDirections(result);
            
            // Get distance and duration for price estimate
            const route = result.routes[0];
            const leg = route.legs[0];
            const distance = leg.distance.value / 1000; // Convert to km
            const duration = leg.duration.value / 60; // Convert to minutes
            
            // Auto-calculate price estimate
            calculatePriceEstimate(pickupCoords, dropoffCoords);
        }
    });
}

function loadNearbyDrivers(location) {
    fetch('/api/nearby_drivers', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            lat: location.lat,
            lng: location.lng,
            radius_km: 10
        })
    })
    .then(response => response.json())
    .then(data => {
        displayNearbyDrivers(data.drivers || []);
        showDriverMarkers(data.drivers || []);
    })
    .catch(error => {
        console.error('Error loading nearby drivers:', error);
    });
}

function displayNearbyDrivers(drivers) {
    const driversList = document.getElementById('nearbyDriversList');
    const driversSection = document.getElementById('nearbyDriversSection');
    
    if (drivers.length === 0) {
        driversSection.style.display = 'none';
        return;
    }
    
    driversList.innerHTML = '';
    
    drivers.forEach(driver => {
        const driverCard = document.createElement('div');
        driverCard.className = 'driver-card mb-2 p-3 border rounded';
        driverCard.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="fw-bold">${driver.name || 'Driver'}</div>
                    <div class="text-muted small">
                        <i class="bi bi-star-fill text-warning"></i> ${driver.rating.toFixed(1)} 
                        • ${driver.distance_km} km away
                        • ${driver.total_rides} rides
                    </div>
                </div>
                <div class="driver-marker">
                    <i class="bi bi-car-front-fill"></i>
                </div>
            </div>
        `;
        
        driversList.appendChild(driverCard);
    });
    
    driversSection.style.display = 'block';
}

function showDriverMarkers(drivers) {
    // Clear existing driver markers
    driverMarkers.forEach(marker => marker.setMap(null));
    driverMarkers = [];
    
    // Add new driver markers
    drivers.forEach(driver => {
        const marker = new google.maps.Marker({
            position: { lat: driver.lat, lng: driver.lng },
            map: map,
            title: `${driver.name} (${driver.rating.toFixed(1)}★)`,
            icon: {
                path: "M29.395,0H17.636c-3.117,0-5.643,3.467-5.643,6.584v34.804c0,3.116,2.526,5.644,5.643,5.644h11.759   c3.116,0,5.644-2.527,5.644-5.644V6.584C35.037,3.467,32.511,0,29.395,0z M34.05,14.188v11.665l-2.729,0.351v-4.806L34.05,14.188z   M32.618,10.773c-1.016,3.9-2.219,8.51-2.219,8.51H16.631l-2.222-8.51C14.41,10.773,23.293,7.755,32.618,10.773z M15.741,21.713   v4.492l-2.73-0.349V14.502L15.741,21.713z M13.011,37.938V27.579l2.73,0.343v8.196L13.011,37.938z M14.568,40.882l2.218-3.336   h13.771l2.219,3.336H14.568z M31.321,35.805v-7.872l2.729-0.355v10.048L31.321,35.805z",
                fillColor: '#28a745',
                fillOpacity: 1,
                strokeColor: '#ffffff',
                strokeWeight: 1,
                scale: 0.5
            }
        });
        
        driverMarkers.push(marker);
    });
}

function calculatePriceEstimate(pickup, dropoff) {
    fetch('/api/price_estimate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            pickup_coords: pickup,
            dropoff_coords: dropoff
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Price estimate error:', data.error);
            return;
        }
        
        // Update price estimate display
        document.getElementById('baseFare').textContent = '$' + data.base_fare.toFixed(2);
        document.getElementById('distanceCost').textContent = '$' + data.distance_cost.toFixed(2);
        document.getElementById('timeCost').textContent = '$' + data.time_cost.toFixed(2);
        document.getElementById('totalPrice').textContent = '$' + data.total_price.toFixed(2);
        
        // Show the price estimate
        document.getElementById('priceEstimate').style.display = 'block';
    })
    .catch(error => {
        console.error('Price estimate error:', error);
    });
}

function reverseGeocode(coords, callback) {
    const geocoder = new google.maps.Geocoder();
    
    geocoder.geocode({ location: coords }, (results, status) => {
        if (status === 'OK' && results[0]) {
            callback(results[0].formatted_address);
        } else {
            callback(null);
        }
    });
}

function setupEventListeners() {
    // Current location button
    const currentLocationBtn = document.getElementById('currentLocationBtn');
    if (currentLocationBtn) {
        currentLocationBtn.addEventListener('click', () => {
            if (currentLocation) {
                document.getElementById('pickup_address').value = '';
                reverseGeocode(currentLocation, (address) => {
                    if (address) {
                        document.getElementById('pickup_address').value = address;
                        pickupCoords = currentLocation;
                        updatePickupMarker(currentLocation);
                        
                        if (dropoffCoords) {
                            updateRoute();
                        }
                    }
                });
            } else {
                getCurrentLocation();
            }
        });
    }
    
    // Get estimate button
    const getEstimateBtn = document.getElementById('getEstimate');
    if (getEstimateBtn) {
        getEstimateBtn.addEventListener('click', () => {
            if (pickupCoords && dropoffCoords) {
                calculatePriceEstimate(pickupCoords, dropoffCoords);
            } else {
                alert('Please select both pickup and destination locations.');
            }
        });
    }
    
    // Form submission
    const bookRideForm = document.getElementById('bookRideForm');
    if (bookRideForm) {
        bookRideForm.addEventListener('submit', (e) => {
            const pickup = document.getElementById('pickup_address').value.trim();
            const dropoff = document.getElementById('dropoff_address').value.trim();
            
            if (!pickup || !dropoff) {
                e.preventDefault();
                alert('Please fill in both pickup and destination addresses.');
                return;
            }
            
            if (pickup === dropoff) {
                e.preventDefault();
                alert('Pickup and destination cannot be the same.');
                return;
            }
            
            // Show loading state
            const submitBtn = bookRideForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Booking Ride...';
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Map will be initialized by Google Maps callback
    console.log('Maps booking script loaded');
});