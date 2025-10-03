# IEP Projekat - Detaljan Plan Implementacije
## Sistem za upravljanje rada prodavnicom

### 📋 Pregled Projekta

**Opis sistema:**
Veb aplikacija za upravljanje prodavnicom sa multi-user pristupom koja podržava:
- Registraciju i autentikaciju korisnika (kupci, kuriri, vlasnici)
- Upravljanje proizvodima i kategorijama
- Kreiranje i praćenje narudžbina
- Sistem dostave putem kurira
- Blockchain plaćanja preko Ethereum platforme
- Statistike prodaje i kategorija

**Tehnologije:**
- Backend: Python, Flask, SQLAlchemy
- Baze podataka: MySQL (2 odvojene baze)
- Autentikacija: JWT tokeni
- Kontejnerizacija: Docker, Docker Compose
- Blockchain: Ethereum, Ganache CLI, Web3, Solidity

**Test struktura:**
- **Authentication**: Registracija, login, delete korisnika
- **Level 0**: Dodavanje i pretraga proizvoda
- **Level 1**: Kreiranje narudžbina
- **Level 2**: Preuzimanje i dostava narudžbina
- **Level 3**: Statistike za vlasnike

---

## 🎯 Implementacioni Plan

### Faza 1: Priprema i struktura projekta

#### **Korak 1: Kreiranje strukture direktorijuma**
```
IEPprojekat/
├── authentication/              # Autentikacija servis
│   ├── app.py                  # Flask aplikacija
│   ├── models.py               # User model
│   ├── requirements.txt        # Dependencies
│   └── Dockerfile             # Docker config
├── applications/               # Store servisi
│   ├── owner/                 # Vlasnik servis
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── customer/              # Kupac servis
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── courier/               # Kurir servis
│       ├── app.py
│       ├── requirements.txt
│       └── Dockerfile
├── shared/                     # Zajedničke komponente
│   ├── models.py              # SQLAlchemy modeli
│   └── utils.py               # Helper funkcije
├── blockchain/                 # Blockchain komponente
│   ├── contracts/             # Solidity smart contracts
│   └── deployment.py          # Contract deployment
├── database/                   # DB initialization
│   ├── auth_init.sql          # Auth DB init
│   └── store_init.sql         # Store DB init
├── docker-compose.yml          # Orchestration
└── README.md                   # Dokumentacija
```

#### **Korak 2: Kreiranje osnovnih konfiguracionih fajlova**
- Docker Compose sa servisima i mrežama
- Environment variables za konfiguraciju
- Requirements.txt fajlovi za svaki servis

---

### Faza 2: Database modeli i infrastruktura

#### **Korak 3: SQLAlchemy modeli**
**Authentication baza:**
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    forename = db.Column(db.String(256), nullable=False)
    surname = db.Column(db.String(256), nullable=False) 
    email = db.Column(db.String(256), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(64), nullable=False)  # customer/courier/owner
```

**Store baza:**
```python
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False)

class ProductCategory(db.Model):  # Many-to-many
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), primary_key=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_email = db.Column(db.String(256), nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(64), default='CREATED')  # CREATED/PENDING/COMPLETE
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    contract_address = db.Column(db.String(256))  # Blockchain

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
```

#### **Korak 4: Database inicijalizacija**
- Script za kreiranje tabela
- Dodavanje default owner korisnika:
  ```json
  {
    "forename": "Scrooge",
    "surname": "McDuck", 
    "email": "onlymoney@gmail.com",
    "password": "evenmoremoney"
  }
  ```

---

### Faza 3: Authentication servis

#### **Korak 5: Implementacija authentication endpoints**

**POST /register_customer & /register_courier**
```python
# Validacije (po redosledu):
1. Proveri postojanje svih polja (forename, surname, email, password)
2. Proveri format email-a (regex validation)
3. Proveri dužinu passworda (minimum 8 karaktera)
4. Proveri jedinstvnost email-a
```

**POST /login**
```python
# Funkcionalnost:
1. Validacija polja
2. Provera kredencijala
3. Generisanje JWT tokena sa:
   - exp: 1 sat od izdavanja
   - sub: email
   - forename, surname, roles
   - type: "access"
