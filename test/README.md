
                ██████╗ ██╗███╗   ██╗███████╗
                ██╔══██╗██║████╗  ██║██╔════╝
                ██████╔╝██║██╔██╗ ██║█████╗  
                ██╔═══╝ ██║██║╚██╗██║██╔══╝  
                ██║     ██║██║ ╚████║███████╗
                ╚═╝     ╚═╝╚═╝  ╚═══╝╚══════╝
            Pmap Interface for Nlp Experimentation

&copy; 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

## Cypress

The GUI test cases are written using Cypress (https://www.cypress.io/).
The actual test cases can be seen in `tests/cypress/integration/`.

## PyTest

The python unit test cases are writting using PyTest (https://docs.pytest.org/).
The actual test cases can be seen in `tests/pytest/`.

## Running in developer environment

```
pipenv install --dev
pushd tests
npm install
```

Then, when the dev stack is running:

```
./open_with_dev_stack.sh [--pytest|--cyptress]
```

This will either run pytest or open the cypress dashboard.

Note that running with the dev stack is noticably slower than running with the docker-compose stack.
You should also be sure to freshly import the testing data before you run the tests
(`./setup_test_data.sh`), as the tests may add data to the database that will mess up future runs.

## Running with docker

To run with docker, a standalone container is built with the cypress code in it.

To build the docker container(s), run
```
./build.sh
```

This will build the entire docker-compose stack and import the test data into a test database
(not the same one as running normal docker-compose).

To run the docker-compose stack and then the standalone cypress container, you can then run
```
./run_docker_compose.sh <arguments>
```

For usage instructions, run the script with no arguments.

It is also possible to run the cypress container directly, as long as you set the following
environment variables:
* `CYPRESS_BASE_URL`: the URI to the frontend
* `CYPRESS_API_URL`: the URI to the backend
