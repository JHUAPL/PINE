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


def test_download_collection_data():
    # find a collection that has annotations that the test user has access to
    user = "margaret"
    collection_title = "NER Test Collection"
    client = common.login_with_user(user, common.client())

    col_data = common.test_collection_data(collection_title)
    assert col_data != None
    collection_id = common.get_collection_id(client, collection_title)
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

    collection_id = common.get_collection_id(client, collection_title)
    assert collection_id != None
    with pytest.raises(pine.client.exceptions.PineClientHttpException) as excinfo:
        client.download_collection_data(collection_id)
    assert excinfo.value.status_code == 401


def test_collection_user_permissions():
    client = common.login_with_test_user(common.client())

    collection_id = common.get_collection_id(client, "NER Test Collection")
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
        "archive": False,
        "delete_documents": False
    }

    collection_id = common.get_collection_id(client, "Trial Collection")
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
        "archive": True,
        "delete_documents": True
    }

def test_collection_creation_and_get_and_archive():
    client = common.login_with_test_user(common.client())
    pipeline_id = [p for p in client.get_pipelines() if p["name"].lower() == "spacy"][0]["_id"]
    assert pipeline_id is not None
    my_id = client.get_my_user_id()
    assert my_id is not None
    
    collection_builder = client.collection_builder() \
        .viewer(my_id) \
        .annotator(my_id) \
        .label("label") \
        .title("Collection to Test Creation") \
        .description("This is a collection for pytest to test creation.") \
        .classifier(pipeline_id, train_every=100)
    collection_id = client.create_collection(collection_builder)
    assert type(collection_id) is str
    
    try:
        collection = client.get_collection(collection_id)
        assert type(collection) is dict
        
        assert collection["_id"] == collection_id
        assert collection["creator_id"] == my_id
        assert collection["annotators"] == [my_id]
        assert collection["viewers"] == [my_id]
        assert collection["archived"] == False
        assert collection["labels"] == ["label"]
        assert collection["metadata"] == {
            "title": "Collection to Test Creation",
            "description": "This is a collection for pytest to test creation."
        }
        
        updated_collection = client.archive_collection(collection_id, True)
        assert type(updated_collection) is dict
        assert updated_collection["_id"] == collection_id
        assert updated_collection["archived"] == True
        
        updated_collection = client.archive_collection(collection_id, False)
        assert type(updated_collection) is dict
        assert updated_collection["_id"] == collection_id
        assert updated_collection["archived"] == False
    finally:
        client.archive_collection(collection_id, True)
