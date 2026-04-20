import io
import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId

UID = str(ObjectId())


def test_upload_image(client, mock_mongo):
    mock_mongo["user_imgdb"].insert_one.return_value = MagicMock()
    r = client.post(
        f"/{UID}/upload",
        files={"file": ("test.png", io.BytesIO(b"fakeimage"), "image/png")},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "Image uploaded successfully"


def test_upload_image_error(client, mock_mongo):
    mock_mongo["user_imgdb"].insert_one.side_effect = Exception("db error")
    r = client.post(
        f"/{UID}/upload",
        files={"file": ("test.png", io.BytesIO(b"fakeimage"), "image/png")},
    )
    assert r.status_code == 500


def test_delete_user_image(client, mock_mongo):
    mock_mongo["user_imgdb"].delete_one.return_value = MagicMock()
    r = client.delete(f"/{UID}/upload")
    assert r.status_code == 200
    assert r.json()["status"] == "Image delete successfully"


def test_delete_user_image_error(client, mock_mongo):
    mock_mongo["user_imgdb"].delete_one.side_effect = Exception("db error")
    r = client.delete(f"/{UID}/upload")
    assert r.status_code == 500


def test_img_return():
    fake_content = b"\x89PNG\r\n"
    with patch("app.routes.genRoute.requests.get") as mock_get:
        mock_get.return_value = MagicMock(content=fake_content)
        from app.routes.genRoute import img_return
        result = img_return([{"id": "abc", "url": "http://fake.url/img.png"}])
    assert len(result) == 1
    assert result[0][0] == "abc.png"
    assert result[0][2] == "image/png"


def _make_png_bytes():
    """Minimal valid 1x1 PNG."""
    import struct, zlib
    def chunk(name, data):
        c = struct.pack(">I", len(data)) + name + data
        return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\xff\xff")
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def test_generate_with_user_image(client, mock_mongo):
    from unittest.mock import MagicMock, patch
    import base64

    png = _make_png_bytes()
    b64_png = base64.b64encode(png).decode()

    mock_mongo["user_imgdb"].find_one.return_value = {"uid": UID, "base64": b64_png}
    mock_mongo["cdb"].list_collection_names.return_value = []

    fake_part = MagicMock()
    fake_part.inline_data.data = png
    fake_part.inline_data.mime_type = "image/png"
    fake_response = MagicMock()
    fake_response.candidates = [MagicMock(content=MagicMock(parts=[fake_part]))]

    with patch("app.routes.genRoute.client") as mock_client:
        mock_client.models.generate_content.return_value = fake_response
        r = client.post("/generate", json={"uid": UID})

    assert r.status_code == 200


def test_generate_no_user_image(client, mock_mongo):
    from unittest.mock import MagicMock, patch

    png = _make_png_bytes()
    mock_mongo["user_imgdb"].find_one.return_value = None
    mock_mongo["cdb"].list_collection_names.return_value = []

    fake_part = MagicMock()
    fake_part.inline_data.data = png
    fake_part.inline_data.mime_type = "image/png"
    fake_response = MagicMock()
    fake_response.candidates = [MagicMock(content=MagicMock(parts=[fake_part]))]

    with patch("app.routes.genRoute.client") as mock_client:
        mock_client.models.generate_content.return_value = fake_response
        r = client.post("/generate", json={"uid": UID})

    assert r.status_code == 200


def test_generate_no_image_returned(client, mock_mongo):
    from unittest.mock import MagicMock, patch

    mock_mongo["user_imgdb"].find_one.return_value = None
    mock_mongo["cdb"].list_collection_names.return_value = []

    fake_part = MagicMock()
    fake_part.inline_data = None
    fake_response = MagicMock()
    fake_response.candidates = [MagicMock(content=MagicMock(parts=[fake_part]))]

    with patch("app.routes.genRoute.client") as mock_client:
        mock_client.models.generate_content.return_value = fake_response
        r = client.post("/generate", json={"uid": UID})

    assert r.status_code == 500


def test_generate_retry_on_429(client, mock_mongo):
    from unittest.mock import MagicMock, patch

    png = _make_png_bytes()
    mock_mongo["user_imgdb"].find_one.return_value = None
    mock_mongo["cdb"].list_collection_names.return_value = []

    fake_part = MagicMock()
    fake_part.inline_data.data = png
    fake_part.inline_data.mime_type = "image/png"
    fake_response = MagicMock()
    fake_response.candidates = [MagicMock(content=MagicMock(parts=[fake_part]))]

    with patch("app.routes.genRoute.client") as mock_client, \
         patch("app.routes.genRoute.time.sleep"):
        mock_client.models.generate_content.side_effect = [
            Exception("429 retryDelay 5s"),
            fake_response,
        ]
        r = client.post("/generate", json={"uid": UID})

    assert r.status_code == 200
