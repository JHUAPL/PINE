&copy; 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

                ██████╗ ██╗███╗   ██╗███████╗
                ██╔══██╗██║████╗  ██║██╔════╝
                ██████╔╝██║██╔██╗ ██║█████╗  
                ██╔═══╝ ██║██║╚██╗██║██╔══╝  
                ██║     ██║██║ ╚████║███████╗
                ╚═╝     ╚═╝╚═╝  ╚═══╝╚══════╝
            Pmap Interface for Nlp Experimentation
                      Web App Backend

## Development Environment

Developer pre-reqs:
* Python 3 with pip and pipenv

First-time setup:
* `pipenv install --dev`
  - This will create a virtualenv and install the necessary packages.

Running the server:
* `./dev_run.sh`

Once test data has been set up in the eve layer, the script `setup_dev_data.sh`
can be used to set up data from the backend's perspective.

## Setup

Before running, you must edit ../.env and set `VEGAS_CLIENT_SECRET` appropriately
if you are using the "vegas" auth module.  Alternatively set this secret as an
environment variable.

## Authentication:

* The "vegas" module is used by default.
* An "eve" module is also provided.  This queries the eve server for users and uses those
  for authentication.  You can run `scripts/data/list_users.sh` to list available users in the
  data server.  No further configuration is needed locally.

## Production Environment:

This service can also be run as a Docker container.
It should be run using docker-compose at the top level (../).
