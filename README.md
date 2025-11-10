# Zeitec Verifier System - Complete Web Application

## 🎯 Overview

This is a complete, production-ready web application for the Zeitec Verifier System, covering all 3 phases:

- **Phase 1**: Registrant Management (Application & Approval)
- **Phase 2**: Device Registration (CSV Upload & Validation)
- **Phase 3**: Issuance & Verification (Deduplication & Verifier Review)

## 📦 What's Included

### Backend (Python Flask)
- REST API with 20+ endpoints
- PostgreSQL database integration
- JWT authentication
- CSV validation & deduplication
- File upload handling
- Audit trail logging

### Frontend (React + Tailwind CSS)
- Single-page application
- Responsive design
- Public registrant application form
- Status checking
- Admin dashboard for all 3 phases
- Real-time data updates

### Database
- Complete PostgreSQL schema
- All tables for 3 phases
- Indexes for performance
- Audit trail system

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 14+
- npm or yarn

### Step 1: Database Setup

```bash
# Create PostgreSQL database
createdb zeitec_verifier

# Create database user
psql postgres -c "CREATE USER zeitec_user WITH PASSWORD 'zeitec_password';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE zeitec_verifier TO zeitec_user;"

# Run schema
psql zeitec_verifier < database/schema.sql
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your database credentials

# Run the backend
python app.py
```

Backend will run on http://localhost:5000

### Step 3: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env

# Run the frontend
npm start
```

Frontend will run on http://localhost:3000

## 🧪 Testing the Application

### 1. Test Registrant Application (Public)

1. Go to http://localhost:3000
2. Click "Apply as Registrant"
3. Fill in the form:
   - Organization Name: NASENI Solar Project
   - Contact Person: John Doe
   - Email: test@naseni.gov.ng
   - Country: Nigeria
   - Number of Facilities: 5
   - Total Capacity: 1250 kW
4. Upload a test document (any PDF)
5. Submit
6. Note the email address

### 2. Check Application Status (Public)

1. Click "Check Status"
2. Enter the email: test@naseni.gov.ng
3. See status: "PENDING"

### 3. Login as Admin

1. Click "Admin Login"
2. Credentials:
   - Username: `admin`
   - Password: `admin123`
3. You'll see the admin dashboard

### 4. Approve Registrant (Admin)

1. In admin dashboard, you'll see the pending application
2. Click "Approve"
3. Application status changes to "APPROVED"

### 5. Test Device Registration

Create a test CSV file (`test_devices.csv`):

```csv
deviceId,facilityId,serialNumber,manufacturer,model,capacityKW,technology,country,gridConnectionPoint,commissioningDate
DEV001,FAC001,SN12345,SolarTech,ST-5000,50,Solar PV,Nigeria,AEDC-Lagos-North,2024-01-15
DEV002,FAC002,SN12346,SolarTech,ST-5000,45,Solar PV,Nigeria,AEDC-Lagos-South,2024-01-20
```

Use Postman or curl:

```bash
curl -X POST http://localhost:5000/api/devices/submit \
  -F "registrant_email=test@naseni.gov.ng" \
  -F "device_registry_csv=@test_devices.csv" \
  -F "owner_declaration=@test_declaration.pdf"
```

### 6. Test Issuance Submission

Create a test issuance CSV (`test_issuance.csv`):

```csv
deviceId,timestamp,kWh,auditTrailId
DEV001,2024-01-15T00:00:00Z,12.5,abc123...
DEV001,2024-01-15T01:00:00Z,13.2,def456...
```

Submit via API:

```bash
curl -X POST http://localhost:5000/api/issuance/submit \
  -F "registrant_email=test@naseni.gov.ng" \
  -F "device_id=1" \
  -F "issuance_period_csv=@test_issuance.csv" \
  -F "registrant_declaration=@test_declaration.pdf"
```

## 📝 API Documentation

### Authentication Endpoints

#### POST /api/auth/login
Login as admin

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJ...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJ...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@zeitec.io",
    "full_name": "System Administrator"
  }
}
```

### Registrant Endpoints

#### POST /api/registrants/apply
Public endpoint - Submit registrant application

**Form Data:**
- `organization_name` (required)
- `contact_person` (required)
- `email` (required)
- `phone`
- `country` (required)
- `num_facilities`
- `total_capacity_kw`
- `description`
- `business_document` (file)

#### GET /api/registrants/status/{email}
Public endpoint - Check application status

#### GET /api/registrants/
Admin endpoint - List all registrants

