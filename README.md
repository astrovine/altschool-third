My submission for altschool's python week 3 assessment, a backend application for creating events and managing RSVP .
I used FastAPI and PostgreSQL with SQLAlchemy (async). The application is also fully dockerised for portability(I recommend using that to start the application locally when cloned)

## Quick Start

### Using Docker

```bash
docker-compose up --build

docker-compose run migrate

docker-compose logs -f api
```

### Local Development

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

cp .env.example .env

alembic upgrade head

uvicorn application.main:app --reload
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=application --cov-report=term-missing

# Run specific test file
pytest tests/test_events.py -v
```