```

**POST /delete**
```python
# Funkcionalnost:
1. Validacija JWT tokena iz Authorization header
2. Brisanje korisnika iz baze
```

#### **Korak 6: JWT token implementacija**
```python
# Token struktura:
{
    "nbf": timestamp,
    "exp": timestamp + 3600,  # 1 sat
    "sub": email,
    "forename": "...",
    "surname": "...", 
    "roles": ["customer"|"courier"|"owner"],
    "type": "access"
}
```

---

### Faza 4: Owner servis

#### **Korak 7: Implementacija owner endpoints**

**POST /update** - Upload proizvoda
```python
# Funkcionalnost:
1. JWT validacija (owner role)
2. Validacija CSV file field
3. Parsing CSV: kategorije|ime|cena
4. Validacije:
   - Tačno 3 vrednosti po liniji
   - Cena > 0 (float)
   - Jedinstveno ime proizvoda
5. Batch insert proizvoda i kategorija
```

**GET /product_statistics**
```python
# SQL Query:
SELECT p.name, 
       SUM(CASE WHEN o.status = 'COMPLETE' THEN oi.quantity ELSE 0 END) as sold,
       SUM(CASE WHEN o.status IN ('CREATED', 'PENDING') THEN oi.quantity ELSE 0 END) as waiting
FROM products p
JOIN order_items oi ON p.id = oi.product_id  
JOIN orders o ON oi.order_id = o.id
GROUP BY p.id
HAVING sold > 0 OR waiting > 0
```

**GET /category_statistics**
```python
# SQL Query - sortiranje po broju dostavljenih proizvoda:
SELECT c.name, COUNT(*) as delivered_count
FROM categories c
JOIN product_categories pc ON c.id = pc.category_id
JOIN order_items oi ON pc.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'COMPLETE'
GROUP BY c.id
ORDER BY delivered_count DESC, c.name ASC
```

---

### Faza 5: Customer servis

#### **Korak 8: Implementacija customer endpoints**

**GET /search?name=...&category=...**
```python
# SQL Query sa filter logikom:
products_query = db.session.query(Product)
if name:
    products_query = products_query.filter(Product.name.contains(name))
if category:
    products_query = products_query.join(ProductCategory).join(Category)\
                                 .filter(Category.name.contains(category))

categories_query = db.session.query(Category)
if category:
    categories_query = categories_query.filter(Category.name.contains(category))
```

**POST /order** - Kreiranje narudžbine
```python
# Validacije:
1. Postojanje requests field
2. Za svaki request: id i quantity polja
3. Validacija product_id (integer > 0)
4. Validacija quantity (integer > 0)  
5. Postojanje proizvoda u bazi
6. (Blockchain) Validacija address polja

# Kreiranje:
1. Kreiranje Order zapisa
2. Kreiranje OrderItem zapisa
3. (Blockchain) Deployment smart contract
```

**GET /status** - Pregled narudžbina
```python
# Vraća sve narudžbine korisnika sa detaljima proizvoda
orders = Order.query.filter_by(customer_email=current_user_email).all()
```

**POST /delivered** - Potvrda dostave
```python
# Validacije:
1. Postojanje order_id
2. Order pripada korisniku
3. Order je u PENDING stanju
4. (Blockchain) Transfer sredstava

