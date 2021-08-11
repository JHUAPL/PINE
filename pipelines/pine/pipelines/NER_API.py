# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import logging
import os
import typing
import uuid

import numpy as np
import pydash

from skmultilearn.model_selection import IterativeStratification
from sklearn.preprocessing import MultiLabelBinarizer
from itertools import chain

from .EveClient import EveClient
from . import RankingFunctions as rank
from .pmap_ner import NER
from .shared.config import ConfigBuilder

logger = logging.getLogger(__name__)
config = ConfigBuilder.get_config()


class ner_api(object):

    def __init__(self):
        self.model_dir = config.MODELS_DIR
        logger.info("Saving models to {}".format(self.model_dir))
        self.eve_client = EveClient()

    def status(self, classifier_id: str, pipeline_name: str) -> dict:
        classifier = NER(pipeline_name)
        status = {
            "pipeline_name": pipeline_name,
            "classifier_id": classifier_id,
            "model_dir": self.model_dir,
            "eve_entry_point": self.eve_client.entry_point,
            "classifier_class": classifier.pipeline_class,
            "classifier": classifier.status()
        }
        if classifier_id:
            classifier_obj, pipeline_obj, metrics_obj = self.get_classifier_pipeline_metrics_objs(classifier_id)
            status["has_trained"] = "filename" in classifier_obj
        return status

    def perform_fold(self, model: NER, train_data, test_data, **pipeline_parameters):
        model.fit(train_data[0], train_data[1], **pipeline_parameters)
        results = model.evaluate(test_data[0], test_data[1], range(0, len(test_data[0])))

        return results

    def perform_five_fold(self, model: NER, documents, annotations, doc_ids, **pipeline_parameters):
        metrics = list()
        # store list of documents ids per fold
        folds = list()
        # turning into numpy arrays to be able to access values with index array
        documents_np_array = np.array(documents)
        annotations_np_array = np.array(annotations, dtype=object)
        doc_ids_np_array = np.array(doc_ids)
        ann_list = list()

        for ann in annotations_np_array:
            ann_list = ann_list + list([x[2] for x in ann])
        # getting unique label names in annotations
        unique_ann_list = list(set(ann_list))

        # array to store multilabel values
        multilabel_array = []
        for ann in annotations_np_array:
            multilabel_array.append([unique_ann_list.index(x[2]) for x in ann])

        multilabel_binarizer = MultiLabelBinarizer().fit_transform(multilabel_array)

        skf = IterativeStratification(n_splits=5, order=1)

        total_metrics = {}

        for train_index, test_index in skf.split(documents_np_array, multilabel_binarizer):
            # get annotations train and test datasets
            train_annotations = annotations_np_array[train_index]
            test_annotations = annotations_np_array[test_index]

            # get documents train and test datasets
            train_documents = documents_np_array[train_index]
            test_documents = documents_np_array[test_index]

            fold_metrics = self.perform_fold(model, [train_documents.tolist(), train_annotations.tolist()],
                                             [test_documents.tolist(), test_annotations.tolist()], **pipeline_parameters)

            # saving docs used to train fold
            fold_doc_ids = doc_ids_np_array[train_index]
            folds.append(fold_doc_ids.tolist())

            # saving fold metrics
            metrics.append(fold_metrics)


            for key in fold_metrics.keys():
                if key not in total_metrics:
                    total_metrics[key] = {"FN": 0, "FP": 0, "TP": 0, "TN": 0, "f1": 0, "precision": 0, "recall": 0, "acc": 0}
                total_metrics[key]["FN"] = total_metrics[key]["FN"] + fold_metrics[key]["FN"]
                total_metrics[key]["FP"] = total_metrics[key]["FP"] + fold_metrics[key]["FP"]
                total_metrics[key]["TP"] = total_metrics[key]["TP"] + fold_metrics[key]["TP"]
                total_metrics[key]["TN"] = total_metrics[key]["TN"] + fold_metrics[key]["TN"]


        average_metrics = {}
        for label in total_metrics.keys():
            avg_metric = {}
            avg_metric["FN"]  = total_metrics[label]["FN"] / 5
            avg_metric["FP"]  = total_metrics[label]["FP"] / 5
            avg_metric["TP"]  = total_metrics[label]["TP"] / 5
            avg_metric["TN"]  = total_metrics[label]["TN"] / 5
            if (avg_metric["TP"] + avg_metric["FN"]) != 0:
                avg_metric["recall"] = avg_metric["TP"] / (avg_metric["TP"] + avg_metric["FN"])
            else:
                avg_metric["recall"] = 1.0
            if (avg_metric["TP"] + avg_metric["FP"]) != 0:
                avg_metric["precision"]  = avg_metric["TP"] / (avg_metric["TP"] + avg_metric["FP"])
            else:
                avg_metric["precision"]  = 0.0
            if (avg_metric["precision"]  + avg_metric["recall"]) != 0:
                avg_metric["f1"] = 2 * (avg_metric["precision"] * avg_metric["recall"]) / (avg_metric["precision"] + avg_metric["recall"])
            else:
                avg_metric["f1"] = 0
            avg_metric["acc"] = (avg_metric["TP"] + avg_metric["TN"]) / (avg_metric["TP"] + avg_metric["TN"] + avg_metric["FP"] + avg_metric["FN"])

            average_metrics[label] = avg_metric


        return metrics, folds, average_metrics

    def get_document_ranking(self, model: NER, doc_map: typing.Dict[str, str], doc_ids: typing.List[str]) -> typing.List[str]:
        """Calculates document rankings and returns document IDs sorted by ranking.
        
        The ranking should be which documents should be evaluated first.  This probably
        corresponds in some ways to the documents which the model is least confident about.
        
        :param model: NER model
        :param doc_map: dict: mapping of document IDs to document text where overlap is 0
        :param doc_ids: list: IDs of documents where ???
        
        :returns: sorted document IDs
        :rtype: list
        """
        # re rank documents
        documents_no_anns = []
        ids_no_anns = list(set(doc_map.keys()).difference(set(doc_ids)))
        for doc_id in ids_no_anns:
            documents_no_anns.append(doc_map[doc_id])

        # classifier.load_model(os.path.join(self.model_dir, filename))
        # ranks = classifier.next_example(documents_no_anns, ids_no_anns)
        results = model.predict_proba(documents_no_anns)
        ranks = rank.least_confidence_squared(ids_no_anns, results)
        return [r[0] for r in ranks]

    def get_classifier_pipeline_metrics_objs(self, classifier_id):
        classifier_obj = self.eve_client.get_obj('classifiers', classifier_id)
        if classifier_obj is None:
            raise Exception("No classifier_id {} was found".format(classifier_id))

        pipeline_obj = self.eve_client.get_obj("pipelines", str(classifier_obj["pipeline_id"]))
        if pipeline_obj is None:
            raise Exception("No pipeline associated with classifier_id {}".format(classifier_id))

        # Todo: fix indexing issue so it fails gracefully
        metrics_query = 'metrics?where={"classifier_id":"%s"}' % classifier_id
        metrics_obj = self.eve_client.get_items(metrics_query)[0][0]
        if metrics_obj is None:
            raise Exception("No metrics found for classifier_id {}".format(classifier_id))

        return classifier_obj, pipeline_obj, metrics_obj

    def train_model(self, custom_filename, classifier_id, pipeline_name):
        logger.info("train_model called with custom_filename='{}' classifier_id='{}' pipeline_name='{}'".format(
            custom_filename, classifier_id, pipeline_name))

        # get classifier object
        classifier_obj, pipeline_obj, metrics_obj = self.get_classifier_pipeline_metrics_objs(classifier_id)
        collection_id = pydash.get(classifier_obj, 'collection_id', None)
        pipeline_parameters = pydash.get(classifier_obj, 'parameters', None)
        logger.info("train_model collection_id='{}' pipeline_parameters='{}'".format(
            collection_id, pipeline_parameters))

        #get pipeline name
        # pipeline_name = pipeline_obj["name"]

        # get documents where overlap is 0
        doc_map = self.eve_client.get_documents(collection_id)
        # get documents with its annotations where overlap is 0
        documents, labels, doc_ids, ann_ids = self.eve_client.get_docs_with_annotations(collection_id, doc_map)

        # instantiate model
        classifier = NER(pipeline_name)

        # get folds information
        metrics, folds, averages = self.perform_five_fold(classifier, documents, labels, doc_ids, **pipeline_parameters)

        logger.info("Starting to train classifier for {} pipeline".format(pipeline_name))
        fit_results = classifier.fit(documents, labels, **pipeline_parameters)
        results = {
            "fit": fit_results,
            "average_metrics": averages,
            "updated_objects": {}
        }

        logger.info("Trained classifier for {} pipeline".format(pipeline_name))

        # save classifier
        logger.info("Saving classifier model for {} pipeline".format(pipeline_name))
        filename = custom_filename + "_" + str(uuid.uuid4())
        results["model_filename"] = filename
        model_filename = classifier.save_model(os.path.join(self.model_dir, pipeline_name, filename))
        # update classifier on eve
        if not self.eve_client.update('classifiers', classifier_id, classifier_obj['_etag'], {'filename': model_filename}):
            raise Exception("Unable to update classifier for {}".format(filename))
        logger.info("Saved classifier for {}".format(filename))
        results["updated_objects"]["classifiers"] = [classifier_id]

        # update classifier metrics on eve
        metrics_updated_obj = {
            'trained_classifier_db_version': classifier_obj['_version']+1,
            'documents': list(set(chain.from_iterable(folds))),
            'annotations': list(ann_ids),
            'folds': list(folds),
            'metrics': list(metrics),
            'metric_averages': dict(averages),
            'filename': filename
        }
        if not self.eve_client.update('metrics', metrics_obj["_id"], metrics_obj['_etag'], metrics_updated_obj):
            raise Exception("Unable to update metrics for {}".format(filename))
        logger.info("Saved classifier metrics for {}".format(filename))
        results["updated_objects"]["metrics"] = [metrics_obj["_id"]]

        # re rank documents
        ranks = self.get_document_ranking(classifier, doc_map, doc_ids)
        logger.info("Performing document rankings")

        # Save updates to eve
        query = 'next_instances?where={"classifier_id":"%s"}' % classifier_id
        next_instance_obj = self.eve_client.get_items(query)[0]
        etag = next_instance_obj[0]['_etag']
        next_instance_id = next_instance_obj[0]['_id']
        if not self.eve_client.update('next_instances', next_instance_id, etag, {'document_ids': ranks}):
            raise Exception("Unable to update next_instances for {}".format(filename))
        logger.info("Updated next instances entry for {}".format(filename))
        results["updated_objects"]["next_instances"] = [next_instance_id]
        
        return results

    def predict(self, classifier_id: str, pipeline_name: str, document_ids: typing.List[str], texts: typing.List[str]):
        classifier_obj, pipeline_obj, metrics_obj = self.get_classifier_pipeline_metrics_objs(classifier_id)

        if classifier_obj is None:
            raise Exception("No classifier obj")
        if 'filename' not in classifier_obj:
            raise Exception('No filename in classifier obj')

        if document_ids == None:
            document_ids = []
        if texts == None:
            texts = []

        # pipeline_name=pipeline_obj["name"]
        
        # load documents
        doc_map = self.eve_client.get_documents_by_id(document_ids)
        documents = []
        for document_id in document_ids:
            if document_id not in doc_map:
                raise Exception("Unable to find document with ID {}".format(document_id))
            documents.append(doc_map[document_id])

        filename = os.path.join(self.model_dir, pipeline_name, classifier_obj['filename'])

        if not os.path.exists(filename):
            raise FileNotFoundError("No model with {} filename has been created".format(filename))
        classifier = NER(pipeline_name)
        classifier.load_model(filename)
        logger.info("Loaded classifier {}".format(classifier))

        predicted_documents = classifier.predict(documents)
        predicted_documents_by_id = {}
        for i, doc_id in enumerate(document_ids):
            predicted_documents_by_id[doc_id] = predicted_documents[i].serialize()
        predicted_texts = [p.serialize() for p in classifier.predict(texts)]
        return {
            "documents_by_id": predicted_documents_by_id,
            "texts": predicted_texts
        }
        return classifier.predict(documents, document_ids)
