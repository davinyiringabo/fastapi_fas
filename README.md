# Student Financial Aid System API

A FastAPI-based backend service for managing student financial aid applications.

## Features

### User Types
- **Students**: Can register, apply for aid, and track applications
- **Managers**: Review and process aid applications
- **Administrators**: Manage users and oversee the system

### Authentication & Security
- Email/Password authentication
- JWT token-based authorization
- Email verification for new accounts
- Secure password reset flow

### Core Functionality

#### Students
- Account registration with email verification
- Login/Authentication
- Apply for financial aid
- Track application status
- View application history

#### Managers
- Application review
- Approve/Reject applications
- View all applications

#### Administrators
- User management
- Manager account creation
- View all system data
- Deactivate manager accounts

## Technical Setup

### Prerequisites
- Python 3.8+
- PostgreSQL
- SMTP server access for emails

### Environment Variables
Create a `.env` file with: 