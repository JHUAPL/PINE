# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import logging
import math
import random
import typing

from .pipeline import DocumentPredictionProbabilities

logger = logging.getLogger(__name__)

def rank(document_ids: typing.List[str], results: typing.List[DocumentPredictionProbabilities], metric: str) -> typing.List[typing.Tuple[str, float]]:
    '''
    if metric == 'lc': return least_confidence(results)
    if metric == 'ma': return largest_margin(results)
    if metric == 'en': return entropy_rank(results)
    if metric == 'lcs': return least_confidence_squared(results)
    if metric == 'lce': return least_confidence_squared_by_entity(results)
    if metric == 'ra': return random_rank(results)
    if metric == 'mlp': return most_of_least_popular(results)
    return -1

    #Dictionary method is inefficient as it runs every method before returning one
    '''
    return {
        'lc':least_confidence(results),
        'ma':largest_margin(results),
        'en':entropy_rank(results),
        'lcs':least_confidence_squared(results),
        'lce':least_confidence_squared_by_entity(results),
        'ra':random_rank(results),
        'mlp':most_of_least_popular(results)
    }[metric]
    

def least_confidence(document_ids: typing.List[str], results: typing.List[DocumentPredictionProbabilities]) -> typing.List[typing.Tuple[str, float]]:
    logger.info('least confidence')
    #returns average confidence in each document, ranked from lowest to highest
    ranking = []
    for (doc_id, result) in zip(document_ids, results):
        confidence = 0
        numel = 0
        for ner in result.ner:
            (_, pred) = ner.get_highest_prediction() #sort from most to least confident
            confidence += pred
            numel += 1
        if numel > 0:
            confidence /= numel
        #print(confidence)
        ranking.append((doc_id, confidence))
    ranking.sort(key=lambda tup: tup[1])
    return ranking

def least_confidence_squared(document_ids: typing.List[str], results: typing.List[DocumentPredictionProbabilities]) -> typing.List[typing.Tuple[str, float]]:
    logger.info('least confidence squared')
    #returns average squared confidence in each document, ranked from lowest to highest (hopefully prioritizes consistently low confidence over spotty)
    ranking = []
    for (doc_id, result) in zip(document_ids, results):
        confidence = 0
        numel = 0
        for ner in result.ner:
            (_, pred) = ner.get_highest_prediction() #sort from most to least confident prediction
            confidence += math.pow(pred, 2)
            numel += 1
        if numel > 0:
            confidence /= numel
        #print(confidence)
        ranking.append((doc_id, confidence))
    ranking.sort(key=lambda tup: tup[1])
    return ranking

def least_confidence_squared_by_entity(document_ids: typing.List[str], results: typing.List[DocumentPredictionProbabilities]) -> typing.List[typing.Tuple[str, float]]:
    logger.info('least confidence square by entity')
    #returns average squared entity-confidence in each document (average confidence squared per entity), same idea as lcs but for individual entities
    ranking = []
    for (doc_id, result) in zip(document_ids, results):
        confidences = {}
        numels = {}
        for ner in result.ner:
            (pred_label, pred_prob) = ner.get_highest_prediction() #sort from most to least confident prediction
            if pred_label not in confidences:
                confidences[pred_label] = 0
                numels[pred_label] = 0
            confidences[pred_label] += pred_prob
            numels[pred_label] += 1
        confidence = 0
        for label in confidences:
            confidence += math.pow((confidences[label]/numels[label]), 2)
        if len(confidences) > 0:
            confidence /= len(confidences)
        #print(confidence)
        ranking.append((doc_id, confidence))
    ranking.sort(key=lambda tup: tup[1])
    return ranking

