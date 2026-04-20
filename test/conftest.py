import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_mongo(monkeypatch):
    """Patch MongoDB collections before any app module is imported."""
    userdb_mock = MagicMock()
    user_likedb_mock = MagicMock()
    user_imgdb_mock = MagicMock()
    cdb_mock = MagicMock()

    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")

    with patch("app.config.userdb", userdb_mock), \
         patch("app.config.user_likedb", user_likedb_mock), \
         patch("app.config.user_imgdb", user_imgdb_mock), \
         patch("app.config.cdb", cdb_mock), \
         patch("app.routes.userRoute.userdb", userdb_mock), \
         patch("app.routes.userRoute.user_likedb", user_likedb_mock), \
         patch("app.routes.userRoute.user_imgdb", user_imgdb_mock), \
         patch("app.routes.genRoute.userdb", userdb_mock), \
         patch("app.routes.genRoute.user_imgdb", user_imgdb_mock), \
         patch("app.routes.genRoute.cdb", cdb_mock), \
         patch("app.routes.genRoute.client", MagicMock()):
        yield {
            "userdb": userdb_mock,
            "user_likedb": user_likedb_mock,
            "user_imgdb": user_imgdb_mock,
            "cdb": cdb_mock,
        }


@pytest.fixture
def client(mock_mongo):
    from app.main import app
    return TestClient(app)
