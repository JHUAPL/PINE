# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import pytest

import common
import pine.client.exceptions

def test_delete_document_not_allowed():
    client = common.login_with_test_user(common.client())

    collection_id = common.get_collection_id(client, "Trial Collection")
    assert collection_id != None
    
    with pytest.raises(pine.client.exceptions.PineClientHttpException):
        client.delete_document("nonexistent")

def test_add_and_delete_document():
    client = common.login_with_test_user(common.client())

    collection_id = common.get_collection_id(client, "Trial Collection")
    assert collection_id != None

    added_doc_id = client.add_document(collection_id=collection_id,
                                       text="This is a test document to be deleted.")
    assert added_doc_id != None
    
    annotation_id = client.annotate_document(added_doc_id, [], [])
    assert annotation_id != None
    
    delete_resp = client.delete_document(added_doc_id)
    assert delete_resp != None
    assert isinstance(delete_resp, dict)
    
    assert delete_resp["success"]
    
    changed_objs = delete_resp["changed_objs"]
    assert annotation_id in changed_objs["annotations"]["deleted"]
    assert added_doc_id in changed_objs["documents"]["deleted"]

def test_add_and_delete_documents():
    client = common.login_with_test_user(common.client())

    collection_id = common.get_collection_id(client, "Trial Collection")
    assert collection_id != None

    added_doc_id = client.add_document(collection_id=collection_id,
                                       text="This is a test document to be deleted.")
    assert added_doc_id != None
    
    added_doc_id_2 = client.add_document(collection_id=collection_id,
                                       text="This is a test document to be deleted.")
    assert added_doc_id_2 != None
    
    delete_resp = client.delete_documents([added_doc_id, added_doc_id_2])
    assert delete_resp != None
    assert isinstance(delete_resp, dict)
    
    assert delete_resp["success"]
    
    changed_objs = delete_resp["changed_objs"]
    assert len(changed_objs["annotations"]["deleted"]) == 0
    assert added_doc_id in changed_objs["documents"]["deleted"]
    assert added_doc_id_2 in changed_objs["documents"]["deleted"]
    