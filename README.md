# 🏨 Looking.com Backend - CapCorn API Wrapper

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-ready FastAPI backend that wraps the CapCorn Hotel Booking API, providing enhanced functionality, simplified interfaces, and analytics capabilities for the Looking.com platform.

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
- [API Endpoints](#-api-endpoints)
- [Configuration](#-configuration)
- [Development](#-development)
- [Deployment](#-deployment)
- [Analytics](#-analytics)

## 🎯 Overview

This backend serves as an intelligent middleware layer between the Looking.com UI and the CapCorn Hotel Management System. It transforms complex XML-based APIs into modern REST endpoints with JSON payloads, while adding powerful features like:

- **Flexible date range searches** - Search multiple date combinations in parallel
- **Booking analytics** - Track reservations, popular dates, and customer patterns
- **Simplified interfaces** - User-friendly request/response models
- **MCP Server integration** - Serves data to Model Context Protocol servers for AI-powered analytics
- **Dashboard support** - Powers the Looking.com analytics dashboard

### 🔌 Integration Flow

```
Looking.com UI → MCP Server → FastAPI Backend → CapCorn API
                     ↓
              Analytics Dashboard
```

## ✨ Features

### 🔍 Enhanced Room Search

- **Intelligent Date Ranges**: Specify a timespan and duration, get all possible booking combinations
- **Parallel Processing**: Execute multiple searches concurrently for lightning-fast results
- **Smart Validation**: Pydantic models ensure data integrity
- **Language Support**: Easy-to-use language codes (`"en"`, `"de"`)

### 📊 Analytics Capabilities

Track and analyze:
- 📈 Total bookings made through the platform
- 💰 Revenue metrics and pricing trends
- 📅 Popular booking dates and durations
- 🏠 Most requested room types
- 👥 Guest demographics (adults/children ratios)
- 🌍 Geographic distribution of bookings

### 🛡️ Production-Ready Features

- ✅ Comprehensive input validation with Pydantic
- ✅ Async/await for high performance
- ✅ CORS support for web applications
- ✅ Environment-based configuration
- ✅ Detailed API documentation (OpenAPI/Swagger)
- ✅ Error handling and logging
- ✅ Type safety throughout

## 🏗️ Architecture

### Directory Structure

```
lookingcom-backend/
├── src/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/                       # API route handlers
│   │   └── v1/
│   │       ├── rooms.py          # Room search endpoints
│   │       ├── reservations.py   # Booking endpoints
│   │       └── router.py         # Route aggregation
│   ├── schemas/                   # Pydantic request/response models
│   │   ├── room_availability.py  # Room search schemas
│   │   ├── reservation.py        # Booking schemas
│   │   └── simplified_search.py  # Enhanced search models
│   ├── services/                  # Business logic layer
│   │   └── capcorn_client.py     # CapCorn API client
│   ├── core/                      # Core configuration
│   │   └── config.py             # Settings management
│   └── models/                    # Database models (future)
├── .env                           # Environment variables
├── pyproject.toml                 # UV/Python dependencies
└── README.md                      # This file
```

### 🔄 Separation of Concerns

- **API Layer** (`api/`): HTTP request handling, routing, validation
- **Schemas** (`schemas/`): Request/response models, data validation
- **Services** (`services/`): Business logic, external API communication
- **Core** (`core/`): Configuration, settings, utilities
- **Models** (`models/`): Database models for analytics (future)

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- [UV](https://github.com/astral-sh/uv) - Fast Python package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sbergsmann/lookingcom-backend.git
   cd lookingcom-backend
   ```

2. **Install dependencies with UV**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the development server**
   ```bash
   uv run fastapi dev src/main.py
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🔌 API Endpoints

### Health Check

```http
GET /
GET /health
```

Returns service status and version information.

### 🏠 Room Search (Simplified)

```http
POST /api/v1/rooms/search
```

**Request Body:**
```json
{
  "language": "de",
  "timespan": {
    "from": "2025-12-17",
    "to": "2025-12-24"
  },
  "duration": 4,
  "adults": 2,
  "children": [
    {"age": 3},
    {"age": 7}
  ]
}
```

**Features:**
- Generates all possible date ranges within the timespan
- Executes parallel searches for maximum performance
- Returns aggregated results with date information

**Response:**
```json
{
  "total_queries": 4,
  "total_options": 24,
  "duration_days": 4,
  "options": [
    {
      "arrival": "2025-12-17",
      "departure": "2025-12-21",
      "catc": "DZ",
      "type": "Doppelzimmer",
      "description": "Zimmer with balcony...",
      "size": 28,
      "price": 675.0,
      "price_per_person": 225.0,
      "price_per_adult": 337.5,
      "price_per_night": 168.75,
      "board": 1,
      "room_type": 1
    }
  ]
}
```

### 🏠 Room Availability (Direct)

```http
POST /api/v1/rooms/availability
```

Direct access to CapCorn API with original format (for advanced users).

### 📝 Create Reservation

```http
POST /api/v1/reservations
```

**Request Body:**
```json
{
  "hotel_id": "9100",
  "room_type_code": "DZ",
  "number_of_units": 1,
  "meal_plan": 1,
  "guest_counts": [
    {"age_qualifying_code": 10, "count": 2},
    {"age_qualifying_code": 8, "age": 3, "count": 1}
  ],
  "arrival": "2025-12-17",
  "departure": "2025-12-20",
  "total_amount": 675.0,
  "guest": {
    "name_prefix": "Herr",
    "given_name": "Max",
    "surname": "Mustermann",
    "phone_number": "+436641234567",
    "email": "max@example.com",
    "address": {
      "address_line": "Hauptstraße 1",
      "city_name": "Vienna",
      "postal_code": "1010",
      "country_code": "AT"
    }
  },
  "reservation_id": "BOOK-12345",
  "source": "LookingCom"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Reservation created successfully",
  "reservation_id": "BOOK-12345"
}
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Application
DEBUG=False

# CapCorn API Configuration
CAPCORN_BASE_URL=https://mainframe.capcorn.net/RestService
CAPCORN_SYSTEM=ttf-hackathon
CAPCORN_USER=ttf
CAPCORN_PASSWORD=your_password
CAPCORN_HOTEL_ID=9100
CAPCORN_PIN=your_pin

# CORS (comma-separated list or *)
CORS_ORIGINS=*
```

### Meal Plans

| Code | Description |
|------|-------------|
| 1    | Breakfast |
| 2    | Half Board |
| 3    | Full Board |
| 4    | No Meals |
| 5    | All Inclusive |

### Room Types

| Code | Description |
|------|-------------|
| 1    | Hotel Room |
| 2    | Apartment / Holiday Home |

## 🛠️ Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black src/
uv run isort src/
```

### Type Checking

```bash
uv run mypy src/
```

### Running with Hot Reload

```bash
uv run fastapi dev src/main.py
```

## 🐳 Deployment

### Docker Support

```bash
# Build image
docker build -t lookingcom-backend .

# Run container
docker run -p 8000:8000 --env-file .env lookingcom-backend
```

### Docker Compose

```bash
docker-compose up -d
```

### Production Considerations

- Use a production ASGI server (Uvicorn/Gunicorn)
- Enable HTTPS with proper certificates
- Set up logging and monitoring
- Configure rate limiting
- Use environment-specific configs
- Set `DEBUG=False` in production

## 📊 Analytics

The backend is designed to integrate with analytics systems and dashboards:

### 🎯 MCP Server Integration

The API endpoints are consumed by Model Context Protocol (MCP) servers that:
- Process booking data for AI-powered insights
- Generate recommendations based on booking patterns
- Provide natural language interfaces to the data
- Power conversational analytics experiences

### 📈 Dashboard Metrics

Data served to the Looking.com analytics dashboard includes:

- **Booking Trends**: Daily, weekly, monthly reservation counts
- **Revenue Analytics**: Total bookings value, average booking size
- **Room Performance**: Most popular room categories and types
- **Customer Insights**: Guest demographics, booking lead times
- **Seasonal Patterns**: Peak and off-peak periods identification
- **Conversion Metrics**: Search-to-booking conversion rates

### 🔮 Future Analytics Features

- Real-time booking notifications
- Predictive pricing recommendations
- Customer segmentation analysis
- Competitive benchmarking
- Dynamic pricing optimization
- Availability forecasting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is proprietary software developed for Looking.com.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [UV](https://github.com/astral-sh/uv)
- Integrates with [CapCorn Hotel Management System](https://capcorn.at/)

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Contact: dev@looking.com

---

**Made with ❤️ for Tourism Technology Festival Hackathon 2025**