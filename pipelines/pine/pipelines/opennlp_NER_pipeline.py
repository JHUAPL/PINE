#!/usr/bin/env python3
# coding: utf8
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import logging
import os
from os.path import isfile, isdir, exists, join
import pydash
import uuid
import sys
import traceback

from .pipeline import Pipeline
from .shared.config import ConfigBuilder

config = ConfigBuilder.get_config()
logger = logging.getLogger(__name__)

#also imports pyjnius after configuring java environment variables

class opennlp_NER(Pipeline):
    #Path variables
    __jar = '' 
    __jdk_dir = ''
    __temp_dir = None
    __train_file = ''
    __test_file = '' #TODO: only really needed for evaluate_orig, maybe remove?

    #Model variables
    __model = None
    __nameFinder = None

    #Class variables
    __id = None


    #init()
    #set tunable parameters
    #TODO: Should probably make this more robust by inserting try/catch
    def __init__(self, java_dir=None, ner_path=None, tmp_dir=None):

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

        self.__train_file = join(self.__temp_dir, 'opennlp_ner.train')
        self.__test_file = join(self.__temp_dir, 'opennlp_ner.test')

        #TODO: set defaults for the following
        #TODO: Point to location of JAVA installation
        if java_dir != None:
            self.__jdk_dir = java_dir
        else:
            self.__jdk_dir = '/usr/lib/jvm/java-1.8.0-openjdk-amd64'
        if isdir(self.__jdk_dir):
            os.environ['JAVA_HOME'] = self.__jdk_dir
        else:
            raise ImportError("ERROR: JAVA installation not found")

        #Point to Location of OpenNLP Library Directory
        if ner_path != None:
            self.__ner_path = ner_path
        else:
            #self.__jar = 'resources/apache-opennlp-1.9.0/lib/'
            self.__ner_path= 'resources/apache-opennlp-1.9.0'
        if exists(self.__ner_path):
            os.environ['CLASSPATH'] = os.path.join(self.__ner_path, 'lib', '*')
        else:
            raise ImportError("ERROR: OpenNLP Library not found")


        #if you get to this point, java and opennlp library should be located
        import jnius_config
        if not jnius_config.vm_running:
            logger.info('Configured JVM')
            jnius_config.add_options('-Xmx8g') #allocate enough memory to the JVM heap to run the classifier
        else:
            raise RuntimeWarning('WARNING: JVM already running. Cannot run open nlp')

        #import pyjnius to import required classes from JAVA/opennlp
        from jnius import autoclass

        #General
        self.__java_String = autoclass("java.lang.String")
        self.__java_File = autoclass("java.io.File")

        #TOKENIZING
        self.__java_SentenceModel = autoclass("opennlp.tools.sentdetect.SentenceModel")
        self.__java_SentenceDetectorME = autoclass("opennlp.tools.sentdetect.SentenceDetectorME")
        self.__java_TokenizerModel = autoclass("opennlp.tools.tokenize.TokenizerModel")
        self.__java_TokenizerME = autoclass("opennlp.tools.tokenize.TokenizerME")

        #self.__sentenceDetector = self.__java_SentenceDetectorME(self.__java_SentenceModel(self.__java_File(self.__java_String("pipelines/resources/apache-opennlp-1.9.0/en-sent.bin"))))
        #self.__tokenizer = self.__java_TokenizerME(self.__java_TokenizerModel(self.__java_File(self.__java_String("pipelines/resources/apache-opennlp-1.9.0/en-token.bin"))))
        self.__sentenceDetector = self.__java_SentenceDetectorME(self.__java_SentenceModel(self.__java_File(self.__java_String(os.path.join(self.__ner_path, 'en-sent.bin')))))
        self.__tokenizer = self.__java_TokenizerME(self.__java_TokenizerModel(self.__java_File(self.__java_String(os.path.join(self.__ner_path, 'en-token.bin')))))

        #TRAINING
        self.__java_PlainTextByLineStream = autoclass("opennlp.tools.util.PlainTextByLineStream")
        self.__java_NameSampleDataStream = autoclass("opennlp.tools.namefind.NameSampleDataStream")
        self.__java_NameFinderME = autoclass("opennlp.tools.namefind.NameFinderME")
        self.__java_TrainingParameters = autoclass("opennlp.tools.util.TrainingParameters")
        self.__java_TokenNameFinderFactory = autoclass("opennlp.tools.namefind.TokenNameFinderFactory")
        self.__java_MarkableFileInputStreamFactory = autoclass("opennlp.tools.util.MarkableFileInputStreamFactory")

        #SAVING/LOADING MODEL
        self.__java_TokenNameFinderModel = autoclass("opennlp.tools.namefind.TokenNameFinderModel")

        #EVALUATION
        self.__java_TokenNameFinderEvaluator = autoclass("opennlp.tools.namefind.TokenNameFinderEvaluator")

        #MISC
        self.__java_WindowFeatureGenerator = autoclass("opennlp.tools.util.featuregen.WindowFeatureGenerator")
        self.__java_AdditionalContextFeatureGenerator = autoclass("opennlp.tools.util.featuregen.AdditionalContextFeatureGenerator")
        self.__java_Array = autoclass("java.lang.reflect.Array")

    #fit(X, y)
    #internal state is changed
    def fit(self, X, y, params):
        try:
            data = self.format_data(X, y)
            if len(data)==0 or data is None:
                raise Exception("ERROR: could not format input correctly")
        except:
            raise Exception("ERROR: could not format input correctly")
        #print(data)
        with open(self.__train_file, 'w') as f:
            f.write(data)
        inputStreamFactory = self.__java_MarkableFileInputStreamFactory(self.__java_File(self.__java_String(self.__train_file)))
        lineStream = self.__java_PlainTextByLineStream(inputStreamFactory, self.__java_String("utf-8"))
        sampleStream = self.__java_NameSampleDataStream(lineStream)
        nameFinderFactory = self.__java_TokenNameFinderFactory()


        if not params or params is None:
            trainParams = self.__java_TrainingParameters.defaultParams()
        else:
            paramTypes = {"algorithm": self.__java_TrainingParameters.ALGORITHM_PARAM,
                        "cutoff": self.__java_TrainingParameters.CUTOFF_PARAM,
                        "iterations": self.__java_TrainingParameters.ITERATIONS_PARAM,
                        "threads": self.__java_TrainingParameters.THREADS_PARAM,
                        "trainerType": self.__java_TrainingParameters.TRAINER_TYPE_PARAM }

            trainParams = self.__java_TrainingParameters()
            keyInParams = False
            for key in paramTypes.keys():
                if key in params:
                    keyInParams = True
                    trainParams.put(self.__java_String(paramTypes[key]), self.__java_String(str(params[key])))

            if not keyInParams:
                trainParams = self.__java_TrainingParameters.defaultParams()
        # The following call produces all of the loglikelihood output
        self.__model = self.__java_NameFinderME.train(self.__java_String("en"), None, sampleStream, trainParams, nameFinderFactory)
        self.__nameFinder = self.__java_NameFinderME(self.__model)
        os.remove(self.__train_file)

    #predict(X, Xid)
    #returns {text_id: [[offset_start, offset_end, label], ... []], ...}
    def predict(self, X, Xid):
        out = {}
        #self.find_all_init()
        for doc, doc_id in zip(X, Xid):
            doc_ents = []
            sentences = self.__sentenceDetector.sentPosDetect(self.__java_String(str(doc).encode('utf-8')))
            for s in sentences:
                s_start = s.getStart()
                s_end = s.getEnd()
                sent = self.__java_String(str(doc[s_start:s_end]).encode('utf-8'))
                tokens = self.__tokenizer.tokenizePos(sent)
                tok_string = []
                doc_tokens = []
                for t in tokens:

                    t_start = t.getStart() + s_start
                    t_end = t.getEnd() + s_start

                    doc_tokens.append((t_start, t_end))
                    tok_string.append(self.__java_String(str(doc[t_start:t_end]).encode('utf-8')))
                ents = self.__nameFinder.find(tok_string)
                # ents = self.find_all(tok_string)
                for e in ents:
                    start_token = tokens[e.getStart()]
                    end_token = tokens[e.getEnd() - 1]
                    doc_ents.append((start_token.getStart() + s_start, end_token.getEnd() + s_start, e.getType()))
                # sequenceFinder = self.__model.getNameFinderSequenceModel()
                # print(str(len(ents)) + ',' + str(len(tok_string)) + str(sequenceFinder.getOutcomes()))
            #print(doc_id)
            #print(doc_ents)
            out[doc_id] = (doc_ents, doc_tokens)
            self.__nameFinder.clearAdaptiveData()
        return out

    # predict_proba(X, Xid)
    # returns {text_id: [(offset_start, offset_end, label, score), ... (), ...}
    # TODO: figure out how to retrieve confidences for all labels instead of just most confident
    # Right now get_all_labels and include_other do nothing
    def predict_proba(self, X, Xid, get_all_labels=False, include_other=False):
        out = {}
        for doc, doc_id in zip(X, Xid):
            doc_ents = []
            sentences = self.__sentenceDetector.sentPosDetect(self.__java_String(str(doc).encode('utf-8')))
            for s in sentences:
                s_start = s.getStart()
                s_end = s.getEnd()
                sent = self.__java_String(str(doc[s_start:s_end]).encode('utf-8'))
                tokens = self.__tokenizer.tokenizePos(sent)
                tok_string = []
                for t in tokens:
                    t_start = t.getStart() + s_start
                    t_end = t.getEnd() + s_start
                    tok_string.append(self.__java_String(str(doc[t_start:t_end]).encode('utf-8')))
                ents = self.__nameFinder.find(tok_string)
                for e in ents:
                    start_token = tokens[e.getStart()]
                    end_token = tokens[e.getEnd() - 1]
                    doc_ents.append((start_token.getStart() + s_start, end_token.getEnd() + s_start, e.getType(), e.getProb()))
            out[doc_id] = doc_ents
            self.__nameFinder.clearAdaptiveData()
        return out

    # TODO: next_example(X, Xid)
    # Given model's current state evaluate the input (id, String) pairs and return a rank ordering of lowest->highest scores for instances (will need to discuss specifics of ranking)
    # Discussing rank is now a major project - see notes
    def next_example(self, X, Xid):
        return

