&copy; 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

## Developer Environment

Required packages:
* python 3.8
* pipenv
* make

`pipenv install --dev`

### Generating documentation

Make sure you have the proper latex packages installed:
* `sudo apt install latexmk texlive-latex-recommended texlive-fonts-recommended texlive-latex-extra`

Generate through pipenv:
* `pipenv run doc` or use convenience script `../generate_documentation.sh`

Generated documentation can then be found in `./build`.
