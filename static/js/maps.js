// Mock Google Maps functionality for the MVP
// In production, replace with actual Google Maps API

class MockMaps {
    static mockLocations = [
        { name: "Downtown Plaza", lat: 40.7128, lng: -74.0060 },
        { name: "Central Park", lat: 40.7829, lng: -73.9654 },
        { name: "Brooklyn Bridge", lat: 40.7061, lng: -73.9969 },
        { name: "Times Square", lat: 40.7580, lng: -73.9855 },
        { name: "Wall Street", lat: 40.7074, lng: -74.0113 },
        { name: "Statue of Liberty", lat: 40.6892, lng: -74.0445 },
        { name: "Empire State Building", lat: 40.7484, lng: -73.9857 },
        { name: "One World Trade Center", lat: 40.7127, lng: -74.0134 }
    ];

    static calculateDistance(pickup, dropoff) {
        // Simple distance calculation using Haversine formula
        const R = 6371; // Earth's radius in km
        const dLat = this.deg2rad(dropoff.lat - pickup.lat);
        const dLng = this.deg2rad(dropoff.lng - pickup.lng);
        
        const a = 
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(this.deg2rad(pickup.lat)) * Math.cos(this.deg2rad(dropoff.lat)) * 
            Math.sin(dLng/2) * Math.sin(dLng/2);
        
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        const distance = R * c;
        
        return Math.round(distance * 100) / 100; // Round to 2 decimal places
    }

    static deg2rad(deg) {
        return deg * (Math.PI/180);
    }

    static estimateDuration(distanceKm) {
        // Estimate duration based on average city speed (25 km/h)
        const averageSpeed = 25;
        const durationHours = distanceKm / averageSpeed;
        const durationMinutes = Math.round(durationHours * 60);
        return Math.max(5, durationMinutes); // Minimum 5 minutes
    }

    static geocodeAddress(address) {
        // Mock geocoding - return random location from mock locations
        const mockLocation = this.mockLocations[Math.floor(Math.random() * this.mockLocations.length)];
        
        // Add some randomness to coordinates
        const randomLat = mockLocation.lat + (Math.random() - 0.5) * 0.01;
        const randomLng = mockLocation.lng + (Math.random() - 0.5) * 0.01;
        
        return {
            lat: randomLat,
            lng: randomLng,
            address: address
        };
    }

    static initializeMap(containerId) {
        // Mock map initialization
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="mock-map">
                    <div class="text-center py-5">
                        <i class="bi bi-map display-4 text-primary"></i>
                        <h5 class="mt-3">Mock Map View</h5>
                        <p class="text-muted">Interactive map would appear here in production</p>
                    </div>
                </div>
            `;
            container.style.height = '300px';
            container.style.backgroundColor = '#f8f9fa';
            container.style.border = '1px solid #dee2e6';
            container.style.borderRadius = '0.375rem';
        }
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MockMaps;
}
