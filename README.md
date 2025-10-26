# IEP Projekat - Sistem za upravljanje prodavnicom

Mikroservisni sistem za e-trgovinu sa blockchain plaćanjem implementiran korišćenjem Python, Flask, MySQL, i Ethereum blockchain platforme.

## Pregled

Sistem se sastoji iz sledećih komponenti:
- **Authentication servis** - Registracija, prijava i autentikacija korisnika
- **Owner servis** - Upravljanje proizvodima i statistike
- **Customer servis** - Pretraga, naručivanje, plaćanje
- **Courier servis** - Preuzimanje i dostava narudžbina
- **Blockchain** - Ethereum smart contracts za payment processing

## Arhitektura

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

## Pokretanje Sistema

### Preduslovi
- Docker
- Docker Compose

### Setup

1. **Klonirati projekat**
```bash
git clone <repo-url>
cd IEPprojekat
```

2. **Konfigurisati environment varijable**
```bash
cp .env.example .env
# OWNER_PRIVATE_KEY će biti automatski generisan pri prvom pokretanju
```

3. **Build i pokretanje**
```bash
docker-compose build
docker-compose up -d
```

4. **Provera statusa**
```bash
docker-compose ps
```

## Testiranje

### Pokretanje testova

**Authentication testovi:**
```bash
python Tests/main.py --type authentication \
  --authentication-url http://127.0.0.1:5000 \
  --jwt-secret JWT_SECRET_DEV_KEY \
  --roles-field roles \
  --owner-role owner \
  --customer-role customer \
  --courier-role courier
```

**Svi testovi bez blockchain:**
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

**Svi testovi sa blockchain:**
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
- `POST /register_customer` - Registracija kupca
- `POST /register_courier` - Registracija kurira
- `POST /login` - Prijava korisnika
- `POST /delete` - Brisanje korisničkog naloga

### Owner Service (Port 5001)
- `POST /update` - Upload proizvoda (CSV)
- `GET /product_statistics` - Statistike proizvoda
- `GET /category_statistics` - Statistike kategorija

### Customer Service (Port 5002)
- `GET /search` - Pretraga proizvoda
- `POST /order` - Kreiranje narudžbine
- `GET /status` - Status narudžbina
- `POST /generate_invoice` - Generisanje invoice za plaćanje (blockchain)
- `POST /delivered` - Potvrda dostave

### Courier Service (Port 5003)
- `GET /orders_to_deliver` - Lista narudžbina za dostavu
- `POST /pick_up_order` - Preuzimanje narudžbine

## Tehnologije

- **Backend:** Python 3.9, Flask 2.3.0
- **Database:** MySQL 8.0
- **Authentication:** JWT (Flask-JWT-Extended)
- **Blockchain:** Ethereum (Ganache), Web3.py, Solidity
- **Deployment:** Docker, Docker Compose

## Struktura Projekta

```
IEPprojekat/
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

- Network isolation između authentication i store mreža
- JWT token authentication sa 1h expiracijom
- Password hashing (SHA256)
- Blockchain smart contract security

## Default Korisnici

**Owner (predefinisan):**
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
# Promeniti portove u docker-compose.yml
ports:
  - "50XX:5000"  # Promeniti 50XX
```

**Ganache not responding:**
```bash
docker-compose restart ganache
```

## License

ETF Beograd - IEP Projekat 2025

Luka Šćekić


