import pytest
import bcrypt
from bson import ObjectId
from unittest.mock import MagicMock

OID = str(ObjectId())
SALT = bcrypt.gensalt()
HASHED_PW = bcrypt.hashpw(b"password123", SALT)


def _db_user(oid=None):
    _id = ObjectId(oid) if oid else ObjectId()
    return {"_id": _id, "email": "test@test.com", "first_name": "T", "last_name": "U", "password": HASHED_PW}


# ── POST /users ───────────────────────────────────────────────────────────────

def test_create_user(client, mock_mongo):
    mock_mongo["userdb"].find_one.return_value = None
    inserted = MagicMock()
    inserted.inserted_id = ObjectId()
    mock_mongo["userdb"].insert_one.return_value = inserted
    mock_mongo["userdb"].find_one.side_effect = [None, _db_user(str(inserted.inserted_id))]
    r = client.post("/users", json={
        "email": "new@test.com", "password": "password123",
        "first_name": "N", "last_name": "U"
    })
    assert r.status_code == 200


def test_create_user_duplicate_email(client, mock_mongo):
    mock_mongo["userdb"].find_one.return_value = _db_user()
    r = client.post("/users", json={
        "email": "test@test.com", "password": "password123",
        "first_name": "N", "last_name": "U"
    })
    assert r.status_code in (400, 500)


# ── GET /users/{user_id} ──────────────────────────────────────────────────────

def test_get_user_found_with_img(client, mock_mongo):
    u = _db_user()
    mock_mongo["userdb"].find_one.return_value = u
    mock_mongo["user_imgdb"].find_one.return_value = {"uid": str(u["_id"]), "base64": "abc"}
    r = client.get(f"/users/{str(u['_id'])}")
    assert r.status_code == 200
    assert r.json()["img_status"] is True


def test_get_user_found_no_img(client, mock_mongo):
    u = _db_user()
    mock_mongo["userdb"].find_one.return_value = u
    mock_mongo["user_imgdb"].find_one.return_value = None
    r = client.get(f"/users/{str(u['_id'])}")
    assert r.status_code == 200
    assert r.json()["img_status"] is False


def test_get_user_not_found(client, mock_mongo):
    mock_mongo["userdb"].find_one.return_value = None
    r = client.get(f"/users/{OID}")
    assert r.status_code == 404


# ── PUT /users/{user_id} ──────────────────────────────────────────────────────

def test_update_user(client, mock_mongo):
    u = _db_user()
    mock_mongo["userdb"].find_one.return_value = u
    mock_mongo["userdb"].find_one_and_update.return_value = {**u, "first_name": "Updated"}
    r = client.put(f"/users/{str(u['_id'])}", json={"first_name": "Updated"})
    assert r.status_code == 200


def test_update_user_not_found(client, mock_mongo):
    mock_mongo["userdb"].find_one.return_value = None
    r = client.put(f"/users/{OID}", json={"first_name": "X"})
    assert r.status_code == 404


# ── POST /login ───────────────────────────────────────────────────────────────

def test_login_success(client, mock_mongo):
    mock_mongo["userdb"].find_one.return_value = _db_user()
    r = client.post("/login", json={"email": "test@test.com", "password": "password123"})
    assert r.status_code == 200


def test_login_wrong_password(client, mock_mongo):
    mock_mongo["userdb"].find_one.return_value = _db_user()
    r = client.post("/login", json={"email": "test@test.com", "password": "wrongpassword"})
    assert r.status_code == 401


def test_login_user_not_found(client, mock_mongo):
    mock_mongo["userdb"].find_one.return_value = None
    r = client.post("/login", json={"email": "no@no.com", "password": "password123"})
    assert r.status_code == 404


# ── DELETE /delete/{user_id} ──────────────────────────────────────────────────

def test_delete_user(client, mock_mongo):
    u = _db_user()
    mock_mongo["userdb"].find_one.return_value = u
    mock_mongo["user_likedb"].find.return_value = []
    r = client.delete(f"/delete/{str(u['_id'])}")
    assert r.status_code == 200


def test_delete_user_not_found(client, mock_mongo):
    mock_mongo["userdb"].find_one.return_value = None
    r = client.delete(f"/delete/{OID}")
    assert r.status_code in (404, 500)


# ── POST /likes ───────────────────────────────────────────────────────────────

def test_create_like(client, mock_mongo):
    inserted = MagicMock()
    inserted.inserted_id = ObjectId()
    mock_mongo["user_likedb"].insert_one.return_value = inserted
    r = client.post("/likes", json={"uid": OID, "item_id1": "abc"})
    assert r.status_code == 200


# ── GET /likes/{uid} ──────────────────────────────────────────────────────────

def test_get_likes(client, mock_mongo):
    oid = ObjectId()
    mock_mongo["user_likedb"].find.return_value = [{
        "_id": oid, "uid": OID,
        "item_id1": "a", "item_id2": None, "item_id3": None, "item_id4": None
    }]
    r = client.get(f"/likes/{OID}")
    assert r.status_code == 200
    assert len(r.json()) == 1


# ── DELETE /likes/{lid} ───────────────────────────────────────────────────────

def test_delete_like(client, mock_mongo):
    lid = ObjectId()
    mock_mongo["user_likedb"].find_one.return_value = {"_id": lid}
    r = client.delete(f"/likes/{str(lid)}")
    assert r.status_code == 200


def test_delete_like_not_found(client, mock_mongo):
    mock_mongo["user_likedb"].find_one.return_value = None
    r = client.delete(f"/likes/{OID}")
    assert r.status_code in (404, 500)
