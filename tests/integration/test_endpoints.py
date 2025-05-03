"""
Integration tests for the SWIFT Code API endpoints.

These tests verify the behavior of all API endpoints by making actual HTTP
requests to the application and checking the responses.
"""

import pytest


#############################################
# Helper Functions
#############################################


async def create_test_swift_code(client, swift_code_data):
    """Helper function to create a test SWIFT code via the API"""
    return await client.post("/v1/swift-codes/", json=swift_code_data)


#############################################
# Create Endpoint Tests
#############################################


@pytest.mark.asyncio
async def test_add_swift_code_success(async_test_client, test_swift_code_data):
    response = await create_test_swift_code(async_test_client, test_swift_code_data)

    assert response.status_code == 201
    assert response.json()["message"] == "SWIFT code added successfully"
    assert response.json()["swiftCode"] == "TESTCODE123"


@pytest.mark.asyncio
async def test_add_swift_code_duplicate(async_test_client, test_swift_code_data):
    await create_test_swift_code(async_test_client, test_swift_code_data)

    response = await create_test_swift_code(async_test_client, test_swift_code_data)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


#############################################
# Read Endpoint Tests
#############################################


@pytest.mark.asyncio
async def test_get_swift_code_success(async_test_client, test_swift_code_data):
    await create_test_swift_code(async_test_client, test_swift_code_data)

    response = await async_test_client.get("/v1/swift-codes/TESTCODE123")

    assert response.status_code == 200
    assert response.json()["swiftCode"] == "TESTCODE123"
    assert response.json()["bankName"] == "Test Bank"
    assert response.json()["countryISO2"] == "PL"
    assert response.json()["isHeadquarter"] is True


@pytest.mark.asyncio
async def test_get_swift_code_not_found(async_test_client):
    response = await async_test_client.get("/v1/swift-codes/NONEXISTENT")

    assert response.status_code == 404
    assert response.json()["detail"] == "SWIFT code not found"


@pytest.mark.asyncio
async def test_get_swift_codes_by_country_success(async_test_client, test_swift_code_data):
    await create_test_swift_code(async_test_client, test_swift_code_data)

    response = await async_test_client.get("/v1/swift-codes/country/PL")

    assert response.status_code == 200
    assert response.json()["countryISO2"] == "PL"
    assert response.json()["countryName"] == "POLAND"
    assert len(response.json()["swiftCodes"]) >= 1

    swift_codes = [code["swiftCode"] for code in response.json()["swiftCodes"]]
    assert "TESTCODE123" in swift_codes


@pytest.mark.asyncio
async def test_get_swift_codes_by_country_not_found(async_test_client):
    response = await async_test_client.get("/v1/swift-codes/country/ZZ")

    assert response.status_code == 404
    assert response.json()["detail"] == "No SWIFT codes found for this country"


#############################################
# Delete Endpoint Tests
#############################################


@pytest.mark.asyncio
async def test_delete_swift_code_success(async_test_client, test_swift_code_data):
    await create_test_swift_code(async_test_client, test_swift_code_data)

    response = await async_test_client.delete("/v1/swift-codes/TESTCODE123")

    assert response.status_code == 200
    assert response.json()["message"] == "SWIFT code TESTCODE123 deleted successfully"

    verify_response = await async_test_client.get("/v1/swift-codes/TESTCODE123")
    assert verify_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_swift_code_not_found(async_test_client):
    response = await async_test_client.delete("/v1/swift-codes/NONEXISTENT")

    assert response.status_code == 404
    assert response.json()["detail"] == "SWIFT code not found"
