from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    palm_image_path = db.Column(db.String(255))
    palm_features = db.Column(db.Text)  # Store ORB features as JSON string
    payment_pin_hash = db.Column(db.String(256))  # 6-digit PIN for backup authentication
    wallet_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_palm_registered = db.Column(db.Boolean, default=False)
    is_pin_set = db.Column(db.Boolean, default=False)
    
    # Relationships
    transactions_sent = db.relationship('Transaction', foreign_keys='Transaction.sender_id', backref='sender', lazy='dynamic')
    transactions_received = db.relationship('Transaction', foreign_keys='Transaction.receiver_id', backref='receiver', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def set_payment_pin(self, pin):
        """Set 6-digit payment PIN"""
        if len(pin) == 6 and pin.isdigit():
            self.payment_pin_hash = generate_password_hash(pin)
            self.is_pin_set = True
            return True
        return False
    
    def check_payment_pin(self, pin):
        """Verify 6-digit payment PIN"""
        if not self.payment_pin_hash:
            return False
        return check_password_hash(self.payment_pin_hash, pin)
    
    def add_funds(self, amount):
        self.wallet_balance += amount
        db.session.commit()
    
    def deduct_funds(self, amount):
        if self.wallet_balance >= amount:
            self.wallet_balance -= amount
            db.session.commit()
            return True
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # None for deposits
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'deposit', 'payment', 'withdrawal'
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='completed')  # 'pending', 'completed', 'failed'
    
    def __repr__(self):
        return f'<Transaction {self.id}: {self.transaction_type} - ${self.amount}>'

class PalmScanLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    scan_result = db.Column(db.String(20), nullable=False)  # 'success', 'failed', 'no_match'
    confidence_score = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    
    def __repr__(self):
        return f'<PalmScanLog {self.id}: {self.scan_result}>'
