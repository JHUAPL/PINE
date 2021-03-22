# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import pytest

import common
import pine.client.exceptions

def test_list_collections():
    client = common.login_with_test_user(common.client())
    unarchived_collections = client.list_collections(False)
    assert type(unarchived_collections) is list
    assert len(unarchived_collections) > 0
    all_collections = client.list_collections(True)
    assert type(all_collections) is list
    assert len(all_collections) >= len(unarchived_collections)

    # make sure every collection has some expected properties
    for col in (all_collections + unarchived_collections):
        assert "_id" in col
        assert "annotators" in col
        assert "viewers" in col
        assert "configuration" in col
        assert "metadata" in col

    # make sure all_collections is superset of unarchived_collections
    for col in unarchived_collections:
        found = False
        for col2 in all_collections:
            if col["_id"] == col2["_id"]:
                found = True
                break
        assert found == True

    # make sure anything in all that's not in unarchived is archived
    for col in all_collections:
        found = False
        for col2 in unarchived_collections:
            if col["_id"] == col2["_id"]:
                found = True
                break
        assert col["archived"] == (not found)


def _get_collection_id(collection_title: str, client):
    for col in client.list_collections():
        if col["metadata"]["title"] == collection_title:
            return col["_id"]
    raise AssertionError("Couldn't find collection with title " + collection_title)

def test_download_collection_data():
    # find a collection that has annotations that the test user has access to
    user = "margaret"
    collection_title = "NER Test Collection"
    client = common.login_with_user(user, common.client())

    col_data = common.test_collection_data(collection_title)
    assert col_data != None
    collection_id = _get_collection_id(collection_title, client)
    assert collection_id != None

    # start with nothing but IDs
    kwargs = {
        "collection_id": collection_id,
        "include_collection_metadata": False,
        "include_document_metadata": False,
        "include_document_text": False,
        "include_annotations": False,
        "include_annotation_latest_version_only": True
    }
    data = client.download_collection_data(**kwargs)
    assert set(data.keys()) == {"_id", "documents"}
    assert len(data["documents"]) == col_data["documents"]["num_docs"]
    for doc in data["documents"]:
        assert set(doc.keys()) == {"_id"}
    doc_ids = [doc["_id"] for doc in data["documents"]]
    
    # turn on collection metadata
    kwargs["include_collection_metadata"] = True
    data = client.download_collection_data(**kwargs)
    assert set(data.keys()) == {"_id", "documents", "annotators", "viewers", "metadata",
                                "configuration", "labels", "archived", "creator_id"}
    assert len(data["documents"]) == len(doc_ids)
    for doc in data["documents"]:
        assert set(doc.keys()) == {"_id"}

    # turn on document metadata
    kwargs["include_document_metadata"] = True
    data = client.download_collection_data(**kwargs)
    assert len(data["documents"]) == len(doc_ids)
    for doc in data["documents"]:
        assert set(doc.keys()) == {"_id", "metadata", "has_annotated", "creator_id", "overlap"}

    # turn on document text
    kwargs["include_document_text"] = True
    data = client.download_collection_data(**kwargs)
    assert len(data["documents"]) == len(doc_ids)
    for doc in data["documents"]:
        assert set(doc.keys()) == {"_id", "metadata", "has_annotated", "creator_id", "overlap", "text"}

    # turn on annotations
    kwargs["include_annotations"] = True
    data = client.download_collection_data(**kwargs)
    assert len(data["documents"]) == len(doc_ids)
    for doc in data["documents"]:
        assert set(doc.keys()) == {"_id", "metadata", "has_annotated", "creator_id", "overlap", "text", "annotations"}
        annotations = doc["annotations"]
        assert type(annotations) is list and len(annotations) > 0
        for annotation in annotations:
            assert set(annotation.keys()) == {"_id", "creator_id", "annotation"}

    # turn on all annotation versions
    kwargs["include_annotation_latest_version_only"] = False
    data = client.download_collection_data(**kwargs)
    assert len(data["documents"]) == len(doc_ids)
    for doc in data["documents"]:
        annotations = doc["annotations"]
        assert type(annotations) is list and len(annotations) > 0
        for annotation in annotations:
            assert set(annotation.keys()) == {"_id", "creator_id", "annotation", "_version", "_latest_version"}


def test_download_collection_data_errors():
    # find a collection that has annotations that the test user does NOT have access to
    user = "ada"
    collection_title = "NER Test Collection"
    client = common.login_with_user(user, common.client())

    with pytest.raises(pine.client.exceptions.PineClientValueException):
        client.download_collection_data(None)

    collection_id = _get_collection_id(collection_title, client)
    assert collection_id != None
    with pytest.raises(pine.client.exceptions.PineClientHttpException) as excinfo:
        client.download_collection_data(collection_id)
    assert excinfo.value.status_code == 401


def test_collection_user_permissions():
    client = common.login_with_test_user(common.client())

    collection_id = _get_collection_id("NER Test Collection", client)
    assert collection_id != None
    permissions = client.get_collection_permissions(collection_id)
    assert permissions.to_dict() == {
        "view": True,
        "annotate": True,
        "add_documents": True,
        "add_images": True,
        "modify_users": False,
        "modify_labels": False,
        "modify_document_metadata": True,
        "download_data": False,
        "archive": False
    }

    collection_id = _get_collection_id("Trial Collection", client)
    assert collection_id != None
    permissions = client.get_collection_permissions(collection_id)
    assert permissions.to_dict() == {
        "view": True,
        "annotate": True,
        "add_documents": True,
        "add_images": True,
        "modify_users": True,
        "modify_labels": True,
        "modify_document_metadata": True,
        "download_data": True,
        "archive": True
    }
