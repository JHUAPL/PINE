# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import csv

import pytest

import common
import pine.client.exceptions

def test_get_and_advance_next_documents(tmp_path):
    client = common.login_with_test_user(common.client())
    pipeline_id = [p for p in client.get_pipelines() if p["name"].lower() == "spacy"][0]["_id"]
    assert pipeline_id is not None
    my_id = client.get_my_user_id()
    assert my_id is not None

    # write documents CSV
    documents_file = tmp_path / "documents.csv"
    with open(documents_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for i in range(5):
            writer.writerow(["This is document number {}.".format(i)])

    collection = client.collection_builder() \
        .viewer(my_id) \
        .annotator(my_id) \
        .label("label") \
        .title("Collection to Test Next Document") \
        .description("This is a collection for pytest to test the next/advance documents feature.") \
        .classifier(pipeline_id, train_every=100, overlap=1) \
        .document_csv_file(documents_file, has_header=False, text_column=0)
    collection_id = client.create_collection(collection)
    assert collection_id is not None
    
    document_ids = [d["_id"] for d in client.get_collection_documents(collection_id, True, 1)]
    assert len(document_ids) == 5
    
    try:
        classifier = client.get_collection_classifier(collection_id)
        assert classifier is not None
        classifier_id = classifier["_id"]
        assert classifier_id is not None
        
        # add more documents
        document_ids += [
            client.add_document(
                collection_id=collection_id,
                overlap=1,
                text="This is document number {}.".format(i))
            for i in range(5, 10)]
        assert len(document_ids) == 10
        for document_id in document_ids:
            assert type(document_id) is str
        
        next_ids = []
        next_id = client.get_next_document(classifier_id)
        while next_id is not None:
            assert type(next_id) is str
            assert next_id not in next_ids # no duplicates
            next_ids.append(next_id)
            assert len(next_ids) <= len(document_ids) # sanity check to prevent an infinite loop
            updated_document = client.advance_next_document(classifier_id, next_id)
            assert type(updated_document) is dict
            next_id = client.get_next_document(classifier_id)
        assert set(document_ids) == set(next_ids)
    finally:
        client.archive_collection(collection_id)

def _check_pipeline_status(status, classifier_id):
    assert type(status) is dict
    assert "service_details" in status and type(status["service_details"]) is dict
    assert "job_id" in status
    assert type(status["job_id"]) is str and len(status["job_id"]) != 0
    assert "job_request" in status and type(status["job_request"]) is dict
    assert "job_response" in status and type(status["job_response"]) is dict

    request = status["job_request"]
    assert "job_data" in request and type(request["job_data"]) is dict

    response = status["job_response"]
    assert "classifier_id" in response and classifier_id == response["classifier_id"]
    assert "model_dir" in response
    assert "pipeline_name" in response
    assert "classifier_class" in response
    assert "classifier" in response and type(response["classifier"]) is dict
    assert (classifier_id != None) == ("has_trained" in response)

def test_get_pipelines():
    client = common.login_with_test_user(common.client())

    imported_pipelines = common.test_pipeline_data()
    expected_pipeline_ids = [pipeline["_id"] for pipeline in imported_pipelines]

    pipelines = client.get_pipelines()
    actual_pipeline_ids = [pipeline["_id"] for pipeline in pipelines]
    assert set(expected_pipeline_ids) == set(actual_pipeline_ids)

    for pipeline in pipelines:
        expected = [p for p in imported_pipelines if p["_id"] == pipeline["_id"]][0]
        for key in expected:
            assert expected[key] == pipeline[key]

def test_get_pipeline_status():
    client = common.login_with_test_user(common.client())

    for pipeline in common.test_pipeline_data():
        status = client.get_pipeline_status(pipeline["_id"])
        _check_pipeline_status(status, None)

def test_get_collection_classifier():
    client = common.login_with_test_user(common.client())

    # make sure that a correct classifier is returned for each collection
    for collection in client.list_collections():
        classifier = client.get_collection_classifier(collection["_id"])
        assert type(classifier) is dict
        assert classifier["collection_id"] == collection["_id"]
        assert classifier["pipeline_id"] is not None

def test_get_classifier_status():
    client = common.login_with_test_user(common.client())

    for collection in client.list_collections():
        classifier = client.get_collection_classifier(collection["_id"])
        status = client.get_classifier_status(classifier["_id"])
        _check_pipeline_status(status, classifier["_id"])

def _assert_job_response(job_response, should_have_response: bool) -> str:
    assert job_response is not None and isinstance(job_response, dict)
    assert "job_id" in job_response
    job_id = job_response["job_id"]
    assert job_id is not None and isinstance(job_id, str)
    assert "job_request" in job_response and job_response["job_request"] is not None
    assert isinstance(job_response["job_request"], dict)
    if should_have_response:
        assert "job_response" in job_response and job_response["job_response"] is not None
        assert isinstance(job_response["job_response"], dict)
    else:
        assert "job_response" not in job_response or prediction_job_data["job_response"] is None
    return job_id

def _test_train_and_predict(collection_title):
    client = common.login_with_test_user(common.client())
    
    collection = common.get_collection(client, collection_title)
    assert collection is not None
    collection_id = collection["_id"]
    assert collection_id is not None
    labels = collection["labels"]
    assert labels is not None and len(labels) > 0
    classifier_id = client.get_collection_classifier(collection_id)["_id"]
    assert classifier_id is not None
    first_document = client.get_collection_documents(collection_id, truncate=False)[0]
    document_id = first_document["_id"]
    document_text = first_document["text"]
    assert document_text.startswith("Thousands of demonstrators have ")
    
    # train async
    train_job_data = client.classifier_train(classifier_id, do_async=True)
    train_job_id = _assert_job_response(train_job_data, False)
    common.wait_for_job_to_finish(client, classifier_id, train_job_id, max_wait_seconds=120)
    status = client.get_classifier_status(classifier_id)
    _check_pipeline_status(status, classifier_id)
    assert status["job_response"]["has_trained"]
    train_job_results = client.get_classifier_job_results(classifier_id, train_job_id)
    assert train_job_results != None and isinstance(train_job_results, dict)
    
    # predict from ID sync
    prediction_job_data = client.classifier_predict(classifier_id, [document_id], [], do_async=False)
    prediction_job_id = _assert_job_response(prediction_job_data, True)
    docs_by_id = prediction_job_data["job_response"]["documents_by_id"]
    texts = prediction_job_data["job_response"]["texts"]
    assert docs_by_id.keys() == {document_id}
    prediction_from_id = docs_by_id[document_id]
    assert len(texts) == 0
    
    # predict from text async
    prediction_job_data = client.classifier_predict(classifier_id, [], [document_text], do_async=True)
    prediction_job_id = _assert_job_response(prediction_job_data, False)
    common.wait_for_job_to_finish(client, classifier_id, prediction_job_id, max_wait_seconds=120)
    prediction_job_data = client.get_classifier_job_results(classifier_id, prediction_job_id)
    assert prediction_job_data != None and isinstance(prediction_job_data, dict)
    docs_by_id = prediction_job_data["documents_by_id"]
    texts = prediction_job_data["texts"]
    assert len(docs_by_id) == 0
    assert len(texts) == 1
    prediction_from_text = texts[0]
    
    # should be the same
    assert prediction_from_id == prediction_from_text
    
    # make sure they're in the right format
    assert isinstance(prediction_from_id, dict)
    assert "doc" in prediction_from_id and "ner" in prediction_from_id
    assert isinstance(prediction_from_id["doc"], list)
    for pred in prediction_from_id["doc"]:
        assert isinstance(pred, str)
        assert pred in labels
    assert isinstance(prediction_from_id["ner"], list)
    for pred in prediction_from_id["ner"]:
        assert isinstance(pred, list) and isinstance(pred[0], int) and isinstance(pred[1], int) and isinstance(pred[2], str)
        assert pred[0] >= 0 and pred[1] > pred[0]
        assert pred[2] in labels
    
    return prediction_from_id

@pytest.mark.flaky(reruns=3)
def test_train_and_predict_spacy():
    prediction = _test_train_and_predict("Small Collection")
    assert len(prediction["doc"]) == 0
    preds = prediction["ner"]
    # unfortunately the spacy predictions are not the same across runs
    # but there are some that seem to consistently be there
    common_labels = {'gpe', 'org', 'geo', 'tim'}
    common_tokens = [[48, 54], [111, 118], [633, 640], [717, 724], [754, 760], [833, 837],
        [852, 858], [972, 976], [1025, 1029], [1200, 1209], [1221, 1225]]
    for [s, e] in common_tokens:
        found = False
        for pred in preds:
            if pred[0] == s and pred[1] == e:
                if pred[2] not in common_labels:
                    print(common_labels, pred)
                assert pred[2] in common_labels
                found = True
                break
        if not found:
            print([s, e], preds)
        assert found

def test_train_and_predict_opennlp():
    prediction = _test_train_and_predict("Small Collection OpenNLP")
    assert len(prediction["doc"]) == 0
    preds = prediction["ner"]
    assert preds == [[48, 54, 'geo'], [77, 81, 'geo'], [111, 118, 'gpe'], [255, 259, 'per'],
        [343, 353, 'geo'], [368, 377, 'geo'], [524, 531, 'geo'], [542, 553, 'org'],
        [570, 577, 'gpe'], [596, 604, 'geo'], [633, 640, 'gpe'], [665, 669, 'geo'],
        [717, 724, 'gpe'], [754, 760, 'geo'], [833, 837, 'geo'], [840, 845, 'geo'],
        [852, 858, 'geo'], [865, 899, 'org'], [934, 940, 'geo'], [941, 950, 'tim'],
        [972, 976, 'gpe'], [1025, 1029, 'gpe'], [1089, 1096, 'geo'], [1113, 1120, 'gpe'],
        [1200, 1209, 'tim'], [1221, 1225, 'org']]

def test_train_and_predict_simpletransformers():
    prediction = _test_train_and_predict("Small Collection Simpletransformers")
    assert len(prediction["doc"]) == 0
    preds = prediction["ner"]
    # unfortunately the simpletransformers predictions are not the same across runs
    # and there don't seem to be guaranteed common tokens
    # so just make sure any predictions have proper labels...
    common_labels = {'gpe', 'org', 'geo', 'tim', 'per'}
    for pred in preds:
        assert pred[2] in common_labels

def test_sync_train():  
    client = common.login_with_test_user(common.client())
    
    collection = common.get_collection(client, "Small Collection OpenNLP")
    assert collection is not None
    collection_id = collection["_id"]
    assert collection_id is not None
    classifier_id = client.get_collection_classifier(collection_id)["_id"]
    assert classifier_id is not None
    
    train_job_data = client.classifier_train(classifier_id, do_async=False)
    _assert_job_response(train_job_data, True)
    results = train_job_data["job_response"]
    assert results is not None and isinstance(results, dict)
    assert "average_metrics" in results and isinstance(results["average_metrics"], dict)
    assert "updated_objects" in results and isinstance(results["updated_objects"], dict)
    assert "fit" in results and isinstance(results["fit"], dict)
    assert "model_filename" in results and isinstance(results["model_filename"], str)
