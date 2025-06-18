# Palm Payment System

## Overview

This is a Flask-based web application that implements a biometric payment system using palm recognition technology. Users can register accounts, authenticate using palm prints, manage digital wallets, and make secure payments. The system combines traditional password authentication with advanced biometric features for enhanced security.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with support for PostgreSQL (production) and SQLite (development)
- **Authentication**: Hybrid system supporting both traditional password-based and biometric palm authentication
- **Image Processing**: OpenCV for palm image preprocessing and feature extraction
- **Deployment**: Gunicorn WSGI server with autoscaling support

### Frontend Architecture
- **Templates**: Jinja2 templating engine
- **Styling**: Bootstrap 5 with dark theme support
- **JavaScript**: Vanilla JavaScript for camera interactions and palm scanning
- **Icons**: Font Awesome for UI icons

### Database Schema
- **Users Table**: Stores user credentials, wallet balance, and palm biometric data
- **Transactions Table**: Records all wallet transactions (deposits, payments, withdrawals)
- **Palm Scan Logs**: Tracks authentication attempts and biometric scanning events

## Key Components

### 1. User Management (`models.py`)
- User registration and authentication
- Password hashing with Werkzeug security
- Wallet balance management
- Palm biometric data storage

### 2. Palm Recognition System (`palm_recognition.py`)
- ORB (Oriented FAST and Rotated BRIEF) feature detection
- Image preprocessing with noise reduction and contrast enhancement
- Feature matching for biometric authentication
- Support for image resizing and standardization

### 3. Wallet Service (`wallet.py`)
- Fund management (deposits and withdrawals)
- Transaction logging and history
- Balance validation and security checks
- Payment processing between users

### 4. Web Routes (`routes.py`)
- User registration and login endpoints
- Dashboard and wallet management
- Payment processing and transaction history
- File upload handling for palm images

### 5. Camera Integration (`static/js/camera.js`)
- WebRTC camera access
- Real-time palm image capture
- Canvas-based image processing
- Error handling for camera permissions

## Data Flow

### Registration Flow
1. User provides username, email, and password
2. System creates account with encrypted password
3. Optional palm registration for biometric authentication
4. User gets default wallet with zero balance

### Authentication Flow
1. Traditional login: Username/password verification
2. Biometric login: Palm image capture and feature matching
3. Session creation upon successful authentication
4. Redirect to dashboard with user context

### Payment Flow
1. Sender initiates payment with recipient and amount
2. System validates sender's wallet balance
3. Funds deducted from sender and added to recipient
4. Transaction recorded with timestamps and descriptions
5. Both parties receive transaction confirmation

## External Dependencies

### Python Packages
- `flask`: Web framework
- `flask-sqlalchemy`: Database ORM
- `opencv-python`: Image processing and computer vision
- `numpy`: Numerical computations for image data
- `psycopg2-binary`: PostgreSQL database adapter
- `gunicorn`: Production WSGI server
- `werkzeug`: Security utilities and request handling

### Frontend Libraries
- Bootstrap 5: UI framework with dark theme
- Font Awesome: Icon library
- WebRTC: Camera access for biometric scanning

## Deployment Strategy

### Development Environment
- SQLite database for local development
- Flask development server with hot reload
- Debug mode enabled for error tracking

### Production Environment
- PostgreSQL database with connection pooling
- Gunicorn WSGI server with autoscaling
- Environment-based configuration management
- Proxy fix middleware for reverse proxy support

### Configuration Management
- Environment variables for sensitive data (database URLs, session secrets)
- Configurable upload directories for palm images
- File size limits for uploaded biometric data

## Changelog
- June 18, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.