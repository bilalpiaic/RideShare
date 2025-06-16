# RideShare Platform

## Overview

This is a production-ready MVP of a ride-sharing platform built with Flask, designed to connect riders with drivers for seamless transportation services. The application features user authentication, ride booking, driver matching, payment processing, and receipt generation.

## System Architecture

The application follows a monolithic Flask architecture with clear separation of concerns:

- **Web Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (configured for production deployment)
- **Authentication**: Replit Auth integration with OAuth support
- **Frontend**: Server-side rendered HTML templates with Bootstrap 5
- **Deployment**: Gunicorn WSGI server with auto-scaling configuration

## Key Components

### Authentication System
- **Replit Auth Integration**: Uses Flask-Dance for OAuth authentication
- **User Management**: Role-based access control (riders vs drivers)
- **Session Management**: Secure session handling with permanent sessions
- **Database Models**: User and OAuth tables with proper relationships

### User Management
- **Dual Roles**: Support for both riders and drivers
- **Profile Setup**: Initial profile configuration after first login
- **Vehicle Information**: Driver-specific vehicle details stored as JSON
- **Availability Status**: Real-time driver availability tracking
- **Location Tracking**: Live GPS tracking for drivers with real-time updates

### Ride Management
- **Ride Booking**: Complete ride request system with live location selection
- **Google Maps Integration**: Real-time location services with autocomplete
- **Driver Assignment**: Location-based driver matching with proximity search
- **Status Tracking**: Multi-stage ride status (requested, assigned, completed, cancelled)
- **Live Location Services**: Real-time GPS tracking and nearby driver visibility

### Payment System
- **Mock Payment Processing**: Simulated payment handling for MVP
- **Transaction Records**: Complete payment history and transaction tracking
- **Receipt Generation**: PDF receipt creation using ReportLab

### Service Layer Architecture
- **RideService**: Handles ride creation, driver assignment, and status management
- **PaymentService**: Processes payments and manages transaction records
- **PricingService**: Dynamic fare calculation based on distance and time
- **ReceiptService**: PDF generation for completed rides
- **LocationService**: Google Maps API integration for geocoding, routing, and location tracking

## Data Flow

1. **User Authentication**: Users authenticate via Replit Auth OAuth flow
2. **Profile Setup**: New users configure their role (rider/driver) and profile
3. **Ride Request**: Riders input pickup/dropoff locations and request rides
4. **Driver Assignment**: System automatically assigns available drivers
5. **Ride Execution**: Real-time status updates through the ride lifecycle
6. **Payment Processing**: Automatic fare calculation and payment processing
7. **Receipt Generation**: PDF receipts generated for completed rides

## External Dependencies

### Authentication
- **Replit Auth**: OAuth provider for user authentication
- **Flask-Dance**: OAuth client implementation
- **Flask-Login**: Session management and user context

### Database
- **PostgreSQL**: Primary database (configured via DATABASE_URL)
- **SQLAlchemy**: ORM with declarative base models
- **Connection Pooling**: Configured for production reliability

### Frontend
- **Bootstrap 5**: Responsive UI framework with dark theme
- **Bootstrap Icons**: Icon library for consistent UI elements
- **Custom CSS**: Enhanced styling for ride-sharing specific components

### PDF Generation
- **ReportLab**: Professional PDF receipt generation
- **Template System**: Structured receipt layout with ride details

### Live Location Services
- **Google Maps Integration**: Real-time location services with Places API
- **Driver Tracking**: Live GPS tracking with 30-second location updates
- **Nearby Driver Search**: Proximity-based driver matching within configurable radius
- **Route Optimization**: Real-time routing and distance calculation
- **Payment Gateway**: Mock payment processing for development

## Deployment Strategy

### Production Configuration
- **WSGI Server**: Gunicorn with optimized worker configuration
- **Auto-scaling**: Configured for automatic scaling based on load
- **Environment Variables**: 
  - `DATABASE_URL`: PostgreSQL connection string
  - `SESSION_SECRET`: Flask session encryption key

### Development Workflow
- **Hot Reload**: Gunicorn configured with `--reload` for development
- **Port Configuration**: Default port 5000 with proper binding
- **Logging**: Debug-level logging enabled for development

### Database Management
- **Auto-migration**: Database tables created automatically on startup
- **Schema Validation**: Proper foreign key relationships and constraints
- **Connection Management**: Pool recycling and pre-ping for reliability

## Changelog

```
Changelog:
- June 16, 2025. Initial setup
- June 16, 2025. Enhanced with live location services:
  * Real-time location tracking using browser geolocation
  * Interactive maps with OpenStreetMap/Leaflet integration
  * Address autocomplete using Nominatim geocoding
  * Nearby driver visibility within configurable radius
  * Live route planning and distance calculation
  * Driver location tracking page with GPS updates
  * Enhanced booking interface with live map
  * Sample demo data with realistic NYC locations
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```