#WARNING: REQUIRES PROBABLITIES FOR ALL POSSIBLE LABELS PER TOKEN INSTEAD OF JUST MOST LIKELY
def largest_margin(document_ids: typing.List[str], results: typing.List[DocumentPredictionProbabilities]) -> typing.List[typing.Tuple[str, float]]:
    logger.info('largest margin')
    #returns average margin in each document, ranked from lowest to highest
    ranking = []
    for (doc_id, result) in zip(document_ids, results):
        margin = 0
        numel = 0
        for ner in result.ner:
            #if only most confident prediction is provided, cannot calculate margin
            if len(ner.predictions) > 1:
                sorted_predictions = ner.get_predictions_from_highest_to_lowest() #sort from most to least confident prediction
                margin += (sorted_predictions[0][1] - sorted_predictions[1][1])
                numel += 1
                
        if numel > 0:
            margin /= numel
        #print(margin)
        ranking.append((doc_id, margin))
    ranking.sort(key=lambda tup: tup[1])
    return ranking

#WARNING: REQUIRES PROBABLITIES FOR ALL POSSIBLE LABELS PER TOKEN INSTEAD OF JUST MOST LIKELY
def entropy_rank(document_ids: typing.List[str], results: typing.List[DocumentPredictionProbabilities], N=None) -> typing.List[typing.Tuple[str, float]]:
    logger.info('entropy rank')
    ranking = []
    for (doc_id, result) in zip(document_ids, results):
        entropy = 0
        numel = 0
        #TODO: check to ensure N is not larger than number of possible labels
        for ner in result.ner:
            #print(ent[2])
            #if only most confident prediction is provided, cannot calculate entropy
            if len(ner.predictions) > 1:
                sorted_predictions = ner.get_predictions_from_highest_to_lowest() #sort from most to least confident prediction
                for i in range(0, min(N, len(sorted_predictions)) if N is not None else len(sorted_predictions)):
                    #print(str(i))
                    prob = sorted_predictions[i][1]
                    entropy += (prob*math.log(prob))
                entropy *= -1
                numel += 1
        if numel > 0:
            entropy = entropy/numel
        #print(margin)
        ranking.append((doc_id, entropy))
    ranking.sort(key=lambda tup: tup[1], reverse=True)
    return ranking

def random_rank(document_ids: typing.List[str], results: typing.List[DocumentPredictionProbabilities]) -> typing.List[typing.Tuple[str, float]]:
    logger.info('random rank')
    ranks = list(range(0, len(results)))
    random.shuffle(ranks)
    ranking = []
    for (i, doc_id) in enumerate(document_ids):
        ner = results[ranks[i]].ner
        ranking.append((doc_id, ner.get_highest_prediction()[1]))

    return ranking

def most_of_least_popular(document_ids: typing.List[str], results: typing.List[DocumentPredictionProbabilities]) -> typing.List[typing.Tuple[str, float]]:
    logger.info('most of least popular')
    doc_stats = []
    ranking = []
    popularity = {}
    for (doc_id, result) in zip(document_ids, results):
        stats = {}
        for ner in result.ner:
            (predicted_label, _) = ner.get_highest_prediction()
            if predicted_label not in stats:
                stats[predicted_label] = 0
            stats[predicted_label] += 1

        doc_stats.append((doc_id, stats))
        for label in stats:
            if label not in popularity:
                popularity[label] = 0
            popularity[label] += stats[label]
    if 'O' in popularity:
        del popularity['O']
    #ignores labels with 0 predicted instances...
    #for every label, starting with least popular
    for l in sorted(popularity, key=popularity.__getitem__):
        label_rank = []
        for doc in doc_stats:
            if l not in doc[1]:
                doc[1][l] = 0
            label_rank.append((doc[0], doc[1][l]))
        #sort all documents by predicted instances of that label
        label_rank.sort(key=lambda tup: tup[1], reverse=True)

        #go through the ranking for individual label in order from most to least instances
        for lp in range(0, len(label_rank)):
            doc_label_stats = label_rank[lp] #(doc_id, label_instances)
            #append any documents with nonzero predicted instances in their respective order
            if doc_label_stats[1] > 0: 
                # TODO check what this is actually doing if we ever use this method
                ranking.append((doc_label_stats[0], [l, doc_label_stats[1]]))
                #remove ranked document from pool
                doc_stats = [d for d in doc_stats if d[0] != doc_label_stats[0]]
            else:
                break

    return ranking
