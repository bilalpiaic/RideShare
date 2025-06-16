// Enhanced ride booking with live location using OpenStreetMap fallback
let map;
let pickupMarker;
let dropoffMarker;
let currentLocationMarker;
let driverMarkers = [];
let pickupCoords = null;
let dropoffCoords = null;
let currentLocation = null;

// Initialize map when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    setupEventListeners();
    getCurrentLocation();
});

function initializeMap() {
    // Create map using Leaflet (OpenStreetMap)
    const mapContainer = document.getElementById('map');
    
    if (!mapContainer) return;
    
    // Default location (New York City)
    const defaultLocation = [40.7128, -74.0060];
    
    // Initialize Leaflet map
    map = L.map('map').setView(defaultLocation, 13);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Add custom CSS for Leaflet
    if (!document.getElementById('leaflet-css')) {
        const link = document.createElement('link');
        link.id = 'leaflet-css';
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        document.head.appendChild(link);
    }
    
    // Load Leaflet library if not already loaded
    if (typeof L === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        script.onload = () => {
            initializeMap();
        };
        document.head.appendChild(script);
        return;
    }
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
                if (map) {
                    map.setView([currentLocation.lat, currentLocation.lng], 15);
                    
                    // Add current location marker
                    currentLocationMarker = L.marker([currentLocation.lat, currentLocation.lng])
                        .addTo(map)
                        .bindPopup('Your Current Location')
                        .openPopup();
                }
                
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
                // Load drivers for default location
                loadNearbyDrivers({ lat: 40.7128, lng: -74.0060 });
            }
        );
    }
}

function setupEventListeners() {
    // Current location button
    const currentLocationBtn = document.getElementById('currentLocationBtn');
    if (currentLocationBtn) {
        currentLocationBtn.addEventListener('click', () => {
            getCurrentLocation();
        });
    }
    
    // Address input autocomplete
    setupAddressAutocomplete();
    
    // Get estimate button
    const getEstimateBtn = document.getElementById('getEstimate');
    if (getEstimateBtn) {
        getEstimateBtn.addEventListener('click', calculatePriceEstimate);
    }
    
    // Form submission
    const bookRideForm = document.getElementById('bookRideForm');
    if (bookRideForm) {
        bookRideForm.addEventListener('submit', handleFormSubmission);
    }
}

function setupAddressAutocomplete() {
    const pickupInput = document.getElementById('pickup_address');
    const dropoffInput = document.getElementById('dropoff_address');
    
    if (pickupInput) {
        setupInputAutocomplete(pickupInput, 'pickup');
    }
    if (dropoffInput) {
        setupInputAutocomplete(dropoffInput, 'dropoff');
    }
}

function setupInputAutocomplete(input, type) {
    let timeout;
    
    input.addEventListener('input', function() {
        clearTimeout(timeout);
        const query = this.value.trim();
        
        if (query.length < 3) {
            hideAutocompleteDropdown(type);
            return;
        }
        
        timeout = setTimeout(() => {
            fetchLocationSuggestions(query, type);
        }, 500);
    });
    
    input.addEventListener('blur', function() {
        setTimeout(() => hideAutocompleteDropdown(type), 200);
    });
}

