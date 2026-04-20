from bson import ObjectId
from app.models import individual_data, user_data, likes_get, all_users, all_likes


OID = ObjectId()


def _user():
    return {"_id": OID, "email": "a@b.com", "first_name": "A", "last_name": "B"}


def _like():
    return {
        "_id": OID, "uid": OID,
        "item_id1": "i1", "item_id2": "i2", "item_id3": "i3", "item_id4": "i4",
    }


def test_individual_data():
    r = individual_data(_user())
    assert r == {"id": str(OID), "email": "a@b.com", "first_name": "A", "last_name": "B"}


def test_user_data_with_img():
    r = user_data(_user(), True)
    assert r["img_status"] is True
    assert r["email"] == "a@b.com"


def test_user_data_without_img():
    r = user_data(_user(), False)
    assert r["img_status"] is False


def test_likes_get():
    r = likes_get(_like())
    assert r["item_id1"] == "i1"
    assert r["uid"] == str(OID)


def test_all_users():
    assert len(all_users([_user(), _user()])) == 2


def test_all_likes():
    assert len(all_likes([_like()])) == 1
