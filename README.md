# PINE (Pmap Interface for Nlp Experimentation)

                ██████╗ ██╗███╗   ██╗███████╗
                ██╔══██╗██║████╗  ██║██╔════╝
                ██████╔╝██║██╔██╗ ██║█████╗  
                ██╔═══╝ ██║██║╚██╗██║██╔══╝  
                ██║     ██║██║ ╚████║███████╗
                ╚═╝     ╚═╝╚═╝  ╚═══╝╚══════╝
            Pmap Interface for Nlp Experimentation

&copy; 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

## About PINE

PINE is a web-based tool for text annotation.  It enables annotation at the document level as well
as over text spans (words).  The annotation facilitates generation of natural language processing
(NLP) models to classify documents and perform named entity recognition.  Some of the features
include:
 
* Generate models in Spacy, OpenNLP, or CoreNLP on the fly and rank documents using Active Learning
  to reduce annotation time. 
 
* Extensible framework - add NLP pipelines of your choice. 
 
* Active Learning support - Out of the box active learning support
  (https://en.wikipedia.org/wiki/Active_learning_(machine_learning)) with pluggable active learning
  methods ranking functions.
 
* Facilitates group annotation projects - view other people’s annotations, calculates
  inter-annotator agreement, displays annotation performance.
 
* Enterprise authentication - integrate with your existing OAuth/Active Directory Servers.
 
* Scalability - deploy in docker compose or a kubernetes cluster; ability to use database as a
  service such as CosmosDB.
 
PINE was developed under internal research and development (IRAD) funding at the
[Johns Hopkins University Applied Physics Laboratory](https://www.jhuapl.edu/).  It was created to
support the annotation needs of NLP tasks on the
[precision medicine analytics platform (PMAP)](https://pm.jh.edu/) at Johns Hopkins.  

## Required Resources

Note - download required resources and place in `pipelines/pine/pipelines/resources`:
* apache-opennlp-1.9.0
* stanford-corenlp-full-2018-02-27
* stanford-ner-2018-02-27

Alternatively, you can use the provided convenience script:
`./pipelines/download_resources.sh`

These are required to build docker images for active learning.

----------------------------------------------------------------------------------------------------

## Quickstart

There are two main ways to run PINE:
* The "dev stack", whichs runs all the services on the host system using development servers that
  automatically update when the code is changed.  The development environment takes some time to set
  up the various dependencies and is the appropriate choice if you are going to be changing code.
* The docker compose stack, which runs individual services in different Docker containers networked
  together.  This environment requires only Docker and docker-compose to be installed and is the
  appropriate choice if you are just going to be running PINE, especially in a production setting.
  There are further configurations of the docker compose stack depending on the setting.

All activity in the PINE web user interface requires the user to log in.  Additionally, the PINE
data has access controls on it such that each user must be given permission to view or annotate
individual collections.  The user management is handled by what PINE refers to as an "auth module."
PINE currently supports two auth modules:
* The "eve" module defines users in PINE's database.  Admin users can create and manage users using
  the Admin Dashboard in the web interface, or users can be added to the database using
  command-line tools on the host.
* The "vegas" module integrates with the JHU user directory.  It requires an additional setup step
  as there is a secret associated with PINE that must be added to its configuration.  This is
  probably not the correct choice for external/standlone PINE instances.

The auth module configuration is independent of the environment chosen.  Both the dev stack and the
docker compose stack read configuration values from the `.env` file, which includes the
configuration of the auth module.

This repository also provides testing data that can be imported into PINE, which includes users and
sample collections.

### Getting started with the dev stack

See [Development Environment](#development-environment).

### Getting started with the docker compose stack

See [Docker Environments](#docker-environments).

### Getting started with the "eve" auth module

1. Set `AUTH_MODULE=eve` in the `.env` file.
2. Set the `BACKEND_SECRET_KEY` variable in the `.env` file.  If this is not done, the default
   testing value will be used which is NOT secure as it is checked in to this repo.
3. On first setup, the database will have no users in it.  To add users, either import the testing
   dataset, or use the scripts in `scripts/data` in the backend to manage users.  (See the
   *User management using "eve" auth module* sections in
   [Development Environment](#development-environment) and
   [Docker Environments](#docker-environments) below for exact commands.) Once an admin
   user has been added, users can also be added/managed by logging in as that user and using the
   Admin Dashboad.
4. Log in with the user credentials.

### Getting started with the "vegas" auth module

1. Set `AUTH_MODULE=vegas` and `VEGAS_CLIENT_SECRET` in the `.env` file.  `VEGAS_CLIENT_SECRET`
   must be obtained by contacting one of the PINE developers and being authorized to use it.
2. Set the `BACKEND_SECRET_KEY` variable in the `.env` file.  If this is not done, the default
   testing value will be used which is NOT secure as it is checked in to this repo.
3. VEGAS users are managed externally.
4. Log in with your JHED credentials.

----------------------------------------------------------------------------------------------------

## Development Environment

First, refer to the various README files in the subproject directories for dependencies.  On a clean
install of Ubuntu 18.04, this included:
1. `sudo apt install git python3.6-dev python3-pip curl make gcc`.  Note that on later versions of
   Ubuntu, you'll need to install Python 3.6 using something like pyenv.
2. `sudo pip3 install pipenv`
3. Install Node.JS V14.  One way to do this may be found here:
   https://github.com/nodesource/distributions/blob/master/README.md#deb  An IMPORTANT note here is
   that Node.JS V16 does not currently work with our npm dependencies.  This is due to an issue with
   the version of node-sass that the frontend is currently using
   (https://github.com/sass/node-sass/issues/3077).
4. `./setup_dev_stack.sh` is a convenience script to install various dependencies via apt, npm, and
   pipenv.

At this point, you should be able to run a dev stack can be run with:
```bash
./run_dev_stack.py
```

You probably also need to update `.env` for `VEGAS_CLIENT_SECRET`, if you are
planning to use that auth module.

The dev stack can be stopped with Ctrl-C.

Sometimes mongod doesn't seem to start in time.  If you see a connection
error for mongod, just close it and try it again.

Once the dev stack is up and running, the following ports are accessible:
* `localhost:4200` is the main entrypoint and hosts the web app
* `localhost:5000` hosts the backend
* `localhost:5001` hosts the eve layer

### Generating documentation

1. See `docs/README.md` for information on required environment.
2. `./generate_documentation.sh`
3. Generated documentation can then be found in `./docs/build`.

### Backend OpenAPI Specification

The backend API is documented using an [OpenAPI specification](https://swagger.io/specification/).
This specification covers the main REST API used by PINE.  A copy of the
[Swagger UI](https://swagger.io/tools/swagger-ui/) is hosted at `http[s]://<backendURL>/swagger` and
the specification itself is hosted at `http[s]://<backendURL>/openapi.yaml`.  The easiest way to
use the Swagger UI is to log in to PINE via the normal web UI and then open the Swagger UI.  This
allows the browser to set the user session cookie based on your logged in credentials and then that
cookie will be used in all calls to the Swagger UI/API.

This specification is found in the source code at `backend/pine/backend/api/openapi.yaml`.
*NOTE* however that this file is autogenerated by the `./update_openapi.sh` script.  The "base"
file is located at `backend/pine/backend/api/base.yaml` which then pulls in information from other
files.  ALL changes to the backend API should result in updates to the specification, as it is *NOT*
automatically updated or generated based on code changes.  The `./update_openapi.sh` script requires
Docker to run and standard Linux tools (find, grep, awk, sort) but no other dependencies.

### Testing Data

To import testing data, run the dev stack and then run:
```bash
./setup_dev_test_data.sh
```
You will need python3 and pipenv installed to run this script.

*WARNING*: This script will remove any pre-existing data.  If you need to clear your database
for other reasons, stop your dev stack and then `rm -rf local_data/dev/eve/db`.

### User management using "eve" auth module

Note: these scripts only apply to the "eve" auth module, which stores users
in the eve database.  Users in the "vegas" module are managed externally.

Once the system is up and running:
```bash
cd backend && scripts/data/list_users.sh
```

This script will reset all user passwords to their email:
```bash
cd backend && scripts/data/reset_user_passwords.sh
```

This script will add a new administrator:
```bash
cd backend && scripts/data/add_admin.sh <unique id> <email/username> <password>
```

This script will set a single user's password.
```bash
cd backend && scripts/data/set_user_password.sh <id/email/username> <password>
```

Alternatively, there is an Admin Dashboard through the web interface.

### Testing

There are test cases written using Cypress; for more information, see `test/README.md`.

The short version, to run the tests using the docker-compose stack:
1. `test/build.sh`
2. `test/run_docker_compose.sh --report`
3. Check `./results/<timestamp>` (the script in the previous step will print out the exact path) for:
   * `reports/report.html`: an HTML report of tests run and their status
   * `screenshots/`: for any screenshots from failed tests
   * `videos/`: for videos of all the tests that were run

To use the interactive dashboard:
1. `test/build.sh`
2. `test/run_docker_compose.sh --dashboard`

It is also possible to run the cypress container directly, or locally with the dev stack.  For more
information, see `test/README.md`.

### Versioning

There are three versions being tracked:
* overall version: environment variable PINE_VERSION based on the git tag/revision information (see `./version.sh`)
* eve/database version: controlled in `eve/python/settings.py`
* frontend version: controlled in `frontend/annotation/package.json`

The eve/database version should be bumped up when the schema changes.  This will (eventually) be
used to implement data migration.

The frontend version is the least important.

### Using the copyright checking pre-commit hook

The script `pre-commit` is provided as a helpful utility to make sure that new files checked into
the repository contain the copyright text.  It is _not_ automatically installed and must be
installed manually:

`ln -s ../../pre-commit .git/hooks/`

This hook greps for the copyright text in new files and gives you the option to abort if it is
not found.

----------------------------------------------------------------------------------------------------

## Docker Environments

*IMPORTANT*:

For all the docker-compose environments, it is required to set a `PINE_VERSION` environment
variable.  To do this, either prepend each docker-compose command:
```bash
PINE_VERSION=$(./version.sh) docker-compose ...
```
Or export it in your shell:
```bash
export PINE_VERSION=$(./version.sh)
docker-compose ...
```

The docker environment is run using docker-compose.  There are two supported configurations: the
default and the prod configuration.

If desired, edit `.env` to change default variable values.  You probably also need to update
`.env` for `VEGAS_CLIENT_SECRET`, if you are planning to use that auth module.

To build the images for DEFAULT configuration:
```bash
docker-compose build
```
Or use the convenience script:
```bash
./run_docker_compose.sh --build
```
If your network has an SSL certificate in its configuration, you may be able to do this:
```bash
./run_docker_compose.sh --build-with-cert <crt file>
```
This has only been tested in internal environments and may not cover all scenarios.  For example:
the docker container has to be able to install the ca-certificates package before it can be
installed.

To run containers as daemons for DEFAULT configuration (remove -d flag to see logs):
```bash
docker-compose up
```
You may also want the `--abort-on-container-exit` flag which will make errors more apparent.

Or use the convenience script:
```bash
./run_docker_compose.sh --up
```

With default settings, the webapp will now be accessible at `https://localhost:8888`

### Production Docker Environment

To use the production docker environment instead of the default, simply add
`-f docker-compose.yml -f docker-compose.prod.yml` after the `docker-compose` command, e.g.:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
```

Note that you probably need to update `.env` and add the `MONGO_URI` property.

### Test data

To import test data, you need to run the docker-compose stack using the docker-compose.test.yml file:
```bash
docker-compose build
docker-compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.test.yml up
```
Or use the convenience script:
```bash
./run_docker_compose.sh --build
./run_docker_compose.sh --up-test
```

Once the system is up and running:
```bash
./setup_docker_test_data.sh
```
You will need python3 and pipenv installed to run this script.

Once the test data has been imported, you no longer need to use the docker-compose.test.yml file.

If you need to clear the database, bring down the container and remove the `nlp_webapp_eve_db` and
`nlp_webapp_eve_logs` volumes with `docker volume rm`.

If you are migrating from very old PINE versions, it is possible that you need to migrate your
data if you are seeing applications errors:
```bash
docker-compose exec eve python3 python/update_documents_annnotation_status.py
```

### User management using "eve" auth module

Note: these scripts only apply to the "eve" auth module, which stores users
in the eve database.  Users in the "vegas" module are managed externally.

Once the system is up and running:
```bash
PINE_VERSION=$(./version.sh) docker-compose exec backend scripts/data/list_users.sh
```

This script will reset all user passwords to their email:
```bash
PINE_VERSION=$(./version.sh) docker-compose exec backend scripts/data/reset_user_passwords.sh
```

This script will add a new administrator:
```bash
PINE_VERSION=$(./version.sh) docker-compose exec backend scripts/data/add_admin.sh <id> <email/username> <password>
```

This script will set a single user's password.
```bash
PINE_VERSION=$(./version.sh) docker-compose exec backend scripts/data/set_user_password.sh <id/email/username> <password>
```

Alternatively, there is an Admin Dashboard through the web interface.

----------------------------------------------------------------------------------------------------

## Misc Configuration

### Configuring Logging

See logging configuration files in `./shared/`.  `logging.python.dev.json` is used with the
dev stack; the other files are used in the docker containers.

The docker-compose stack is currently set to bind the `./shared/` directory into the containers
at run-time.  This allows for configuration changes of the logging without needing to rebuild
containers, and also allows the python logging config to live in one place instead of spread out
into each container.  This is controlled with the `${SHARED_VOLUME}` variable from `.env`.

Log files will be stored in the `${LOGS_VOLUME}` variable from `.env`.  Pipeline models files will
be stored in the `${MODELS_VOLUME}` variable from `./env`.

### Collection/Document Images

It is now possible to explore images in the "annotate document" page in the frontend UI.  The image
URL is specified in the metadata field with the key `imageUrl`.  If the URL starts with a "/" it
is loaded from a special endpoint in the backend that loads from a locally attached volume.  For
docker, this volume is controlled by the `DOCUMENT_IMAGE_VOLUME` variable in `.env`.  For running
the dev stack, this volume can be found in `./local_data/dev/test_images`.

To upload images outside the UI, the following procedures should be used:
* All images in the collection should be in the directory `<image volume>/by_collection/<collection ID>`.
* Subdirectories (such as for individual documents) are allowed but not mandatory.
* The document metadata `imageUrl` should be set to `/<image path within the collection directory>`.
* For example: an imageUrl of `/image.jpg` would load `/<image volume>/by_collection/<collection ID>/image.jpg`
  through the backend.
