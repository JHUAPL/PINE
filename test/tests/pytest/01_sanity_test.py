# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import pytest

import common
import pine.client.exceptions

def test_is_valid():
    client = common.client()
    assert client.is_valid() == True

def test_login_and_logout():
    client = common.client()
    assert client.is_logged_in() == False
    
    # invalid login
    with pytest.raises(pine.client.exceptions.PineClientAuthException):
        client.login_eve("asdf", "asdf")
    assert client.is_logged_in() == False
    
    # valid login with ID
    user = common.test_user_data()[0]
    try:
        client.login_eve(user["_id"], user["password"])
        assert client.is_logged_in() == True
        assert client.get_my_user_id() == user["_id"]
        client_user = client.get_logged_in_user()
        assert client_user != None
        assert "display_name" in client_user
        assert "is_admin" in client_user
        assert "username" in client_user
        assert "id" in client_user
    finally:
        client.logout()
        assert client.is_logged_in() == False

    # valid login with email
    try:
        client.login_eve(user["email"], user["password"])
        assert client.is_logged_in() == True
        assert client.get_my_user_id() == user["_id"]
    finally:
        client.logout()
        assert client.is_logged_in() == False
