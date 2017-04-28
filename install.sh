#!/bin/bash -e

# Install virtualenv
virtualenv venv

# Install python dependencies
venv/bin/pip install -r requirements.txt

# Install chromedriver
cd venv/bin/
curl -s https://chromedriver.storage.googleapis.com/2.29/chromedriver_mac64.zip > chromedriver_mac64.zip
unzip chromedriver_mac64.zip
rm chromedriver_mac64.zip
