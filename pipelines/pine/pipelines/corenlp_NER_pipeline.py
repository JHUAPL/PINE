#!/usr/bin/env python3
# coding: utf8
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import logging
import os
from os.path import abspath, isfile, isdir, join
import textwrap
import typing
import uuid

from overrides import overrides

from .pipeline import Pipeline, NerPrediction, DocumentPredictions, NerPredictionProbabilities, DocumentPredictionProbabilities, EvaluationMetrics, StatMetrics
from .shared.config import ConfigBuilder

config = ConfigBuilder.get_config()
logger = logging.getLogger(__name__)

#also imports pyjnius after configuring java environment variables
#NOTE: jvm will run out of memory if you train too many times while it is running, cause of leak unknown
#in the meantime if you must call fit a lot, destroy the object and create a new one to reset the jvm

class corenlp_NER(Pipeline):
    #Path variables
    __jar = ''
    __jdk_dir = ''

    #files output in the process of training model
    #id is so the output files are unique to each instantiation, otherwise weird things will happen if we decide to use query-by-committee
    #TODO: maybe don't use id if it isn't specified?
    __train_file = ''
    __test_file = '' #TODO: only really needed for evaluate_orig, maybe remove?
    __model = ''
    __temp_dir = None

    #model variables
    __crf = None
    __props = None

    #class variables
    __is_setup = False
    __id = None
    __default_fit_params = None

    @classmethod
    def setup(cls, java_dir=None, ner_path=None):
        if cls.__is_setup:
            logger.info("Java is already set up.")
            return
        
        logger.info("Setting up Java.")
        #TODO: set defaults for the following.
        #Point to location of JAVA installation
        if java_dir != None:
            cls.__jdk_dir = java_dir
        else:
            cls.__jdk_dir = '/usr/lib/jvm/java-1.8.0-openjdk-amd64' # self.__jdk_dir = '/usr/lib/jvm/java-8-oracle'
        if isdir(cls.__jdk_dir):
            os.environ['JAVA_HOME'] = cls.__jdk_dir
        else:
            raise ImportError("ERROR: JAVA installation not found")
        
        #Point to Location of Stanford NER Library
        if ner_path != None:
            cls.__jar = ner_path
        else:
            cls.__jar = './resources/stanford-corenlp-full-2018-02-27/stanford-corenlp-3.9.1.jar'
        if isfile(cls.__jar):
            os.environ['CLASSPATH'] = cls.__jar
        else:
            cls.__jar = 'pine/pipelines/resources/stanford-corenlp-full-2018-02-27/stanford-corenlp-3.9.1.jar'
            if isfile(cls.__jar):
                os.environ['CLASSPATH'] = cls.__jar
            else:
                raise ImportError("ERROR: Stanford NER Library not found")
        
        #if you get to this point, java and stanford ner library should be located
        import jnius_config
        if not jnius_config.vm_running:
            logger.info('Configured JVM')
            jnius_config.add_options('-Xmx32g') #allocate enough memory to the JVM heap to run the classifier
        else:
            raise RuntimeWarning('WARNING: JVM already running. Cannot run core nlp')

        #import pyjnius to import required classes from JAVA/Stanford NER
        from jnius import autoclass

        #General
        cls.__java_String = autoclass("java.lang.String")

        #TOKENIZING
        cls.__java_StringReader = autoclass("java.io.StringReader")
        cls.__java_Tokenizer = autoclass("edu.stanford.nlp.process.PTBTokenizer")

        #TRAINING AND TESTING CRFCLASSIFIER
        cls.__java_CRFClassifier = autoclass("edu.stanford.nlp.ie.crf.CRFClassifier")
        cls.__java_Properties = autoclass("java.util.Properties")
        cls.__java_AA = autoclass("edu.stanford.nlp.ling.CoreAnnotations$AnswerAnnotation")

        #GETTING CONFIDENCES
        cls.__java_CRFCliqueTree = autoclass("edu.stanford.nlp.ie.crf.CRFCliqueTree")
        
        cls.__SCNLP = autoclass("edu.stanford.nlp.pipeline.StanfordCoreNLP")
        cls.__default_fit_params = {
            'import_prop_file': None,
            'export_prop_file': None,
            'max_left': 1,
            'use_class_feature': True,
            'use_word': True,
            'use_ngrams': True,
            'no_mid_ngrams': True,
            'max_ngram_length': 6,
            'use_prev': True,
            'use_next': True,
            'use_disjunctive': True,
            'use_sequences': True,
            'use_prev_sequences': True,
            'use_type_seqs': True,
            'use_type_seqs2': True,
            'use_type_y_sequences': True,
            'word_shape': "chris2useLC"
        }
        
        cls.__is_setup = True

    #init()
    #set tunable parameters
    #TODO: Should probably make this more robust by inserting try/catch
    def __init__(self, java_dir=None, ner_path=None, load_model=None, tmp_dir=None):
        corenlp_NER.setup(java_dir=java_dir, ner_path=ner_path)
        
        self.__id = uuid.uuid4()

        if tmp_dir != None:
            self.__temp_dir = tmp_dir
            #can choose to dictate where the model will store files so that it doesn't overwrite any,
            #otherwise it will write to a new directory within the resources folder
        else:
            self.__temp_dir = config.ROOT_DIR + '/tmp/' + str(self.__id)

        if not isdir(self.__temp_dir):
            os.makedirs(self.__temp_dir)
        logger.info("Using temp dir {}".format(self.__temp_dir))

        self.__train_file = join(self.__temp_dir, 'corenlp_training.tsv')
        self.__test_file = join(self.__temp_dir, 'corenlp_test_gold.tsv')
        self.__model = join(self.__temp_dir, 'corenlp-ner-model.ser.gz')

        if load_model != None:
            self.__crf = self.__java_CRFClassifier.getClassifier(self.__java_String(load_model))
            self.__model = load_model

    @overrides
    def status(self) -> dict:
        return {
            "temp_dir": abspath(self.__temp_dir),
            "jdk_dir": abspath(self.__jdk_dir),
            "jar": abspath(self.__jar),
            "default_fit_params": self.__default_fit_params
        }

    @overrides
    def fit(self, X: typing.Iterable[str], y, all_labels: typing.Iterable[str], **params) -> dict:
        default_params = self.__default_fit_params.copy()
        #format input data into tsv file for ner to train on
        try:
            train_data = self.format_data(X, y)
            if len(train_data) == 0 or train_data is None:
                raise Exception("ERROR: could not format input correctly")
        except:
            raise Exception("ERROR: could not format input correctly")

        with open(self.__train_file, 'w') as f:
            for doc in train_data:
                for ent in doc:
                    f.write(ent[0] + '\t' + ent[1]  + '\n')
                f.write('\n')
        if params is not None:
            for key in default_params.keys():
                if key in params:
                    default_params[key] = params[key]
        #if user wants to use their own properties load it, otherwise we make our own
        if default_params["import_prop_file"] != None and isfile(default_params["import_prop_file"]):
            with open(default_params["import_prop_file"], 'r') as f:
                prop_text = f.read()
        else:
            prop_text = textwrap.dedent(
    """# location of the training file
trainFile = """+ self.__train_file + """
# location where you would like to save (serialize) your
# classifier; adding .gz at the end automatically gzips the file,
# making it smaller, and faster to load
serializeTo = """ + self.__model + """

# structure of your training file; this tells the classifier that
# the word is in column 0 and the correct answer is in column 1
map = word=0,answer=1

# This specifies the order of the CRF: order 1 means that features
# apply at most to a class pair of previous class and current class
# or current class and next class.
maxLeft=""" + str(default_params["max_left"]) + """

# these are the features we'd like to train with
useClassFeature=""" + str(default_params["use_class_feature"]) + """
useWord=""" + str(default_params["use_word"]) + """
useNGrams=""" + str(default_params["use_ngrams"]) + """
noMidNGrams=""" + str(default_params["no_mid_ngrams"]) + """
maxNGramLeng=""" + str(default_params["max_ngram_length"]) + """
usePrev=""" + str(default_params["use_prev"]) + """
useNext=""" + str(default_params["use_next"]) + """
useDisjunctive=""" + str(default_params["use_disjunctive"]) + """
useSequences=""" + str(default_params["use_sequences"]) + """
usePrevSequences=""" + str(default_params["use_prev_sequences"]) + """
# the last 4 properties deal with word shape features
useTypeSeqs=""" + str(default_params["use_type_seqs"]) + """
useTypeSeqs2=""" + str(default_params["use_type_seqs2"]) + """
useTypeySequences=""" + str(default_params["use_type_y_sequences"]) + """
wordShape=""" + default_params["word_shape"] + """
""")
        #user can choose to export the properties file they used if they wish
        if default_params["export_prop_file"] != None:
            with open(default_params["export_prop_file"], 'w') as f:
                f.write(prop_text)

        #load properties into the model and train
        p = self.__java_StringReader(self.__java_String(prop_text))
        self.__props = self.__java_Properties()
        self.__props.load(p)

        if self.__crf != None:
            self.__SCNLP.clearAnnotatorPool()
            del self.__crf #may clear up some memory, unclear how much of an effect it has

        self.__crf = self.__java_CRFClassifier(self.__props)

        self.__crf.train()

        #TODO: make this user optional? or just have them call save_model?
        modelPath = self.__props.getProperty(self.__java_String("serializeTo"))
        self.__crf.serializeClassifier(self.__java_String(modelPath))
        os.remove(self.__train_file)

        return {}

    @overrides
    def predict(self, X: typing.Iterable[str]) -> typing.List[DocumentPredictions]:
        out = []
        for doc in X:
            ner_preds = []
            test_text = self.__java_String(doc)
            results = self.__crf.classify(test_text)

            for s in range(results.size()):
                for w in range(results.get(s).size()):
                    word = results.get(s).get(w)
                    start_char = word.beginPosition()
                    end_char = word.endPosition()
                    label = word.get(self.__java_AA)
                    #print(str(start_char) + '-' + str(end_char) + ': ' + word.word() + '/' + label)
                    if label != 'O':
                        ner_preds.append(NerPrediction(start_char, end_char, label))
            out.append(DocumentPredictions(ner_preds, []))
        return out

    @overrides
    def predict_proba(self, X: typing.Iterable[str], get_all_labels=False, include_other=False, **kwargs) -> typing.List[DocumentPredictionProbabilities]:
        out = []
        # Score is confidence of classifier for this prediction
        for doc in X:
            ner_probs = []
            test_text = self.__java_String(doc)
            results = self.__crf.classify(test_text)

            for s in range(results.size()):
                cliqueTree = self.__crf.getCliqueTree(results.get(s))
                for w in range(cliqueTree.length()):
                    word = results.get(s).get(w)
                    start_char = word.beginPosition()
                    end_char = word.endPosition()
                    label = word.get(self.__java_AA)
                    #to capture data for tokens marked 'O' set include_other to True, else these will not be included in the calculations
                    if (include_other == True) or (label != 'O' and include_other == False):
                        if get_all_labels == False:
                            index = self.__crf.classIndex.indexOf(self.__java_String(label))
                            prob = cliqueTree.prob(w, index)
                            #print(str(start_char) + '-' + str(end_char) + ': ' + word.word() + '/' + label)
                            ner_probs.append(NerPredictionProbabilities(start_char, end_char, [(label, prob)]))
                        else:
                            itr = self.__crf.classIndex.iterator()
                            all_probs = []
                            while itr.hasNext():
                                label = itr.next()
                                index = self.__crf.classIndex.indexOf(self.__java_String(label))
                                prob = cliqueTree.prob(w, index)
                                all_probs.append((label, prob))
                            ner_probs.append(NerPredictionProbabilities(start_char, end_char, all_probs))

            out.append(DocumentPredictions(ner_probs, []))
        return out


    @overrides
    #TODO
    def next_example(self, X: typing.Iterable[str], Xid):
        return

