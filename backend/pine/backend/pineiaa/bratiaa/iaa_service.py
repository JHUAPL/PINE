# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import requests
from ..bratiaa import iaa_report, compute_f1_agreement, input_generator
from ..bratiaa import tokenize
from ..bratiaa import exact_match_token_evaluation
from collections import defaultdict
from .. import service
import numpy as np

EVE_HEADERS = {'Content-Type': 'application/json'}

def get_items(resource):
    response = service.get(resource, headers=EVE_HEADERS)
    if response.status_code == 200:
        r = response.json()
        if '_items' in r:
            if '_links' in r and 'next' in r['_links']:
                return r['_items'], r['_links']['next']['href']
            else:
                return r['_items'], None
    return [], None


def get_all_items(query):
    total_items = []
    while True:
        items, query = get_items(query)
        total_items.extend(items)
        if query is None:
            break
    return total_items



def get_doc_annotations(collection_id, exclude=None):
    #get documents
    resource = 'documents?where={"collection_id":"%s"}' % (collection_id)
    docs = get_all_items(resource)

    #get annotations
    resource = 'annotations?where={"collection_id":"%s"}' % (collection_id)
    annotations = get_all_items(resource)

    combined = {}
    for d in docs:
        combined[d['_id']]={"_id":d['_id'], "text":d['text'], "annotations":{}}
        if "metadata" in d:
            combined[d['_id']]['metadata'] = d['metadata']

    for a in annotations:
        creator = a['creator_id']
        if exclude and creator in exclude :
            continue
        docid = a['document_id']
        anns = a['annotation']
        if docid in combined:
            combined[docid]["annotations"][creator]=anns
    return combined

def fix_num_for_json(number):
    if np.isnan(number):
        return "null"
    else:
        return number


def getIAAReportForCollection(collection_id):

    combined = get_doc_annotations(collection_id)

    labels = set()
    for v in combined.values():
        for ann_list in v['annotations'].values():
            for ann in ann_list:
                if len(ann) == 3:
                    labels.add(ann[2])


    anns = []

    for k, c in combined.items():
        anns.append(c)

    token_func = tokenize
    eval_func = exact_match_token_evaluation

    labels = list(labels)

    annotators, documents = input_generator(anns)

    try:
        f1_agreement = compute_f1_agreement(annotators, documents, labels, eval_func=eval_func, token_func=token_func)
        # Get label counts by provider
        counts = defaultdict(lambda: defaultdict(int))
        for document in anns:
            for per, ann_list in document['annotations'].items():
                for a in ann_list:
                    if len(a) == 3:
                        counts[per][a[2]] += 1

        # for label in labels:
        #     print(label)
        #     for person, label_counts in counts.items():
        #         if label in label_counts:
        #             print('\t', person, label_counts[label])

        docids = [d.doc_id for d in f1_agreement.documents]
        list_per_doc = []
        mean_sd_per_doc = f1_agreement.mean_sd_per_document()
        for index, docID in enumerate(docids):
            list_per_doc.append({"doc_id": docID, "avg": fix_num_for_json(mean_sd_per_doc[0][index]),
                                 "stddev": fix_num_for_json(mean_sd_per_doc[1][index])})

        list_per_label = []
        mean_sd_per_label = f1_agreement.mean_sd_per_label()
        for index, label in enumerate(f1_agreement.labels):
            list_per_label.append({"label": label, "avg": fix_num_for_json(mean_sd_per_label[0][index]),
                                   "stddev": fix_num_for_json(mean_sd_per_label[1][index])})


        labels_per_annotator_dict = {}
        for item in dict(counts).items():
            labels_per_annotator_dict[item[0]] = dict(item[1])

        # save iaa report
        new_iaa_report = {
            "collection_id": collection_id,
            "num_of_annotators": len(f1_agreement.annotators),
            "num_of_agreement_docs": len(f1_agreement.documents),
            "num_of_labels": len(f1_agreement.labels),
            "per_doc_agreement": list_per_doc,
            "per_label_agreement": list_per_label,
            "overall_agreement": {"mean": f1_agreement.mean_sd_total()[0], "sd": f1_agreement.mean_sd_total()[1],
                                  "heatmap_data": {"matrix": list(
                                      map(lambda x: list(x), list(f1_agreement.compute_total_f1_matrix()))),
                                                   "annotators": list(f1_agreement.annotators)}},
            "labels_per_annotator": labels_per_annotator_dict
        }

        return new_iaa_report
    except AssertionError:
        #There's no annotations from different annotators to calculate iaa for
        return None









