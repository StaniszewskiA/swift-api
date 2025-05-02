import pytest
from httpx import AsyncClient
from app.main import app
from httpx._transports.asgi import ASGITransport


@pytest.fixture
async def test_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def create_test_swift_code(client):
    return await client.post(
        "/v1/swift-codes/",
        json={
            "address": "123 Test St",
            "bankName": "Test Bank",
            "countryISO2": "PL",
            "countryName": "POLAND",
            "isHeadquarter": True,
            "swiftCode": "TESTCODE123",
        },
    )


@pytest.mark.asyncio
async def test_add_swift_code_success(test_client):
    response = await create_test_swift_code(test_client)
    assert response.status_code == 201
    assert response.json()["message"] == "SWIFT code added successfully"
    assert response.json()["swiftCode"] == "TESTCODE123"


@pytest.mark.asyncio
async def test_add_swift_code_duplicate(test_client):
    await create_test_swift_code(test_client)

    response = await create_test_swift_code(test_client)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_swift_code_success(test_client):
    await create_test_swift_code(test_client)

    response = await test_client.get("/v1/swift-codes/TESTCODE123")
    assert response.status_code == 200
    assert response.json()["swiftCode"] == "TESTCODE123"
    assert response.json()["bankName"] == "Test Bank"
    assert response.json()["countryISO2"] == "PL"
    assert response.json()["isHeadquarter"] is True


@pytest.mark.asyncio
async def test_get_swift_code_not_found(test_client):
    response = await test_client.get("/v1/swift-codes/NONEXISTENT")
    assert response.status_code == 404
    assert response.json()["detail"] == "SWIFT code not found"


@pytest.mark.asyncio
async def test_get_swift_codes_by_country_success(test_client):
    await create_test_swift_code(test_client)

    response = await test_client.get("/v1/swift-codes/country/PL")
    assert response.status_code == 200
    assert response.json()["countryISO2"] == "PL"
    assert response.json()["countryName"] == "POLAND"
    assert len(response.json()["swiftCodes"]) >= 1

    swift_codes = [code["swiftCode"] for code in response.json()["swiftCodes"]]
    assert "TESTCODE123" in swift_codes


@pytest.mark.asyncio
async def test_get_swift_codes_by_country_not_found(test_client):
    response = await test_client.get("/v1/swift-codes/country/ZZ")
    assert response.status_code == 404
    assert response.json()["detail"] == "No SWIFT codes found for this country"


@pytest.mark.asyncio
async def test_delete_swift_code_success(test_client):
    await create_test_swift_code(test_client)

    response = await test_client.delete("/v1/swift-codes/TESTCODE123")
    assert response.status_code == 200
    assert response.json()["message"] == "SWIFT code TESTCODE123 deleted successfully"

    verify_response = await test_client.get("/v1/swift-codes/TESTCODE123")
    assert verify_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_swift_code_not_found(test_client):
    response = await test_client.delete("/v1/swift-codes/NONEXISTENT")
    assert response.status_code == 404
    assert response.json()["detail"] == "SWIFT code not found"
