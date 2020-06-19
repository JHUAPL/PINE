&copy; 2019 The Johns Hopkins University Applied Physics Laboratory LLC.



## Required Resources
Note - download required resources and place in pipelines/pine/pipelines/resources
apache-opennlp-1.9.0
stanford-corenlp-full-2018-02-27
stanford-ner-2018-02-27

These are required to build docker images for active learning

## Configuring Logging

See logging configuration files in `./shared/`.  `logging.python.dev.json` is used with the
dev stack; the other files are used in the docker containers.

The docker-compose stack is currently set to bind the `./shared/` directory into the containers
at run-time.  This allows for configuration changes of the logging without needing to rebuild
containers, and also allows the python logging config to live in one place instead of spread out
into each container.  This is controlled with the `${SHARED_VOLUME}` variable from `.env`.

Log files will be stored in the `${LOGS_VOLUME}` variable from `.env`.  Pipeline models files will
be stored in the `${MODELS_VOLUME}` variable from `./env`.

## Development Environment

First, refer to the various README files in the subproject directories for dependencies.

Install the pipenv in pipelines.

Then a dev stack can be run with:
```bash
./run_dev_stack.py
```

You probably also need to update `.env` for `VEGAS_CLIENT_SECRET`, if you are
planning to use that auth module.

The dev stack can be stopped with Ctrl-C.

Sometimes (for me) mongod doesn't start in time or something.  If you see a connection
error for mongod, just close it and try it again.

Once the dev stack is up and running, the following ports are accessible:
* `localhost:4200` is the main entrypoint and hosts the web app
* `localhost:5000` hosts the backend
* `localhost:5001` hosts the eve layer

### Using the copyright checking pre-commit hook

The script `pre-commit` is provided as a helpful utility to make sure that new files checked into
the repository contain the copyright text.  It is _not_ automatically installed and must be
installed manually:

`ln -s ../../pre-commit .git/hooks/`

This hook greps for the copyright text in new files and gives you the option to abort if it is
not found.

### Clearing the database

First, stop your dev stack.  Then `rm -rf eve/db` and start the stack again.

### Importing test data

Once running, test data can be imported with:
```bash
./setup_dev_data.sh
```

### Updating existing data

If there is existing data in the database, it is possible that it needs to be
migrated.  To do this, run the following once the system is up and running:
```bash
cd eve/python && python3 update_documents_annnotation_status.py
```

## Docker Environments

The docker environment is run using docker-compose.  There are two supported configurations: the
default and the prod configuration.

If desired, edit `.env` to change default variable values.  You probably also need to update
`.env` for `VEGAS_CLIENT_SECRET`, if you are planning to use that auth module.

To build the images for DEFAULT configuration:
```bash
docker-compose build
```

To run containers as daemons for DEFAULT configuration (remove -d flag to see logs):
```bash
docker-compose up -d
```

You may also want the `--abort-on-container-exit` flag which will make errors more apparent.

With default settings, the webapp will now be accessible at https://localhost:8888

To watch logs for DEFAULT configuration:
```bash
docker-compose logs -f
```

To bring containers down for DEFAULT configuration:
```bash
docker-compose down
```

### Production Docker Environment

To use the production docker environment instead of the default, simply add
`-f docker-compose.yml -f docker-compose.prod.yml` after the `docker-compose` command, e.g.:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
```

Note that you probably need to update `.env` and add the `MONGO_URI` property.

### Clearing the database

Bring all the containers down.  Then do a `docker ps --all` and find the numeric ID of the eve
container and remove it with `docker rm <id>`.  Then, remove the two eve volumes with
`docker volume rm nlp_webapp_eve_db` and `docker volume rm nlp_webapp_eve_logs`.  Finally, restart
your containers.

### Importing test data

Once the system is up and running:
```bash
./setup_docker_test_data.sh
```

### Updating existing data

If there is existing data in the database, it is possible that it needs to be
migrated.  To do this, run the following once the system is up and running:
```bash
docker-compose exec eve python3 python/update_documents_annnotation_status.py
```

### User management using "eve" auth module

Note: these scripts only apply to the "eve" auth module, which stores users
in the eve database.  Users in the "vegas" module are managed externally.

Once the system is up and running:
```bash
docker-compose exec backend scripts/data/list_users.sh
```

This script will reset all user passwords to their email:
```bash
docker-compose exec backend scripts/data/reset_user_passwords.sh
```

This script will add a new administrator:
```bash
docker-compose exec backend scripts/data/add_admin.sh <email username> <password>
```

This script will set a single user's password.
```bash
docker-compose exec backend scripts/data/set_user_password.sh <email username> <password>
```

Alternatively, there is an Admin Dashboard through the web interface.

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