function fetchLocationSuggestions(query, type) {
    // Use Nominatim (OpenStreetMap) for geocoding
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&countrycodes=us`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const suggestions = data.map(item => ({
                display_name: item.display_name,
                lat: parseFloat(item.lat),
                lng: parseFloat(item.lon),
                main_text: item.display_name.split(',')[0],
                secondary_text: item.display_name.split(',').slice(1).join(',')
            }));
            showAutocompleteSuggestions(suggestions, type);
        })
        .catch(error => {
            console.error('Geocoding error:', error);
        });
}

function showAutocompleteSuggestions(suggestions, type) {
    const dropdownId = type + 'Dropdown';
    const dropdown = document.getElementById(dropdownId);
    
    if (!dropdown) return;
    
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
            selectLocation(suggestion, type);
        });
        
        dropdown.appendChild(item);
    });
    
    dropdown.style.display = 'block';
}

function hideAutocompleteDropdown(type) {
    const dropdownId = type + 'Dropdown';
    const dropdown = document.getElementById(dropdownId);
    if (dropdown) {
        dropdown.style.display = 'none';
    }
}

function selectLocation(location, type) {
    const inputId = type + '_address';
    const input = document.getElementById(inputId);
    
    input.value = location.display_name;
    hideAutocompleteDropdown(type);
    
    const coords = { lat: location.lat, lng: location.lng };
    
    if (type === 'pickup') {
        pickupCoords = coords;
        updatePickupMarker(coords);
    } else {
        dropoffCoords = coords;
        updateDropoffMarker(coords);
    }
    
    // Update route if both locations are set
    if (pickupCoords && dropoffCoords && map) {
        updateRoute();
        calculatePriceEstimate();
    }
}

function updatePickupMarker(coords) {
    if (pickupMarker && map) {
        map.removeLayer(pickupMarker);
    }
    
    if (map) {
        pickupMarker = L.marker([coords.lat, coords.lng], {
            icon: L.icon({
                iconUrl: 'data:image/svg+xml;base64,' + btoa(`
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 25 25">
                        <circle cx="12.5" cy="12.5" r="10" fill="#28a745" stroke="white" stroke-width="2"/>
                        <text x="12.5" y="17" text-anchor="middle" font-family="Arial" font-size="12" fill="white">P</text>
                    </svg>
                `),
                iconSize: [25, 25],
                iconAnchor: [12.5, 12.5]
            })
        }).addTo(map).bindPopup('Pickup Location');
        
        updateMapBounds();
    }
}

function updateDropoffMarker(coords) {
    if (dropoffMarker && map) {
        map.removeLayer(dropoffMarker);
    }
    
    if (map) {
        dropoffMarker = L.marker([coords.lat, coords.lng], {
            icon: L.icon({
                iconUrl: 'data:image/svg+xml;base64,' + btoa(`
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 25 25">
                        <circle cx="12.5" cy="12.5" r="10" fill="#dc3545" stroke="white" stroke-width="2"/>
                        <text x="12.5" y="17" text-anchor="middle" font-family="Arial" font-size="12" fill="white">D</text>
                    </svg>
                `),
                iconSize: [25, 25],
                iconAnchor: [12.5, 12.5]
            })
        }).addTo(map).bindPopup('Destination');
        
        updateMapBounds();
    }
}

function updateMapBounds() {
    if (!map) return;
    
    const bounds = [];
    if (pickupCoords) bounds.push([pickupCoords.lat, pickupCoords.lng]);
    if (dropoffCoords) bounds.push([dropoffCoords.lat, dropoffCoords.lng]);
    if (currentLocation) bounds.push([currentLocation.lat, currentLocation.lng]);
    
    if (bounds.length > 1) {
        map.fitBounds(bounds, { padding: [20, 20] });
    }
}

function updateRoute() {
    if (!pickupCoords || !dropoffCoords || !map) return;
    
    // Draw a simple line between pickup and dropoff
    const routeLine = L.polyline([
        [pickupCoords.lat, pickupCoords.lng],
        [dropoffCoords.lat, dropoffCoords.lng]
    ], {
        color: '#007bff',
        weight: 4,
        opacity: 0.7
    }).addTo(map);
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
    
    if (!driversList || !driversSection) return;
    
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
                    <i class="bi bi-car-front-fill text-success"></i>
                </div>
            </div>
        `;
        
        driversList.appendChild(driverCard);
    });
    
    driversSection.style.display = 'block';
}

function showDriverMarkers(drivers) {
    if (!map) return;
    
    // Clear existing driver markers
    driverMarkers.forEach(marker => {
        map.removeLayer(marker);
    });
    driverMarkers = [];
    
    // Add new driver markers
    drivers.forEach(driver => {
        const marker = L.marker([driver.lat, driver.lng], {
            icon: L.icon({
                iconUrl: 'data:image/svg+xml;base64,' + btoa(`
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 25 25">
                        <circle cx="12.5" cy="12.5" r="10" fill="#28a745" stroke="white" stroke-width="2"/>
                        <text x="12.5" y="17" text-anchor="middle" font-family="Arial" font-size="10" fill="white">🚗</text>
                    </svg>
                `),
                iconSize: [25, 25],
                iconAnchor: [12.5, 12.5]
            })
        }).addTo(map).bindPopup(`${driver.name}<br>Rating: ${driver.rating.toFixed(1)}★<br>${driver.distance_km} km away`);
        
        driverMarkers.push(marker);
    });
}

function calculatePriceEstimate() {
    if (!pickupCoords || !dropoffCoords) {
        alert('Please select both pickup and destination locations.');
        return;
    }
    
    const getEstimateBtn = document.getElementById('getEstimate');
    if (getEstimateBtn) {
        getEstimateBtn.disabled = true;
        getEstimateBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Calculating...';
    }
    
    fetch('/api/price_estimate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            pickup_coords: pickupCoords,
            dropoff_coords: dropoffCoords
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error calculating price: ' + data.error);
            return;
        }
        
        // Update price estimate display
        document.getElementById('baseFare').textContent = '$' + data.base_fare.toFixed(2);
        document.getElementById('distanceCost').textContent = '$' + data.distance_cost.toFixed(2);
        document.getElementById('timeCost').textContent = '$' + data.time_cost.toFixed(2);
        document.getElementById('totalPrice').textContent = '$' + data.total_price.toFixed(2);
        
        // Show the price estimate
        document.getElementById('priceEstimate').style.display = 'block';
        
        // Smooth scroll to price estimate
        document.getElementById('priceEstimate').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    })
    .catch(error => {
        alert('Error calculating price. Please try again.');
        console.error('Error:', error);
    })
    .finally(() => {
        // Restore button state
        if (getEstimateBtn) {
            getEstimateBtn.disabled = false;
            getEstimateBtn.innerHTML = '<i class="bi bi-calculator me-2"></i>Get Price Estimate';
        }
    });
}

function reverseGeocode(coords, callback) {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${coords.lat}&lon=${coords.lng}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data && data.display_name) {
                callback(data.display_name);
            } else {
                callback(null);
            }
        })
        .catch(error => {
            console.error('Reverse geocoding error:', error);
            callback(null);
        });
}

function handleFormSubmission(e) {
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
    const submitBtn = e.target.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Booking Ride...';
    }
}

// Load Leaflet library
if (typeof L === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    document.head.appendChild(script);
    
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(link);
}