# EXTRA METHODS TO HELP WITH THE opennlp PIPELINE ##

    # Save a model to be used again later
    # models must be saved and loaded with extension ".bin"
    def save_model(self, model_name):
        if not model_name.endswith(".bin"):
            logger.warning('WARNING: model_name must end with .bin, adding...')
            model_name = model_name + ".bin"
        path = self.__java_File(self.__java_String(model_name)).toPath()
        self.__model.serialize(path)
        return model_name



    #loads a model from file
    def load_model(self, model_name):
        if not model_name.endswith(".bin"):
            logger.warning('WARNING: model_name must end with .bin, adding...')
            model_name = model_name + ".bin"
        #TODO: what to do if model doesn't exist?
        path = self.__java_File(self.__java_String(model_name)).toPath()
        self.__model = self.__java_TokenNameFinderModel(path)
        self.__nameFinder = self.__java_NameFinderME(self.__model)
        return True

    #call once before calling find_all, must call every time you fit to a new dataset
    def find_all_init(self):
        factory = self.__model.getFactory()
        self.__seqCodec = factory.createSequenceCodec()
        self.__sequenceValidator = self.__seqCodec.createSequenceValidator()
        self.__sequenceFinder = self.__model.getNameFinderSequenceModel()
        self.__contextGenerator = factory.createContextGenerator()
        acfg = self.__java_AdditionalContextFeatureGenerator()
        self.__contextGenerator.addFeatureGenerator(self.__java_WindowFeatureGenerator(acfg, 8, 8))
        return

    #currently nonfunctional
    def find_all(self,tokens):
        #attempts to recreate the behavior of the find function in NameFinderME.java
        logger.info(type(tokens[0]))
        logger.info(type(self.__contextGenerator))
        logger.info(type(self.__sequenceValidator))
        toks = self.__java_Array.newInstance(self.__java_String, len(tokens))
        logger.info(type(toks))
        for t, tok in enumerate(tokens):
            toks[t] = tok
            logger.info(type(toks))
        empty_context = self.__java_Array.newInstance(self.__java_String, 0)
        bestSequence = self.__sequenceFinder.bestSequences(5, toks, empty_context, self.__contextGenerator, self.__sequenceValidator)

        c = bestSequence.getOutcomes()

        self.__contextGenerator.updateAdaptiveData(tokens, c.toArray([None]*c.size()))
        spans = self.__seqCodec(c)
        return spans

    def get_id(self):
        return self.__id

    #Takes input data and formats it to be easier to use in the opennlp pipeline
    #ASSUMES DATA FOLLOWS FORMAT X = [string], y = [[(start offset, stop offset, label), ()], ... []]
    #Currently cannot assign more than one label to the same word
    def format_data(self, X, y):
        out = ''
        try:
            for doc, ann in zip(X, y):
                #puts labeled entities in order within each document for next part
                ann.sort(key=lambda tup: tup[0])
                sentences = self.__sentenceDetector.sentPosDetect(self.__java_String(str(doc).encode('utf-8')))
                in_ann = False
                a = 0
                doc_done = False
                for s in sentences:
                    try:
                        tokens = self.__tokenizer.tokenizePos(self.__java_String(doc[s.getStart():s.getEnd()]))
                    except:
                        raise Exception("Error tokenizing document string")
                    for tok in tokens:
                        start = s.getStart() + tok.getStart()
                        end = s.getStart() + tok.getEnd()
                        if ann:
                            cur_ann = ann[a]

                        try:
                            #TODO: should it just be == and be exact or <= for some leniency?
                            if cur_ann[0] <= start and not in_ann and not doc_done:
                                out += '<START:' + cur_ann[2] + '> '
                                in_ann = True

                            out += doc[start:end] + ' '
                        except:
                            exec_type, value, tb = sys.exc_info()
                            print(traceback.format_tb(tb))
                            print(value)

                        try:
                            if cur_ann[1] <= end and not doc_done:
                                if in_ann:
                                    out += '<END> '
                                in_ann = False
                                if a + 1 < len(ann):
                                    a += 1
                                else:
                                    doc_done = True
                        except:
                            exec_type, value, tb = sys.exc_info()
                            print(traceback.format_tb(tb))
                            print(value)

                    if not in_ann: out += '\n' #fixes times where sentence detector would cut off in the middle of a label
                out += '\n'
        except Exception as e:
            logger.warning(e)
        return out

    def convert_ann_collection_to_per_token(self, annotations, tokens):
        labels_per_token = []
        for tok in tokens:
            labels = []
            for ann in annotations:
                if ann[0] <= tok[0] and ann[1] >= tok[1]:
                    labels.append(ann[2])
            labels_per_token.append(labels)
        return labels_per_token

    def evaluate(self, X, y, Xid):
        predictions = self.predict(X, Xid)
        stats = {'Totals': [0, 0, 0, 0]}


        for doc_id in predictions:
            guess = predictions[doc_id][0]
            gold = y[Xid.index(doc_id)]

            all_tokens = predictions[doc_id][1]


            reformat_gold = [tuple(pydash.flatten(go)) for go in gold]
            gold = reformat_gold

            labels_in_gold = self.convert_ann_collection_to_per_token(gold, all_tokens)
            labels_in_guess = self.convert_ann_collection_to_per_token(guess, all_tokens)

            all_known_labels = set()

            for ann in guess:
                all_known_labels.add(ann[2])

            for ann in gold:
                all_known_labels.add(ann[2])

            TP = []
            FP = []
            FN = []
            TN = []

            for index in range(0, len(all_tokens)):
                for label in all_known_labels:
                    if label in labels_in_gold[index]:
                        if label in labels_in_guess[index]:
                            TP.append(label)
                        else:
                            FN.append(label)
                    elif label in labels_in_guess[index]:
                        if label not in labels_in_gold[index]:
                            FP.append(label)
                    else:
                        TN.append(label)
            for label in all_known_labels:
                if label not in stats:
                    stats[label] = [0,0,0,0]
            for label in TP:
                stats[label][0] += 1
                stats['Totals'][0] += 1
            for label in FP:
                stats[label][1] += 1
                stats['Totals'][1] += 1
            for label in FN:
                stats[label][2] += 1
                stats['Totals'][2] += 1
            for label in TN:
                stats[label][3] += 1
                stats['Totals'][3] += 1

        for key in stats:
            TP = stats[key][0]
            FP = stats[key][1]
            FN = stats[key][2]
            TN = stats[key][3]
            if (TP + FN) != 0:
                recall = TP / (TP + FN)
            else:
                recall = 1.0
            if (TP + FP) != 0:
                precision = TP / (TP + FP)
            else:
                precision = 0.0
            if (precision + recall) != 0:
                f1 = 2 * (precision * recall) / (precision + recall)
            else:
                f1 = 0
            if (TP + FN + FP + TN) != 0:
                acc = (TP + TN) / (TP + FN + FP + TN)
            else:
                acc = 0
            stats[key] = {'precision': precision, 'recall': recall, 'f1': f1, 'TP': TP, 'FP': FP, 'FN': FN, "TN" : TN, "acc": acc}

        return stats

    def evaluate_orig(self, X, y, Xid):
        try:
            data = self.format_data(X, y)
            if len(data) == 0 or data is None:
                raise Exception("ERROR: could not format input correctly")
        except:
            raise Exception("ERROR: could not format input correctly")

        with open(self.__test_file, 'w') as f:
            f.write(data)
        inputStreamFactory = self.__java_MarkableFileInputStreamFactory(self.__java_File(self.__java_String(self.__test_file)))
        lineStream = self.__java_PlainTextByLineStream(inputStreamFactory, self.__java_String("utf-8"))
        sampleStream = self.__java_NameSampleDataStream(lineStream)

        evaluator = self.__java_TokenNameFinderEvaluator(self.__nameFinder, None)
        evaluator.evaluate(sampleStream)

        result = evaluator.getFMeasure()
        print(result.toString())
        return (result.getPrecisionScore(), result.getRecallScore(), result.getFMeasure())
    
