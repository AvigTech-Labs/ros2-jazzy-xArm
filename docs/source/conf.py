# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ROS2 Jazzy - xArm 6'
copyright = '2026, AvigTech'
author = 'AvigTech'
release = 'Jazzy (Ubuntu 24.04)'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_copybutton',
    'sphinx.ext.mathjax',
    'sphinx_tabs.tabs',
]
templates_path = []  # No se incluye una carpeta de plantillas personalizada
exclude_patterns = []

language = 'es'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme' 
html_static_path = ['_static']
html_show_sourcelink = False
html_css_files = ['css/custom.css']

source_suffix = {
    '.rst': 'restructuredtext',
}

