# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

"""
Functions for computing the difference between two sets of annotations.
"""
from collections import namedtuple, Counter

Annotation = namedtuple('Annotation', ['type', 'label', 'offsets'])


def exact_match_instance_evaluation(ann_list_1, ann_list2, tokens=None):
    exp = set(ann_list_1)
    pred = set(ann_list_2)
    tp = exp.intersection(pred)
    fp = pred.difference(exp)
    fn = exp.difference(pred)
    return tp, fp, fn

def exact_match_token_evaluation(ann_list_1, ann_list_2, tokens=None):
    """
    Annotations are split into token-sized bits before true positives, false positives and false negatives are computed.

    Sub-token annotations are expanded to full tokens. Long annotations will influence the results more than short
    annotations. Boundary errors for adjacent annotations with the same label are ignored!
    """
    exp = Counter(_read_token_annotations(ann_list_1, tokens))
    pred = Counter(_read_token_annotations(ann_list_2, tokens))
    tp = counter2list(exp & pred)
    fp = counter2list(pred - exp)
    fn = counter2list(exp - pred)
    return tp, fp, fn


def counter2list(c):
    for elem, cnt in c.items():
        for i in range(cnt):
            yield (elem)


def _read_token_annotations(ann_list, tokens):
    """
    Yields a new annotation for each token overlapping with an annotation. If annotations are overlapping each other,
    there will be multiple annotations for a single token.
    """
    for annotation in set(ann_list):
        for start, end in annotation.offsets:
            for ts, te in tokens.overlapping_tokens(start, end):
                yield Annotation(annotation.type, annotation.label, ((ts, te),))
