## Development Environment

Requirements:
  * Mongo >=4
  * Python 3, Pip, and Pipenv

With pipenv, doing a `pipenv install --dev` will install the python
dependencies in a virtual environment.

After this you can run `dev_run.sh` to run the dev environment.
Initially the system starts with an empty database; run
`setup_dev_data.sh` to set up initial testing data.

This script contains identifiers for the valid users, pipeline, collections, 
documents and annotations in the database.  If you run this script it will 
generate new data but the identifiers will change.  They will be printed 
at the end of script.

Note that this setup script adds users but does NOT set their passwords.
You should use the setup script in the backend directory to do that. Run 
`set_user_password.sh` with their email, not username.

## Production Environment

This service can also be run as a Docker container.
It should be run using docker-compose at the top level (../).
