---
title: 'PINE: An open source collaborative text annotation tool'
tags:
  - Python
  - NLP
  - Natural Language Processing
  - Named Enitity Recognition
  - Document Classification
  - Active Learning
authors:
  - name: Brant W Chee^[Corresponding author]
    orcid: 0000-0002-6174-4201
    affiliation: "1, 2" 
  - name: Douglas M Zabransky
    affiliation: 1
  - name: Michael Cao
    affiliation: 1 
  - name: Matthew K Chapman
    affiliation: 1
  - name: Fernando J Ortiz-Sacarello
    affiliation: 1
  - name: Willfredo Montanez Vazquez
    affiliation: 1
  - name: Laura J Glendenning
    affiliation: 1
affiliations:
 - name: Johns Hopkins University Applied Physics Laboratory
   index: 1
 - name: Division of Health Science Informatics, Johns Hopkins University School of Medicine
   index: 2
date: 25 June 2020
bibliography: paper.bib
---
# Summary

We introduce the PMAP Interface for NLP Experimentation (PINE) a scaleable web-based tool for collaborative text annotation and natural language processing (NLP) experimentation.  Manually annotated data is a necessity for training many machine learning based NLP tasks.  We have developed an extensible framework to support annotation of text while also enabling experimentation in machine learning methods.  

`PINE` is an enterprise annotation framework supporting many users.  It supports both Docker Compose and Kubernetes deployment with an internal MongoDB or cloud backed NoSQL databases such as CosmosDB [@turnbull:2014][@burns:2016][@chodorow:2013].  Docker Compose and Kubernetes allow for horizontal scaling of either various components if necessary. It is currently deployed as the named entity recognition (NER) annotation tool on the Johns Hopkins University Precision Medicine Analytics Platform (PMAP)[^1].

Collections of documents are uploaded through a web based interface.  Each collection represents an independent project with documents, annotators, labels and associated machine learning pipelines.   When a user adds a collection, they can add relevant metadata such as Dublin Core Metadata Elements Set [@ISO1536-1:2017]; images to view alongside text; users allowed to view or annotate the collection; labels for documents or NER; document classification or NER pipelines; and percent of documents that are overlapping between annotators.  

`PINE` facilitates group annotation projects allowing users within a project to view each others annotations, calculate inter-annotator agreement and display annotation performance.  Annotation overlap is configurable at collection generation.  This lets a collection owner to select what percent of the documents are annotated by all annotators.  A setting of 1 indicates all documents are annnotated by everyone, 0 indicates none are. Some overlap is necessary to calculate interannotator agreement. While annotations are modifiable, changes are tracked and store. This can be useful for example, to see if annotators change labels after a modification to annotation guidelines.   

Annotation is a time consuming and potentially costly task. If enabled, `PINE` supports active learning to help reduce the time and effort in generating gold standard data.  Our implementation of active learning generates a new classifier after x number of documents where x is defined at collection generation time.  After a classifier is generated it ranks previously unlabelled documents and presents them to the users in rank order.  One example of a ranking function could rank documents higher based on increasing amounts of uncertainty from the classifier.  We provide several ranking function, however it is modular and extensible in order to facilitate this area of research.


[^1]: https://pm.jh.edu/

# Related Work
A popular open source tool annotation only tool, BRAT is widely used [@stenetorp:2012].  It supports advanced annotation of relationships and linkages between entities.  However, it does not support document level labeling, image display, enterprise authentication and tracking of annotation changes. 

Other annotation tools exist which support active learning. DUALIST is mature active learning framework that supports labeling of documents and performs active leanring over sequences by allowing the user to submit queries and patterns [@settles:2011].  This differs from other implementations of active learning for sequence labelling such as ourswhere the active learning is transparent to the user and they annotate sequences as presented to them [@searle:2019].  PINE is most similar to MedCATTrainer, they are both modern web based Dockerized annotation tools.  MedCATTrainer is later work following on DUALIST, instead of users directly submitting queries and patterns, MedCATTrainer queries users asking them to provide feedback on correctness for an identified concept [searle:2019].  

