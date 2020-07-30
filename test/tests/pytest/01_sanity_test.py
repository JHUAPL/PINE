# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import common

def test_is_valid():
    client = common.client()
    assert client.is_valid() == True
