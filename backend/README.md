# TBDC Backend - Zoho CRM Integration

FastAPI backend for Zoho CRM integration with automatic OAuth token management.

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py       # OAuth flow endpoints
│   │       │   ├── leads.py      # Lead CRUD operations
│   │       │   └── zoho.py       # Generic Zoho endpoints
│   │       └── router.py         # API router aggregation
│   ├── core/
│   │   ├── config.py             # Settings & configuration
│   │   ├── exceptions.py         # Custom exceptions
│   │   └── logging.py            # Logging configuration
│   ├── middleware/
│   │   └── zoho_token.py         # Token management middleware
│   ├── models/
│   │   └── token.py              # Database models (optional)
│   ├── schemas/
│   │   └── lead.py               # Pydantic schemas
│   ├── services/
│   │   └── zoho/
│   │       ├── crm_service.py    # Zoho CRM API service
│   │       └── token_manager.py  # OAuth token manager
│   ├── utils/
│   │   └── dependencies.py       # FastAPI dependencies
│   └── main.py                   # Application entry point
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── run.py                        # Dev server runner
└── README.md                     # This file
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Zoho OAuth

1. Go to [Zoho API Console](https://api-console.zoho.com/)
2. Create a new Server-based Application
3. Configure the following:
   - **Homepage URL**: `http://localhost:8000`
   - **Authorized Redirect URI**: `http://localhost:8000/api/v1/auth/zoho/callback`
   - **Scopes**: `ZohoCRM.modules.ALL`, `ZohoCRM.settings.ALL`
4. Copy the Client ID and Client Secret

### 4. Set Environment Variables

```bash
cp .env.example .env
# Edit .env with your Zoho credentials
```

### 5. Get Refresh Token (First-time Setup)

```bash
# Start the server
python run.py

# Visit in browser to authorize:
# http://localhost:8000/api/v1/auth/zoho/authorize

# After authorization, you'll receive a refresh token
# Add it to your .env file as ZOHO_REFRESH_TOKEN
```

### 6. Run the Application

```bash
python run.py
# Or
uvicorn app.main:app --reload
```

## API Endpoints

### Health Check
- `GET /health` - Application health status

### Authentication
- `GET /api/v1/auth/zoho/authorize` - Start OAuth flow
- `GET /api/v1/auth/zoho/callback` - OAuth callback
- `GET /api/v1/auth/zoho/status` - Check token status

### Leads
- `GET /api/v1/leads/` - List leads (paginated)
- `GET /api/v1/leads/{id}` - Get lead by ID
- `POST /api/v1/leads/` - Create lead
- `PUT /api/v1/leads/{id}` - Update lead
- `DELETE /api/v1/leads/{id}` - Delete lead
- `GET /api/v1/leads/search/` - Search leads

### Generic Zoho
- `GET /api/v1/zoho/modules/{module}` - Get any module records
- `GET /api/v1/zoho/contacts/` - List contacts
- `GET /api/v1/zoho/deals/` - List deals

## Token Management

The application automatically manages Zoho OAuth tokens:

1. **Automatic Refresh**: Tokens are refreshed 5 minutes before expiry
2. **Background Task**: A background task handles token refresh
3. **Middleware Injection**: Valid tokens are injected into request state
4. **Retry Logic**: Failed API calls due to expired tokens trigger automatic refresh

## Zoho Data Centers

Configure the correct URLs based on your Zoho data center:

| Region | Accounts URL | API Base URL |
|--------|--------------|--------------|
| US | accounts.zoho.com | www.zohoapis.com |
| EU | accounts.zoho.eu | www.zohoapis.eu |
| IN | accounts.zoho.in | www.zohoapis.in |
| AU | accounts.zoho.com.au | www.zohoapis.com.au |
| CN | accounts.zoho.com.cn | www.zohoapis.com.cn |
| JP | accounts.zoho.jp | www.zohoapis.jp |

## API Documentation

Once running, access the interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