To our knowledge no current tool supports realtime generation of inter-annotator statistics on per document and collection level.  These statistics are useful in identifying if further refinement of any annotation guidelines are necessary and can be used in publications involving the data.  `PINE` is also unique in enabling image viewing alongside text for multimodality annotation.  Within the biomedical domain it can be useful for instance to view a radiology report with the associated imagery (for example X-ray or Ultrasound). Downstream machine learning models can potentially enable joint learning over both images and text.  

# Implementation
`PINE` is implemented using a service-oriented architecture, with each service deployed as a Docker container and the overall system deployed using Docker Compose or Kubernetes [@turnbull:2014][@burns:2016].  The frontend is a web GUI developed using Angular and served by an Nginx reverse proxy which also provides access to the backend container, which is a RESTful web server developed in Python and Flask and deployed using Gunicorn [@fain:2016][@dwyer:2017][@gunicorn:2017].  The REST backend server manages user authentication, either using a OAuth2 workflow or using locally-controlled user information, and controls access to database resources.

The database resources are wrapped in a Guincorn-deployed Eve server, which provides a REST interface on top of a remote or local database that supports the MongoDB wire protocol [@gunicorn:2017][@eve:2020][@chodorow:2013]. The figure \autoref{fig:architecture} depicts the architecture of `PINE`.  Individual Docker containers are notated by the grey rectangles.  Data is transfered between containers within a private Docker network denoted by arrows within the larger `PINE` rectangle which represents the appliction.  Volumes which hold persistent data are denoted by the red file boxes.  Persistent data includes generated models and image files.  Optionally MongoDB and authentication services can be deployed within Docker containers in the `PINE` application.  However, the current deployment at Johns Hopkins uses external databases and authentication denoted by the clouds.  

![Diagram of the current architecture.  The application consists of multiple Docker containers in the grey rectangles.] {fig:architecture}(architecture.png)
<!--
Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.
-->

`PINE` was developed with extensibility in mind, multiple pipelines for NER and document classification exist. Example NER pipelines are implemented in: CoreNLP, OpenNLP, and spaCy [@manning:2014][@morton:2005][@honnibal:2017].  A sample document classification pipeline in Scikit-learn [@pedregosa:2011] is also included.  For each of the pipelines, options for the native libraries are exposed from the web when a user configures a new collection.  A new pipeline can be added by dockerizing the library and writing a Python wrapper. The pieplines communicate with the backend via a Redis service.

The wraper is similar to classifier syntax in Scikit-learn [@pedregosa:2011].  The methods take a list of text as input X, with labels, y in the form of a list of entities for each piece of text that includes the character start offset, end offset, and label for each entity.  For document classification the input is the same, however labels are a list of labels for each text.  The main methods which need to be implemented are:

```python
class Pipeline(object, metaclass=abc.ABCMeta):
    def __init__(self):

    def fit(self, X, y):

    def predict(self, X, Xid):

    def predict_proba(self, X, Xid):

    def next_example(self, X, Xid):

    def save_model(self, model_name):
    
    def load_model(self, model_name):
```

There are several active learning ranking algorithms implemented: least confidence, largest margin, entropy ranking, least confidence squared, least confidence squared by entity, random rank, and most of least popular.  Active learning is similarly extensible.  Given an input of reults from a Pipeline a new active learning algorithm returns a ranking of the results.  The ranking order represents the order in which unseen documents are presented for annotation.  

# Acknowledgements

PINE was developed by staff at the Johns Hopkins University Applied Physics Laboratory (JHUAPL).  Funding was provided as an internal research and development project by JHUAPL.  The authors would like to thank all the staff at JHUAPL and the Johns Hopkins University School of Medicine who have provided feedback, bug-finding and deployment help.  

# References

