# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
TOP_DIR = os.path.abspath(os.path.join(DIR, "..", ".."))
SRC_DIRS = [
    os.path.join(TOP_DIR, "backend"),
    os.path.join(TOP_DIR, "client"),
    #os.path.join(TOP_DIR, "eve", "python"),
    os.path.join(TOP_DIR, "pipelines")
]
for SRC_DIR in SRC_DIRS:
    sys.path.insert(0, SRC_DIR)


# -- Project information -----------------------------------------------------

project = 'pine'
copyright = '(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.'
author = 'JHU/APL'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.intersphinx',
    'autoapi.extension'
]

autoclass_content = 'both'
autoapi_python_class_content = 'both'

import autoapi.extension
autoapi_options = list(autoapi.extension._DEFAULT_OPTIONS)
#autoapi_options.remove("private-members")

autoapi_type = 'python'
autoapi_dirs = SRC_DIRS
autoapi_ignore = ["*/test/*", "*/docs/*", "*/docker/*"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['Thumbs.db', '.DS_Store']

intersphinx_mapping = {'python': ('https://docs.python.org/3', None),
                       'requests': ('https://requests.readthedocs.io/en/master', None),
                       'pymongo': ('https://pymongo.readthedocs.io/en/stable', None)}
if os.path.isdir("/etc/ssl/certs"):
    tls_cacerts = "/etc/ssl/certs/"


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'bizstyle'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']