## EXTRA METHODS TO HELP WITH THE corenlp PIPELINE ##
    def get_id(self):
        return self.__id

    #Takes input data and formats it to be easier to use in the corenlp pipeline
    #ASSUMES DATA FOLLOWS FORMAT X = [string], y = [[(start offset, stop offset, label), ()], ... []]
    #Currently cannot assign more than one label to the same word
    def format_data(self, X: typing.Iterable[str], y):
        out = []
        for doc,ann in zip(X,y):
            #Extract labeled entities from doc
            doc_ents = []
            cursor = 0
            #puts labeled entities in order within each document for next part
            ann.sort(key=lambda tup: tup[0])
            for ent in ann:
                label = ent[2]
                start_char = ent[0]
                end_char = ent[1]
                ent_text = doc[start_char:end_char]
                #if there is text before the token, insert it
                if cursor < start_char:
                    doc_ents.append((doc[cursor:start_char], 'O'))
                #this is to prevent tokens from being added more than once (TODO: may want to experiment with other ways of handling multiple labels)
                if cursor <= start_char:
                    doc_ents.append((ent_text, label))
                if cursor <= end_char:
                    cursor = end_char
            if doc[cursor:] != '': #don't want to add a blank accidentally
                doc_ents.append((doc[cursor:], 'O'))
            #print(doc_ents)

            ent_extract = []
            for text, l in doc_ents:
                words = self.tokenize(str(text))
                #print(words)
                #there were several cases where there would be no words (only spaces),
                #the if mitigates that error
                if words:
                    for w in words:
                        ent_extract.append((w,l))
            out.append(ent_extract)
        return out

    @overrides
    #models must be saved with extension ".ser.gz"
    def save_model(self, model_name: str):
        if not model_name.endswith(".ser.gz"):
            logger.warn('WARNING: model_name must end in .ser.gz, adding...')
            model_name = model_name + ".ser.gz"
        self.__crf.serializeClassifier(self.__java_String(model_name))
        logger.info('Saved model to ' + model_name)
        return model_name


    @overrides
    #properties can be exported/imported during train
    def load_model(self, model_name: str):
        #TODO: what to do if model doesn't exist?
        if not model_name.endswith(".ser.gz"):
            logger.warn('WARNING: model_name must end in .ser.gz, adding...')
            model_name = model_name + ".ser.gz"
        self.__crf = self.__java_CRFClassifier.getClassifier(self.__java_String(model_name))
        self.__model = model_name

    #method for tokenizing text
    #TODO: currently this implementation of corenlp doesn't support more than one label per token
    def tokenize(self, input_text):
        #print(input_text)
        text = self.__java_String(input_text)

        r = self.__java_StringReader(text)
        t = self.__java_Tokenizer.newPTBTokenizer(r)

        tokens = []

        while t.hasNext():
            w = t.next()
            tokens.append(w.word())

        return tokens

    #Calculates Precision, Recall, and F1 Score for model based on input test data
    #WARNING: currently works for BioNLP data, no guarantees with other datasets
    # WARNING: this is currently broken, but this whole pipeline is broken
    @overrides
    def evaluate(self, X: typing.Iterable[str], y, all_labels: typing.Iterable[str], verbose=False, **kwargs) -> EvaluationMetrics:
        try:
            train_data = self.format_data(X, y)
            if len(train_data) == 0 or train_data is None:
                raise Exception("ERROR: could not format input correctly")
        except:
            raise Exception("ERROR: could not format input correctly")
        
        known_labels = set()
        for anns in y:
            for ann in anns:
                known_labels.add(ann[2])
        
        metrics = EvaluationMetrics()
        test_text = ''
        for doc in X:
            test_text = test_text + doc + '\n\n'
        
        #rest of code tries to recreate calculations as this line, which can't be called more than once for some reason
        #results = self.__crf.classifyAndWriteAnswers(self.__java_String(self.__test_file), True)
        #print(test_text)
        results = self.__crf.classify(self.__java_String(test_text))

        #Calculate evaluation by iterating through answer key and matching tokens to classifier output
        s = 0
        w = 0
        prev_gold = ''
        prev_guess = ''
        next_guess = None

        for d, doc in enumerate(train_data):
            for i, answer in enumerate(doc):
                #Find corresponding token in gold and predicted
                word = answer[0]
                gold = answer[1]
                if verbose: logger.trace('GOLD: ' + word + ',' + gold)

                if word == '<xn>':
                    if verbose: logger.trace('SKIP')
                    continue

                if next_guess != None:
                    guess = next_guess
                else:
                    guess = (results.get(s).get(w).word(), results.get(s).get(w).get(self.__java_AA))

                a = 1
                votes = {guess[1]: 1}
                next_guess = None
                #if the tokens don't match, loop until they do
                while word != guess[0]:

                    if len(word) > len(guess[0]) and word[0:len(guess[0])] == guess[0]: #if the classifier has tokenized more finely than the answer, then keep adding the next tokens to the guessed token until it matches
                        #since tokens sometime have to be concatenated, we use a voting system,
                        #where the most popular label of all of the individual tokens is used
                        to_add = (results.get(s).get(w+a).word(), results.get(s).get(w+a).get(self.__java_AA))
                        if to_add[1] not in votes:
                            votes[to_add[1]] = 1
                        votes[to_add[1]] += 1
                        #use the most popular label based on the individual tokens
                        guess = (guess[0] + to_add[0], sorted(votes, key=votes.__getitem__, reverse=True)[0])
                        a = a + 1
                    elif len(word) < len(guess[0]) and word == guess[0][0:len(word)]: #if the guessed token is larger than the answer, break the rest off into the next guess
                        next_guess = (guess[0][len(word):], guess[1])
                        guess = (guess[0][0:len(word)], guess[1])
                    else: #if the guess token does not match any part of the answer token, then move on to the next token without adding
                        w = w + 1
                        if w >= results.get(s).size():
                            w = 0
                            s = s + 1
                        if s >= results.size():
                            break
                        guess = (results.get(s).get(w).word(), results.get(s).get(w).get(self.__java_AA))
                        next_guess = None
                        a = 1
                        votes = {guess[1]: 1} #reset votes when concatenation is discarded
                    if verbose: logger.trace(guess)

                    #check what the next gold token is, if it matches with the current guess then just move on
                    #(likely the current answer token doesn't exactly match the guess token, see `` vs '')
                    if i+1 < len(doc):
                        next_gold = doc[i+1]
                    elif i >= len(doc) and d+1 < len(test_data): # this is broken
                        next_gold = test_data[d+1][0]
                    else:
                        next_gold = (None, None)
                    if guess[0] == next_gold[0]: break
                if word != guess[0]: continue

                #if the code gets to here we are pretty confident the tokens match
                if verbose: logger.trace('GUESS: ' + str(guess))

                pred = guess[1]

                known_labels.add(pred)

                # Per token metrics
                for label in known_labels:
                    if label not in metrics.labels:
                        metrics.labels[label] = StatMetrics()


                if gold == pred and gold != 'O':
                    metrics.labels[gold].tp += 1
                    for label in known_labels:
                        if label != gold:
                            metrics.labels[label].tn += 1
                elif gold == 'O' and pred != 'O':
                    metrics.labels[pred].fp += 1
                    for label in known_labels:
                        if label != pred:
                            metrics.labels[label].tn += 1
                elif pred == 'O' and gold != 'O':
                    metrics.labels[gold].fn += 1
                    for label in known_labels:
                        if label != gold:
                            metrics.labels[label].tn += 1
                else:
                    for label in known_labels:
                        metrics.labels[label].tn += 1


                # Per annotation metrics
                # if gold not in stats:
                #     stats[gold] = [0, 0, 0]
                # if pred not in stats:
                #     stats[pred] = [0, 0, 0]
                # if gold == pred:
                #     #TRUE POSITIVE
                #     #Stanford NLP considers adjacent tokens with the same (non 'O') label to be one instance of that label
                #     if gold != prev_gold or gold == 'O':
                #         stats[gold][0] = stats[gold][0] + 1
                #         if gold != 'O': stats['Totals'][0] = stats['Totals'][0] + votes[gold]
                #     if verbose: print('TRUE POSITIVE')
                # else:
                #     #GOLD ADDS FALSE NEGATIVE
                #     if gold != prev_gold or gold == 'O':
                #         stats[gold][2] = stats[gold][2] + 1
                #         if gold != 'O': stats['Totals'][2] = stats['Totals'][2] + 1
                #     if verbose: print('FALSE NEGATIVE FOR ' + gold)
                #     #pred ADDS FALSE POSITIVE
                #     if pred != prev_guess or pred == 'O':
                #         stats[pred][1] = stats[pred][1] + 1
                #         if pred != 'O': stats['Totals'][1] = stats['Totals'][1] + (votes[pred] if pred in votes else 1)
                #     if verbose: print('FALSE POSITIVE FOR ' + pred)
                #
                # #if tokens had to be concatenated and they were not all the same label
                # if len(votes) > 1:
                #     for label in sorted(votes, key=votes.__getitem__, reverse=True)[1:]:
                #         if label not in stats:
                #             stats[label] = [0, 0, 0]
                #         stats[label][1] += votes[label] #add false positives to all the labels other than the most popular one as well
                #         if verbose: print('FALSE POSITIVE FOR ' + label)
                #
                # prev_gold = gold
                # prev_guess = pred

        #removes stats for 'O' as we don't really care about that;
        #ONLY USED FOR PER ANNOTATION METRICS
        # del stats['O']

        for key in metrics.labels:
            metrics.totals.tp += metrics.labels[key].tp
            metrics.totals.fp += metrics.labels[key].fp
            metrics.total.fn += metrics.labels[key].fn
            metrics.total.tn += metrics.labels[key].tn



        #print(test_data[-1])
        metrics.calc_precision_recall_f1_acc()

        return metrics

            #Calculates Precision, Recall, and F1 Score for model based on input test data
    #TODO: prints a whole lot to the command line, find a way to suppress?
    def evaluate_orig(self, X: typing.Iterable[str], y, Xid):
        try:
            test_data = self.format_data(X, y)
            if len(test_data) == 0 or test_data is None:
                raise Exception("ERROR: could not format input correctly")
        except:
            raise Exception("ERROR: could not format input correctly")

        with open(self.__test_file, 'w') as f:
            for d in test_data:
                for e in d:
                    f.write(e[0] + '\t' + e[1]  + '\n')
                f.write('\n')
        results = self.__crf.classifyAndWriteAnswers(self.__java_String(self.__test_file), True)
        return results


