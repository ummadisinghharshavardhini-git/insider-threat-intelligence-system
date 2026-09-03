# Insider Threat Behavioral Intelligence System

## Project Architecture

This project detects risky or unusual behavior from users who already have legitimate access to an organization.

The system consists of four main layers:

1. Client/User Layer
2. API Gateway
3. Microservices Layer
4. Data Layer

## Architecture Layers

### 1. Client/User Layer
Users such as Security Analysts, SOC Engineers, Security Managers, and Admins access the system through the frontend.

### 2. API Gateway
The API Gateway is built using FastAPI. It handles authentication, routing, and rate limiting.

### 3. Microservices Layer
This layer contains modules for identity management, activity collection, behavioral profiling, anomaly detection, risk scoring, investigation, and alerting.

### 4. Data Layer
PostgreSQL is used for structured data such as users, employees, incidents, and alerts. MongoDB is used for flexible data such as raw activity logs and behavioral analytics.

<img width="205" height="536" alt="architecture-diagram" src="https://github.com/user-attachments/assets/97a9e747-d0ab-4ae4-9f40-2782c8495bdd" />
