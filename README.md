# E-Commerce Platform with Blockchain Payment Integration

Microservices-based e-commerce system with blockchain payment processing built using Python, Flask, MySQL, and Ethereum blockchain platform.

## Overview

The system consists of the following components:
- **Authentication service** - User registration, login, and authentication
- **Owner service** - Product management and statistics
- **Customer service** - Product search, ordering, payment
- **Courier service** - Order pickup and delivery
- **Blockchain** - Ethereum smart contracts for payment processing

## Architecture

```
Authentication Network (Isolated)
├── authenticationDB (MySQL)
└── authentication service

Store Network (Isolated)
├── storeDB (MySQL)
├── ganache (Ethereum)
├── owner service
├── customer service
└── courier service
```

## Getting Started

### Prerequisites
- Docker
- Docker Compose

### Setup

1. **Clone the repository**
```bash
git clone <repo-url>
cd blockchain-ecommerce-platform
```

2. **Configure environment variables**
```bash
cp .env.example .env
# OWNER_PRIVATE_KEY will be automatically generated on first run
```

3. **Build and start services**
```bash
docker-compose build
docker-compose up -d
```

4. **Check service status**
```bash
docker-compose ps
```

## Testing

### Running Tests

**Authentication tests:**
```bash
python Tests/main.py --type authentication \
  --authentication-url http://127.0.0.1:5000 \
  --jwt-secret JWT_SECRET_DEV_KEY \
  --roles-field roles \
  --owner-role owner \
  --customer-role customer \
  --courier-role courier
```

**All tests without blockchain:**
```bash
python Tests/main.py --type all \
  --with-authentication \
  --authentication-url http://127.0.0.1:5000 \
  --jwt-secret JWT_SECRET_DEV_KEY \
  --roles-field roles \
  --owner-role owner \
  --customer-role customer \
  --courier-role courier \
  --owner-url http://127.0.0.1:5001 \
  --customer-url http://127.0.0.1:5002 \
  --courier-url http://127.0.0.1:5003
```

**All tests with blockchain:**
```bash
python Tests/main.py --type all \
  --with-authentication \
  --authentication-url http://127.0.0.1:5000 \
  --jwt-secret JWT_SECRET_DEV_KEY \
  --roles-field roles \
  --owner-role owner \
  --customer-role customer \
  --courier-role courier \
  --owner-url http://127.0.0.1:5001 \
  --customer-url http://127.0.0.1:5002 \
  --courier-url http://127.0.0.1:5003 \
  --with-blockchain \
  --provider-url http://127.0.0.1:8545 \
  --owner-private-key <OWNER_PRIVATE_KEY>
```

## API Endpoints

### Authentication Service (Port 5000)
- `POST /register_customer` - Register customer account
- `POST /register_courier` - Register courier account
- `POST /login` - User login
- `POST /delete` - Delete user account

### Owner Service (Port 5001)
- `POST /update` - Upload products (CSV)
- `GET /product_statistics` - Product statistics
- `GET /category_statistics` - Category statistics

### Customer Service (Port 5002)
- `GET /search` - Search products
- `POST /order` - Create order
- `GET /status` - Order status
- `POST /generate_invoice` - Generate payment invoice (blockchain)
- `POST /delivered` - Confirm delivery

### Courier Service (Port 5003)
- `GET /orders_to_deliver` - List orders for delivery
- `POST /pick_up_order` - Pick up order

## Technologies

- **Backend:** Python 3.9, Flask 2.3.0
- **Database:** MySQL 8.0
- **Authentication:** JWT (Flask-JWT-Extended)
- **Blockchain:** Ethereum (Ganache), Web3.py, Solidity
- **Deployment:** Docker, Docker Compose

## Project Structure

```
blockchain-ecommerce-platform/
├── authentication/
│   ├── application.py
│   ├── configuration.py
│   ├── models.py
│   ├── requirements.txt
│   └── Dockerfile
├── applications/
│   ├── configuration.py (shared)
│   ├── models.py (shared)
│   ├── owner/
│   │   ├── application.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── customer/
│   │   ├── application.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── courier/
│       ├── application.py
│       ├── requirements.txt
│       └── Dockerfile
├── blockchain/
│   ├── PaymentContract.sol
│   ├── compile.py
│   └── deploy.py
├── Tests/
├── docker-compose.yml
├── .env
└── README.md
```

## Security

- Network isolation between authentication and store networks
- JWT token authentication with 1h expiration
- Password hashing (SHA256)
- Blockchain smart contract security

## Default Users

**Owner (predefined):**
- Email: `onlymoney@gmail.com`
- Password: `evenmoremoney`
- Role: `owner`

## Troubleshooting

**Database connection error:**
```bash
docker-compose down -v
docker-compose up -d
```

**Port already in use:**
```bash
# Change ports in docker-compose.yml
ports:
  - "50XX:5000"  # Change 50XX
```

**Ganache not responding:**
```bash
docker-compose restart ganache
```

## License

University of Belgrade, School of Electrical Engineering - 2025
