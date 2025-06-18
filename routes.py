import os
import json
import logging
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Transaction, PalmScanLog
from palm_recognition import PalmRecognition
from wallet import WalletService
import cv2
import numpy as np

palm_recognizer = PalmRecognition()
wallet_service = WalletService()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    recent_transactions = Transaction.query.filter(
        (Transaction.sender_id == user.id) | (Transaction.receiver_id == user.id)
    ).order_by(Transaction.timestamp.desc()).limit(5).all()
    
    return render_template('dashboard.html', user=user, transactions=recent_transactions)

@app.route('/register_palm', methods=['GET', 'POST'])
def register_palm():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'palm_image' not in request.files:
            flash('No image uploaded', 'danger')
            return redirect(request.url)
        
        file = request.files['palm_image']
        if file.filename == '':
            flash('No image selected', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            user = User.query.get(session['user_id'])
            filename = secure_filename(f"palm_{user.id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process palm image and extract features
            features = palm_recognizer.extract_features(filepath)
            if features is not None:
                user.palm_image_path = filepath
                user.palm_features = json.dumps(features.tolist())
                user.is_palm_registered = True
                db.session.commit()
                
                flash('Palm print registered successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Failed to process palm image. Please try again.', 'danger')
                os.remove(filepath)  # Clean up failed upload
    
    return render_template('register.html')

@app.route('/palm_login', methods=['POST'])
def palm_login():
    if 'palm_image' not in request.files:
        return jsonify({'success': False, 'message': 'No image uploaded'})
    
    file = request.files['palm_image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid image file'})
    
    # Save temporary file
    temp_filename = secure_filename(f"temp_{file.filename}")
    temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
    file.save(temp_filepath)
    
    try:
        # Extract features from uploaded image
        uploaded_features = palm_recognizer.extract_features(temp_filepath)
        if uploaded_features is None:
            return jsonify({'success': False, 'message': 'Failed to process palm image'})
        
        # Find matching user
        users = User.query.filter_by(is_palm_registered=True).all()
        best_match = None
        best_score = 0
        
        for user in users:
            if user.palm_features:
                stored_features = np.array(json.loads(user.palm_features))
                similarity = palm_recognizer.compare_features(uploaded_features, stored_features)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = user
        
        # Log scan attempt with updated threshold
        threshold = 0.2
        scan_log = PalmScanLog(
            user_id=best_match.id if best_match else None,
            scan_result='success' if best_score > threshold else 'no_match',
            confidence_score=best_score,
            ip_address=request.remote_addr
        )
        db.session.add(scan_log)
        db.session.commit()
        
        # Use adaptive threshold based on best score
        threshold = 0.2  # Reduced from 0.3 to 0.2 for better usability
        
        if best_score > threshold:  # Threshold for successful match
            session['user_id'] = best_match.id
            session['username'] = best_match.username
            return jsonify({
                'success': True, 
                'message': f'Palm authentication successful! (Confidence: {best_score:.1%})',
                'redirect': url_for('dashboard')
            })
        else:
            # Provide more helpful feedback
            if best_score > 0.1:
                message = f'Palm partially recognized but confidence too low ({best_score:.1%}). Please try again with better lighting.'
            else:
                message = 'Palm not recognized. Make sure your palm is clearly visible and try again.'
            return jsonify({'success': False, 'message': message})
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        if amount <= 0:
            flash('Invalid amount', 'danger')
            return redirect(request.url)
        
        user = User.query.get(session['user_id'])
        user.add_funds(amount)
        
        # Create transaction record
        transaction = Transaction(
            receiver_id=user.id,
            amount=amount,
            transaction_type='deposit',
            description=f'Wallet deposit'
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Successfully deposited ${amount:.2f}', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('deposit.html')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        recipient_username = request.form['recipient']
        amount = float(request.form['amount'])
        description = request.form.get('description', '')
        
        if amount <= 0:
            flash('Invalid amount', 'danger')
            return redirect(request.url)
        
        sender = User.query.get(session['user_id'])
        recipient = User.query.filter_by(username=recipient_username).first()
        
        if not recipient:
            flash('Recipient not found', 'danger')
            return redirect(request.url)
        
        if sender.id == recipient.id:
            flash('Cannot send payment to yourself', 'danger')
            return redirect(request.url)
        
        if sender.wallet_balance < amount:
            flash('Insufficient funds', 'danger')
            return redirect(request.url)
        
        # Process payment
        if wallet_service.transfer_funds(sender, recipient, amount, description):
            flash(f'Payment of ${amount:.2f} sent to {recipient.username}', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Payment failed', 'danger')
    
    return render_template('payment.html')

@app.route('/palm_payment', methods=['POST'])
def palm_payment():
    if 'palm_image' not in request.files:
        return jsonify({'success': False, 'message': 'No palm image provided'})
    
    recipient_username = request.form.get('recipient')
    amount = float(request.form.get('amount', 0))
    description = request.form.get('description', '')
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Invalid amount'})
    
    file = request.files['palm_image']
    temp_filename = secure_filename(f"temp_payment_{file.filename}")
    temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
    file.save(temp_filepath)
    
    try:
        # Authenticate user via palm scan
        uploaded_features = palm_recognizer.extract_features(temp_filepath)
        if uploaded_features is None:
            return jsonify({'success': False, 'message': 'Failed to process palm image'})
        
        # Find authenticated user
        authenticated_user = None
        users = User.query.filter_by(is_palm_registered=True).all()
        
        for user in users:
            if user.palm_features:
                stored_features = np.array(json.loads(user.palm_features))
                similarity = palm_recognizer.compare_features(uploaded_features, stored_features)
                
                if similarity > 0.2:  # Authentication threshold (reduced for better usability)
                    authenticated_user = user
                    break
        
        if not authenticated_user:
            return jsonify({'success': False, 'message': 'Palm authentication failed'})
        
        # Find recipient
        recipient = User.query.filter_by(username=recipient_username).first()
        if not recipient:
            return jsonify({'success': False, 'message': 'Recipient not found'})
        
        # Process payment
        if wallet_service.transfer_funds(authenticated_user, recipient, amount, description):
            return jsonify({
                'success': True, 
                'message': f'Payment of ${amount:.2f} sent to {recipient.username}'
            })
        else:
            return jsonify({'success': False, 'message': 'Payment failed - insufficient funds'})
    
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

@app.route('/set_payment_pin', methods=['GET', 'POST'])
def set_payment_pin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        pin = request.form['pin']
        confirm_pin = request.form['confirm_pin']
        
        if pin != confirm_pin:
            flash('PINs do not match', 'danger')
            return render_template('set_pin.html')
        
        user = User.query.get(session['user_id'])
        if user.set_payment_pin(pin):
            db.session.commit()
            flash('Payment PIN set successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('PIN must be exactly 6 digits', 'danger')
    
    return render_template('set_pin.html')

@app.route('/pin_payment', methods=['POST'])
def pin_payment():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    recipient_username = request.form.get('recipient')
    amount = float(request.form.get('amount', 0))
    description = request.form.get('description', '')
    pin = request.form.get('pin')
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Invalid amount'})
    
    if not pin or len(pin) != 6:
        return jsonify({'success': False, 'message': 'Please enter a 6-digit PIN'})
    
    sender = User.query.get(session['user_id'])
    if not sender.is_pin_set:
        return jsonify({'success': False, 'message': 'Payment PIN not set. Please set your PIN first.'})
    
    if not sender.check_payment_pin(pin):
        return jsonify({'success': False, 'message': 'Incorrect PIN. Please try again.'})
    
    recipient = User.query.filter_by(username=recipient_username).first()
    if not recipient:
        return jsonify({'success': False, 'message': 'Recipient not found'})
    
    if sender.wallet_balance < amount:
        return jsonify({'success': False, 'message': 'Insufficient funds'})
    
    if wallet_service.transfer_funds(sender, recipient, amount, description):
        return jsonify({
            'success': True, 
            'message': f'Payment of ${amount:.2f} sent to {recipient.username}'
        })
    else:
        return jsonify({'success': False, 'message': 'Payment failed'})

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter(
        (Transaction.sender_id == user.id) | (Transaction.receiver_id == user.id)
    ).order_by(Transaction.timestamp.desc()).all()
    
    return render_template('history.html', transactions=transactions, current_user_id=user.id)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