# Update:
order.status = 'COMPLETE'
```

#### **Korak 9: Blockchain integracija - customer**

**POST /generate_invoice**
```python
# Funkcionalnost:
1. Validacija order_id i address
2. Provera da transfer nije već izvršen
3. Generisanje transaction data za plaćanje
4. Vraćanje invoice objekta
```

---

### Faza 6: Courier servis

#### **Korak 10: Implementacija courier endpoints**

**GET /orders_to_deliver**
```python
# SQL Query:
SELECT o.id, o.customer_email
FROM orders o 
WHERE o.status = 'CREATED'
ORDER BY o.timestamp
```

**POST /pick_up_order**
```python
# Validacije:
1. Postojanje order_id
2. Order postoji i u CREATED stanju
3. (Blockchain) Validacija address
4. (Blockchain) Provera da je kupac platio

# Update:
order.status = 'PENDING'
```

---

### Faza 7: Blockchain implementacija

#### **Korak 11: Smart Contract (Solidity)**
```solidity
contract OrderPayment {
    address public customer;
    address public courier;
    address public owner;
    uint256 public orderPrice;
    bool public isPaid;
    bool public isDelivered;
    
    modifier onlyCustomer() { require(msg.sender == customer); _; }
    modifier onlyOwner() { require(msg.sender == owner); _; }
    
    function pay() external payable onlyCustomer {
        require(msg.value == orderPrice * 100, "Incorrect payment amount");
        isPaid = true;
    }
    
    function assignCourier(address _courier) external onlyOwner {
        require(isPaid, "Payment not received");
        courier = _courier;
    }
    
    function confirmDelivery() external onlyOwner {
        require(courier != address(0), "No courier assigned");
        
        // Transfer 80% to owner, 20% to courier
        payable(owner).transfer(address(this).balance * 80 / 100);
        payable(courier).transfer(address(this).balance);
        
        isDelivered = true;
    }
}
```

#### **Korak 12: Web3 integracija**
```python
# Setup u svakom servisu:
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('http://ganache:8545'))
owner_account = w3.eth.account.from_key(OWNER_PRIVATE_KEY)

# Contract deployment:
def deploy_order_contract(customer_address, order_price):
    contract = w3.eth.contract(abi=CONTRACT_ABI, bytecode=CONTRACT_BYTECODE)
    transaction = contract.constructor(customer_address, order_price).buildTransaction({
        'from': owner_account.address,
        'gas': 2000000,
        'gasPrice': 1
    })
    # ... deployment logic
```

---

### Faza 8: Docker konfiguracija

#### **Korak 13: Docker Compose setup**
```yaml
version: '3.8'

services:
  # Authentication network
  authentication:
    build: ./authentication
    ports:
      - "5000:5000"
    networks:
      - auth-network
    environment:
      - JWT_SECRET=JWT_SECRET_DEV_KEY
      - DB_HOST=auth-db

  auth-db:
    image: mysql:8.0
    networks:
      - auth-network
    environment:
      - MYSQL_DATABASE=authentication
    volumes:
      - auth-data:/var/lib/mysql

  # Store network  
  owner:
    build: ./applications/owner
    ports:
      - "5001:5000"
    networks:
      - store-network
    environment:
      - DB_HOST=store-db

  customer:
    build: ./applications/customer  
    ports:
      - "5002:5000"
    networks:
      - store-network

  courier:
    build: ./applications/courier
    ports:
      - "5003:5000" 
    networks:
      - store-network

  store-db:
    image: mysql:8.0
    networks:
      - store-network
    environment:
      - MYSQL_DATABASE=store
    volumes:
      - store-data:/var/lib/mysql

  ganache:
    image: trufflesuite/ganache-cli
    ports:
      - "8545:8545"
    networks:
      - store-network
    command: ["--accounts", "10", "--deterministic"]

networks:
  auth-network:
    driver: bridge
  store-network:
    driver: bridge

volumes:
  auth-data:
  store-data:
```

#### **Korak 14: Dockerfile za svaki servis**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

---

### Faza 9: Error handling i validacija

#### **Korak 15: Implementacija precise error messages**
Svi error responses moraju da budu tačno po specifikaciji:

```python
# Authentication errors:
"Field forename is missing."
"Invalid email."
"Invalid password."
"Email already exists."
"Invalid credentials."
"Missing Authorization Header"
"Unknown user."

