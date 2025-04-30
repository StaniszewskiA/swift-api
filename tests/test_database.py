import pytest
from unittest.mock import MagicMock, patch
from app.core.database import yield_db, SessionLocal


@pytest.fixture
def mock_session():
    mock_db = MagicMock(spec=SessionLocal)
    mock_db.close = MagicMock()
    yield mock_db
    mock_db.close.assert_called_once()


def test_yield_db(mock_session):
    with patch("app.core.database.SessionLocal", return_value=mock_session):
        db_generator = yield_db()
        db = next(db_generator)

        assert db is mock_session

        db_generator.close()

        mock_session.close.assert_called_once()
