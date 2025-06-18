import logging
from datetime import datetime
from app import db
from models import User, Transaction

class WalletService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def add_funds(self, user: User, amount: float, description: str = "Wallet deposit") -> bool:
        """
        Add funds to user's wallet
        """
        try:
            if amount <= 0:
                self.logger.warning(f"Invalid deposit amount: {amount}")
                return False
            
            # Update user balance
            user.wallet_balance += amount
            
            # Create transaction record
            transaction = Transaction(
                receiver_id=user.id,
                amount=amount,
                transaction_type='deposit',
                description=description,
                status='completed'
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            self.logger.info(f"Added ${amount:.2f} to user {user.username}'s wallet")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding funds to wallet: {str(e)}")
            db.session.rollback()
            return False
    
    def deduct_funds(self, user: User, amount: float, description: str = "Payment") -> bool:
        """
        Deduct funds from user's wallet
        """
        try:
            if amount <= 0:
                self.logger.warning(f"Invalid deduction amount: {amount}")
                return False
            
            if user.wallet_balance < amount:
                self.logger.warning(f"Insufficient funds: user {user.username} has ${user.wallet_balance:.2f}, needs ${amount:.2f}")
                return False
            
            # Update user balance
            user.wallet_balance -= amount
            
            # Create transaction record
            transaction = Transaction(
                sender_id=user.id,
                receiver_id=user.id,  # Self-transaction for withdrawal
                amount=amount,
                transaction_type='withdrawal',
                description=description,
                status='completed'
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            self.logger.info(f"Deducted ${amount:.2f} from user {user.username}'s wallet")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deducting funds from wallet: {str(e)}")
            db.session.rollback()
            return False
    
    def transfer_funds(self, sender: User, receiver: User, amount: float, description: str = "Payment") -> bool:
        """
        Transfer funds between users
        """
        try:
            if amount <= 0:
                self.logger.warning(f"Invalid transfer amount: {amount}")
                return False
            
            if sender.wallet_balance < amount:
                self.logger.warning(f"Insufficient funds: sender {sender.username} has ${sender.wallet_balance:.2f}, needs ${amount:.2f}")
                return False
            
            if sender.id == receiver.id:
                self.logger.warning("Cannot transfer funds to self")
                return False
            
            # Update balances
            sender.wallet_balance -= amount
            receiver.wallet_balance += amount
            
            # Create transaction record
            transaction = Transaction(
                sender_id=sender.id,
                receiver_id=receiver.id,
                amount=amount,
                transaction_type='payment',
                description=description,
                status='completed'
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            self.logger.info(f"Transferred ${amount:.2f} from {sender.username} to {receiver.username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error transferring funds: {str(e)}")
            db.session.rollback()
            return False
    
    def get_balance(self, user: User) -> float:
        """
        Get user's current wallet balance
        """
        try:
            # Refresh user data from database
            db.session.refresh(user)
            return user.wallet_balance
        except Exception as e:
            self.logger.error(f"Error getting balance for user {user.username}: {str(e)}")
            return 0.0
    
    def get_transaction_history(self, user: User, limit: int = 50) -> list:
        """
        Get user's transaction history
        """
        try:
            transactions = Transaction.query.filter(
                (Transaction.sender_id == user.id) | (Transaction.receiver_id == user.id)
            ).order_by(Transaction.timestamp.desc()).limit(limit).all()
            
            return transactions
        except Exception as e:
            self.logger.error(f"Error getting transaction history for user {user.username}: {str(e)}")
            return []
    
    def validate_transaction(self, sender: User, receiver: User, amount: float) -> tuple:
        """
        Validate a transaction before processing
        Returns (is_valid, error_message)
        """
        try:
            # Check amount
            if amount <= 0:
                return False, "Invalid amount"
            
            # Check sender balance
            if sender.wallet_balance < amount:
                return False, "Insufficient funds"
            
            # Check if sender and receiver are different
            if sender.id == receiver.id:
                return False, "Cannot send payment to yourself"
            
            # Check if receiver exists and is active
            if not receiver:
                return False, "Recipient not found"
            
            return True, "Valid transaction"
            
        except Exception as e:
            self.logger.error(f"Error validating transaction: {str(e)}")
            return False, "Transaction validation error"
    
    def process_refund(self, transaction_id: int, reason: str = "Refund") -> bool:
        """
        Process a refund for a completed transaction
        """
        try:
            transaction = Transaction.query.get(transaction_id)
            if not transaction:
                self.logger.warning(f"Transaction {transaction_id} not found")
                return False
            
            if transaction.transaction_type != 'payment':
                self.logger.warning(f"Cannot refund non-payment transaction {transaction_id}")
                return False
            
            if transaction.status != 'completed':
                self.logger.warning(f"Cannot refund incomplete transaction {transaction_id}")
                return False
            
            sender = User.query.get(transaction.sender_id)
            receiver = User.query.get(transaction.receiver_id)
            
            if not sender or not receiver:
                self.logger.error(f"User not found for transaction {transaction_id}")
                return False
            
            # Reverse the transaction
            receiver.wallet_balance -= transaction.amount
            sender.wallet_balance += transaction.amount
            
            # Create refund transaction record
            refund_transaction = Transaction(
                sender_id=receiver.id,
                receiver_id=sender.id,
                amount=transaction.amount,
                transaction_type='refund',
                description=f"Refund for transaction #{transaction_id}: {reason}",
                status='completed'
            )
            
            db.session.add(refund_transaction)
            db.session.commit()
            
            self.logger.info(f"Processed refund for transaction {transaction_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing refund: {str(e)}")
            db.session.rollback()
            return False
