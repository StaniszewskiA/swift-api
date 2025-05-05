# SWIFT Codes Service

A FastAPI-based microservice for parsing, storing, and retrieving bank SWIFT codes. This service provides a RESTful API for managing SWIFT code data and supports operations like querying by country or specific SWIFT code.

## Features

- **SWIFT Code Management**: Retrieve, add, and delete SWIFT codes
- **Country-based Queries**: Filter SWIFT codes by country
- **Branch Management**: Track relationships between bank headquarters and branches
- **Automated Data Loading**: Parse and load SWIFT codes from Excel files
- **Fully Async**: All I/O operations are asynchronous
- **Containerized**: Ready to deploy with Docker
- **Comprehensive Testing**: Unit and integration tests covering every public function

## Tech Stack

- **Python 3.11+**
- **FastAPI**: Modern, high-performance web framework
- **SQLAlchemy**: Asynchronous ORM for database operations
- **PostgreSQL**: Robust relational database
- **Pandas**: For data parsing and manipulation
- **Poetry**: Dependency management
- **Docker**: Containerization
- **pytest**: Testing framework

## Installation

### Prerequisites

- Python 3.11+
- Poetry
- Docker and Docker Compose (optional, for containerized execution)
- PostgreSQL (if running locally)

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/StaniszewskiA/swift-api
   cd swift-api
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

### Using Docker

1. Build and start the services:
   ```bash
   cd docker
   docker-compose up -d
   ```

## Running the Application

### Local Development

```bash
poetry run uvicorn app.main:app --reload --port 8080
```

### Using Makefile

```bash
# Install dependencies
make setup

# Run the service
make uvicorn-server
```

## Running Inside Docker

To run the application inside Docker, follow these steps:

1. Navigate to the `docker` directory:
   ```bash
   cd docker
   ```

2. Build and start the Docker containers:
   ```bash
   docker-compose up --build
   ```

3. Access the application at `http://localhost:8080` in your browser.

4. To stop the containers, run:
   ```bash
   docker-compose down
   ```

## API Documentation

When the service is running, access the auto-generated Swagger documentation at:
```
http://localhost:8080/docs
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/swift-codes/{swift_code}` | GET | Retrieve details of a specific SWIFT code |
| `/v1/swift-codes/country/{country_iso2code}` | GET | Get all SWIFT codes for a specific country |
| `/v1/swift-codes/` | POST | Add a new SWIFT code |
| `/v1/swift-codes/{swift_code}` | DELETE | Delete a SWIFT code |

## Testing

### Running Tests

Using direct pytest commands:
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app tests
```

Using Makefile (tested on Windows):
```bash
# Run linting checks
make test

# Run tests with coverage report
make test-coverage
```

### Test Database

Tests use either a mocked database or a separate PostgreSQL database specified by `TEST_DATABASE_URL` in the environment. When running with Docker, this is automatically configured.

## Project Structure

```
swift-api/
├── alembic/                # Database migrations
├── app/
│   ├── api/                # API route definitions
│   ├── core/               # Core functionality (DB, logging)
│   ├── crud/               # Database CRUD operations
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic services
│   └── main.py             # Application entry point
├── docker/                 # Docker configuration
│   ├── Dockerfile
│   └── docker-compose.yml
└── tests/
    ├── integration/        # Integration tests
    └── unit/               # Unit tests
```

## Configuration

The application can be configured using environment variables:

- `DATABASE_URL`: Connection string for the main database
- `TEST_DATABASE_URL`: Connection string for the test database
- `SWIFT_CODES_PATH`: Path to the Excel file containing SWIFT codes

## License

MIT

## Possible improvements:
- **API call caching**: Implement response caching to improve performance
- **Enhanced GitHub workflows**: Add more comprehensive CI/CD pipelines
