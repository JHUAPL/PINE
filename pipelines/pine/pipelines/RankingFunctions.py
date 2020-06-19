# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import math, random

def rank(results, metric):
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
	

def least_confidence(results):
	print('least confidence')
	#returns average confidence in each document, ranked from lowest to highest
	ranking = []
	for key in results:
		confidence = 0
		numel = 0
		for ent in results[key]:
			if type(ent[2]) is list:
				ent[2].sort(key=lambda tup: tup[1], reverse=True) #sort from most to least confident
				confidence += ent[2][0][1]
			else:
				confidence += ent[3]
			numel += 1
		if numel > 0:
			confidence /= numel
		#print(confidence)
		ranking.append((key, confidence))
	ranking.sort(key=lambda tup: tup[1])
	return ranking

def least_confidence_squared(results):
	print('least confidence squared')
	#returns average squared confidence in each document, ranked from lowest to highest (hopefully prioritizes consistently low confidence over spotty)
	ranking = []
	for key in results:
		confidence = 0
		numel = 0
		for ent in results[key]:
			if type(ent[2]) is list:
				ent[2].sort(key=lambda tup: tup[1], reverse=True) #sort from most to least confident prediction
				confidence += math.pow(ent[2][0][1], 2)
			else:
				confidence += math.pow(ent[3], 2)
			numel += 1
		if numel > 0:
			confidence /= numel
		#print(confidence)
		ranking.append((key, confidence))
	ranking.sort(key=lambda tup: tup[1])
	rank_res = [ranks[0] for ranks in ranking]
	return rank_res

def least_confidence_squared_by_entity(results):
	print('least confidence square by entity')
	#returns average squared entity-confidence in each document (average confidence squared per entity), same idea as lcs but for individual entities
	ranking = []
	for key in results:
		confidences = {}
		numels = {}
		for ent in results[key]:
			if type(ent[2]) is list:
				ent[2].sort(key=lambda tup: tup[1], reverse=True) #sort from most to least confident prediction
				pred_label = ent[2][0][0]
				pred_prob = ent[2][0][1]
			else:
				pred_label = ent[2]
				pred_prob = ent[3]
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
		ranking.append((key, confidence))
	ranking.sort(key=lambda tup: tup[1])
	return ranking

#WARNING: REQUIRES PROBABLITIES FOR ALL POSSIBLE LABELS PER TOKEN INSTEAD OF JUST MOST LIKELY
def largest_margin(results):
	print('largest margin')
	#returns average margin in each document, ranked from lowest to highest
	ranking = []
	for key in results:
		margin = 0
		numel = 0
		for ent in results[key]:
			#if only most confident prediction is provided, cannot calculate margin
			if type(ent[2]) is list:
				ent[2].sort(key=lambda tup: tup[1], reverse=True) #sort from most to least confident prediction
				margin += (ent[2][0][1] - ent[2][1][1])
				numel += 1
				
		if numel > 0:
			margin /= numel
		#print(margin)
		ranking.append((key, margin))
	ranking.sort(key=lambda tup: tup[1])
	return ranking

#WARNING: REQUIRES PROBABLITIES FOR ALL POSSIBLE LABELS PER TOKEN INSTEAD OF JUST MOST LIKELY
def entropy_rank(results, N=None):
	print('entropy rank')
	ranking = []
	for key in results:
		entropy = 0
		numel = 0
		#TODO: check to ensure N is not larger than number of possible labels
		for ent in results[key]:
			#print(ent[2])
			#if only most confident prediction is provided, cannot calculate entropy
			if type(ent[2]) is list:
				ent[2].sort(key=lambda tup: tup[1], reverse=True) #sort from most to least confident prediction
				for i in range(0, N if N is not None else len(ent[2])):
					#print(str(i))
					prob = ent[2][i][1]
					entropy += (prob*math.log(prob))
				entropy *= -1
				numel += 1
		if numel > 0:
			entropy = entropy/numel
		#print(margin)
		ranking.append((key, entropy))
	ranking.sort(key=lambda tup: tup[1], reverse=True)
	return ranking

def random_rank(results):
	print('random rank')
	ranks = list(range(0, len(results)))
	random.shuffle(ranks)
	ranking = []
	for i,key in enumerate(results):
		ranking.append((key, ranks[i]))

	ranking.sort(key=lambda tup: tup[1])
	return ranking

def most_of_least_popular(results):
	print('most of least popular')
	doc_stats = []
	ranking = []
	popularity = {}
	for key in results:
		stats = {}
		for ent in results[key]:
			if type(ent[2]) is list:
				ent[2].sort(key=lambda tup: tup[1], reverse=True) #sort from most to least confident prediction
				predicted_label = ent[2][0][0]
			else:
				predicted_label = ent[2]
			if predicted_label not in stats:
				stats[predicted_label] = 0
			stats[predicted_label] += 1

		doc_stats.append((key, stats))
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
				ranking.append((doc_label_stats[0], [l, doc_label_stats[1]]))
				#remove ranked document from pool
				doc_stats = [d for d in doc_stats if d[0] != doc_label_stats[0]]
			else:
				break

	return ranking