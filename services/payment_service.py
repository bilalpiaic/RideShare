from app import db
from models import Payment, Ride
from datetime import datetime
import uuid

class PaymentService:
    @staticmethod
    def process_payment(ride_id, amount, payment_method='mock'):
        """Process payment for a ride (mock implementation)"""
        ride = Ride.query.get(ride_id)
        if not ride:
            return {'success': False, 'error': 'Ride not found'}
        
        # Check if payment already exists
        existing_payment = Payment.query.filter_by(ride_id=ride_id).first()
        if existing_payment:
            return {'success': False, 'error': 'Payment already processed'}
        
        # Create payment record
        payment = Payment(
            ride_id=ride_id,
            rider_id=ride.rider_id,
            driver_id=ride.driver_id,
            amount=amount,
            payment_method=payment_method,
            transaction_id=f"mock_{uuid.uuid4().hex[:8]}",
            status='completed',
            processed_at=datetime.now()
        )
        
        db.session.add(payment)
        
        # Update ride status if not already completed
        if ride.status != 'completed':
            ride.status = 'completed'
            ride.completed_at = datetime.now()
        
        db.session.commit()
        
        return {
            'success': True,
            'transaction_id': payment.transaction_id,
            'amount': payment.amount,
            'status': payment.status
        }
    
    @staticmethod
    def get_payment_by_ride(ride_id):
        """Get payment details for a ride"""
        return Payment.query.filter_by(ride_id=ride_id).first()
    
    @staticmethod
    def refund_payment(payment_id, reason=None):
        """Process payment refund (mock implementation)"""
        payment = Payment.query.get(payment_id)
        if not payment:
            return {'success': False, 'error': 'Payment not found'}
        
        if payment.status == 'refunded':
            return {'success': False, 'error': 'Payment already refunded'}
        
        payment.status = 'refunded'
        db.session.commit()
        
        return {
            'success': True,
            'refund_id': f"refund_{uuid.uuid4().hex[:8]}",
            'amount': payment.amount
        }