**Query params:**
- `status` (pending/approved/rejected)
- `country`
- `page`
- `per_page`

#### PUT /api/registrants/{id}/approve
Admin endpoint - Approve registrant

#### PUT /api/registrants/{id}/reject
Admin endpoint - Reject registrant

### Device Endpoints

#### POST /api/devices/submit
Registrant endpoint - Submit device registry CSV

**Form Data:**
- `registrant_email` (required)
- `device_registry_csv` (required file)
- `owner_declaration` (file)
- `single_line_diagram` (file)
- `ppa` (file)
- `site_photos` (multiple files)

#### GET /api/devices/
Admin endpoint - List all devices

#### PUT /api/devices/{id}/approve
Admin endpoint - Approve device

#### PUT /api/devices/{id}/reject
Admin endpoint - Reject device

### Issuance Endpoints

#### POST /api/issuance/submit
Registrant endpoint - Submit issuance period CSV

**Form Data:**
- `registrant_email` (required)
- `device_id` (required)
- `issuance_period_csv` (required file)
- `registrant_declaration` (file)

#### GET /api/issuance/
Verifier endpoint - List all submissions

#### POST /api/issuance/{id}/review
Verifier endpoint - Create review

**Request:**
```json
{
  "decision": "approved",
  "review_notes": "All checks passed",
  "checklist": {
    "device_metadata_matches": true,
    "owner_declaration_valid": true,
    "supporting_docs_complete": true,
    "data_granularity_correct": true,
    "energy_values_reasonable": true,
    "no_timestamp_gaps": true,
    "measurement_tier_declared": true,
    "device_scope_confirmed": true,
    "grouping_keys_consistent": true,
    "no_dedupe_collisions": true
  },
  "measurement_tier": "2.3",
  "device_scope_confirmed": true,
  "grouping_keys_consistent": true,
  "no_dedupe_collisions": true
}
```

## 🔒 Security

### Production Deployment Checklist

1. **Change default admin password immediately**
   ```bash
   curl -X POST http://localhost:5000/api/auth/change-password \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json" \
     -d '{"current_password":"admin123", "new_password":"YourSecurePassword123!"}'
   ```

2. **Set environment variables for production:**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY="your-secret-key-here"
   export JWT_SECRET_KEY="your-jwt-secret-here"
   export DATABASE_URL="postgresql://..."
   ```

3. **Use HTTPS in production** - Configure reverse proxy (nginx/Apache)

4. **Set up CORS properly** - Restrict allowed origins

5. **Enable rate limiting** - Add Flask-Limiter

6. **Regular backups** - Schedule PostgreSQL backups

## 🐳 Docker Deployment (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: zeitec_verifier
      POSTGRES_USER: zeitec_user
      POSTGRES_PASSWORD: zeitec_password
    volumes:
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      FLASK_ENV: production
      DATABASE_URL: postgresql://zeitec_user:zeitec_password@db:5432/zeitec_verifier
    ports:
      - "5000:5000"
    depends_on:
      - db

  frontend:
    build: ./frontend
    environment:
      REACT_APP_API_URL: http://localhost:5000/api
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

Run:
```bash
docker-compose up -d
```

## 📊 Database Schema

### Key Tables

1. **admins** - System administrators
2. **registrants** - Registered organizations
3. **devices** - Solar devices/facilities
4. **device_documents** - Supporting documents
5. **issuance_submissions** - Energy production submissions
6. **deduplication_log** - Audit trail for duplicate prevention
7. **verifier_reviews** - Verifier approvals
8. **audit_trail** - System audit log

## 🛠️ Troubleshooting

### Backend won't start
- Check PostgreSQL is running: `pg_isready`
- Verify database credentials in `.env`
- Check Python version: `python --version` (should be 3.9+)

### Frontend won't start
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node version: `node --version` (should be 16+)
- Verify API URL in `.env`

### Database connection error
- Check PostgreSQL service: `sudo systemctl status postgresql`
- Verify database exists: `psql -l | grep zeitec_verifier`
- Test connection: `psql zeitec_verifier -U zeitec_user`

### File upload errors
- Check upload directory exists and has write permissions
- Verify file size limits in config

## 📞 Support

For issues or questions:
1. Check this README
2. Review API documentation above
3. Check logs:
   - Backend: `tail -f backend/logs/app.log`
   - Frontend: Browser console (F12)

## 📄 License

Proprietary - Zeitec GreenFlow Project

---

**Built for the Zeitec GreenFlow Data Verifier Project**
Version 1.0.0 | 2025
