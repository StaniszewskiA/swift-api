"""
Unit tests for the application startup and configuration.
"""

import pytest
from unittest.mock import AsyncMock, patch

with (
    patch("app.crud.swift_code_crud.create_tables", new_callable=AsyncMock),
    patch("app.crud.swift_code_crud.seed_swift_codes", new_callable=AsyncMock),
):
    from app.main import app


@pytest.mark.asyncio
async def test_lifespan_success(caplog, mock_create_tables, mock_seed_swift_codes, mock_app):
    with patch("app.main.create_tables", mock_create_tables), patch("app.main.seed_swift_codes", mock_seed_swift_codes):
        from app.main import lifespan

        async with lifespan(mock_app):
            mock_create_tables.assert_called_once()
            mock_seed_swift_codes.assert_called_once()

        assert "Starting the app" in caplog.text
        assert "Database initialization complete" in caplog.text
        assert "Shutting down the app" in caplog.text


@pytest.mark.asyncio
async def test_lifespan_with_exception(caplog, mock_create_tables_with_error, mock_seed_swift_codes, mock_app):
    with (
        patch("app.main.create_tables", mock_create_tables_with_error),
        patch("app.main.seed_swift_codes", mock_seed_swift_codes),
    ):
        from app.main import lifespan

        with pytest.raises(Exception) as exc_info:
            async with lifespan(mock_app):
                pass

        assert "Database error" in str(exc_info.value)

        mock_create_tables_with_error.assert_called_once()
        mock_seed_swift_codes.assert_not_called()

        assert "Starting the app" in caplog.text
        assert "Error during app startup: Database error" in caplog.text
        assert "Shutting down the app" in caplog.text


def test_app_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_app_metadata():
    assert app.title == "SWIFT Code Service"
    assert app.description == "API for querying bank SWIFT codes"
    assert app.version == "1.0.0"


def test_routers_included():
    route_paths = [route.path for route in app.routes]

    expected_routes = [
        "/v1/swift-codes/{swift_code}",
        "/v1/swift-codes/country/{country_iso2code}",
        "/v1/swift-codes/",
        "/v1/swift-codes/{swift_code}",
        "/",
    ]

    for route in expected_routes:
        assert route in route_paths, f"Expected route {route} not found in the application"
