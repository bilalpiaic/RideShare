document.addEventListener('DOMContentLoaded', function() {
    const getEstimateBtn = document.getElementById('getEstimate');
    const pickupInput = document.getElementById('pickup_address');
    const dropoffInput = document.getElementById('dropoff_address');
    const priceEstimateDiv = document.getElementById('priceEstimate');
    
    if (getEstimateBtn) {
        getEstimateBtn.addEventListener('click', function() {
            const pickup = pickupInput.value.trim();
            const dropoff = dropoffInput.value.trim();
            
            if (!pickup || !dropoff) {
                alert('Please enter both pickup and destination addresses.');
                return;
            }
            
            // Show loading state
            getEstimateBtn.disabled = true;
            getEstimateBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Calculating...';
            
            // Mock API call to get price estimate
            fetch('/api/price_estimate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    pickup_address: pickup,
                    dropoff_address: dropoff
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
                priceEstimateDiv.style.display = 'block';
                
                // Smooth scroll to price estimate
                priceEstimateDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            })
            .catch(error => {
                alert('Error calculating price. Please try again.');
                console.error('Error:', error);
            })
            .finally(() => {
                // Restore button state
                getEstimateBtn.disabled = false;
                getEstimateBtn.innerHTML = '<i class="bi bi-calculator me-2"></i>Get Price Estimate';
            });
        });
    }
    
    // Auto-suggest functionality (mock)
    function setupAutoSuggest(inputElement) {
        let timeout;
        
        inputElement.addEventListener('input', function() {
            clearTimeout(timeout);
            const query = this.value.trim();
            
            if (query.length < 3) return;
            
            timeout = setTimeout(() => {
                // Mock suggestions
                const suggestions = [
                    query + ' - Downtown',
                    query + ' - Airport',
                    query + ' - Mall',
                    query + ' - University',
                    query + ' - Hospital'
                ];
                
                // In a real app, you would show these suggestions in a dropdown
                console.log('Suggestions for "' + query + '":', suggestions);
            }, 300);
        });
    }
    
    // Setup auto-suggest for both inputs
    if (pickupInput) setupAutoSuggest(pickupInput);
    if (dropoffInput) setupAutoSuggest(dropoffInput);
    
    // Form validation
    const bookRideForm = document.getElementById('bookRideForm');
    if (bookRideForm) {
        bookRideForm.addEventListener('submit', function(e) {
            const pickup = pickupInput.value.trim();
            const dropoff = dropoffInput.value.trim();
            
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
            
            // Show loading state on submit button
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Booking Ride...';
            }
        });
    }
});