# Owner errors:
"Field file missing."
"Incorrect number of values on line X."
"Incorrect price on line X." 
"Product <NAME> already exists."

# Customer errors:
"Field requests is missing."
"Product id is missing for request number X."
"Invalid product id for request number X."
"Invalid product for request number X."
"Missing order id."
"Invalid order id."
"Field address is missing."
"Invalid address."
"Transfer not complete."

# Courier errors:
"Missing order id."
"Invalid order id."
"Missing address." 
"Invalid address."
"Transfer not complete."
```

---

### Faza 10: Testiranje i finalizacija

#### **Korak 16: Test execution**
```bash
# Pokretanje sistema:
docker-compose up -d

# Authentication tests:
python Tests/main.py --type authentication \
    --authentication-url http://127.0.0.1:5000 \
    --jwt-secret JWT_SECRET_DEV_KEY \
    --roles-field roles \
    --owner-role owner \
    --customer-role customer \
    --courier-role courier

# Level tests bez blockchain:
python Tests/main.py --type all \
    --authentication-url http://127.0.0.1:5000 \
    --jwt-secret JWT_SECRET_DEV_KEY \
    --roles-field roles \
    --owner-role owner \
    --customer-role customer \
    --courier-role courier \
    --with-authentication \
    --owner-url http://127.0.0.1:5001 \
    --customer-url http://127.0.0.1:5002 \
    --courier-url http://127.0.0.1:5003

# Level tests sa blockchain:
python Tests/main.py --type all \
    --authentication-url http://127.0.0.1:5000 \
    --jwt-secret JWT_SECRET_DEV_KEY \
    --roles-field roles \
    --owner-role owner \
    --customer-role customer \
    --courier-role courier \
    --with-authentication \
    --owner-url http://127.0.0.1:5001 \
    --customer-url http://127.0.0.1:5002 \
    --courier-url http://127.0.0.1:5003 \
    --with-blockchain \
    --provider-url http://127.0.0.1:8545 \
    --owner-private-key 0xb64be88dd6b89facf295f4fd0dda082efcbe95a2bb4478f5ee582b7efe88cf60
```

#### **Korak 17: Debug common issues**
- JWT token format i expiration
- Database connection issues
- Network isolation between services
- Blockchain transaction failures
- CSV parsing edge cases
- Precise error message matching

#### **Korak 18: Performance optimization**
- Database indexing
- Connection pooling
- Caching frequently accessed data
- Proper Docker resource limits

---

## ✅ Acceptance Criteria

**Sistem je spreman kada:**
1. ✅ Svi authentication testovi prolaze (user registration, login, delete)
2. ✅ Level 0 testovi prolaze (product management, search)
3. ✅ Level 1 testovi prolaze (order creation)
4. ✅ Level 2 testovi prolaze (order delivery)
5. ✅ Level 3 testovi prolaze (owner statistics)
6. ✅ Blockchain integracija funkcioniše (opcional za max bodove)
7. ✅ Docker Compose pokreće sve servise uspešno
8. ✅ Network isolation je implementirana
9. ✅ Database persistence funkcioniše
10. ✅ Error handling je potpun i precizan

---

## 🚀 Deployment

**Finalno pokretanje:**
```bash
# Build i start svih servisa:
docker-compose build
docker-compose up -d

# Provera da li su servisi aktivni:
curl http://localhost:5000/  # Auth
curl http://localhost:5001/  # Owner  
curl http://localhost:5002/  # Customer
curl http://localhost:5003/  # Courier

# Pokretanje kompletnih testova:
cd Tests
python main.py --type all [sa svim potrebnim parametrima]
```

**Cilj:** Postići 100% na svim test nivoima za maksimalan broj bodova.