#!/usr/bin/env bash

if [ "$(basename "$(pwd)")" != "workspaces_bot" ]; then
    echo "Need to run this from ./workspaces_bot"
    exit
fi

echo "Installing env"
poetry install

echo "doing testing"
poetry run pytest

poetry run pylint workspaces *.py
echo "done testing, removing old code"
if [ -f function.zip ]; then
    rm function.zip
fi
rm -rf ./package/

echo "Updating python libs"
python -m pip install --upgrade --target ./package -r requirements.txt
rsync -a workspaces package/

cd package || exit
echo "Adding python packages to package"
zip -q -r9 ../function.zip .
cd ..

echo "Adding lambda function to package"
zip -r9 -g function.zip lambda_function.py

echo "Adding workspace* to package"
zip -r9 -g function.zip workspace*.py

echo "Uploading package to lambda"
aws lambda update-function-code --function-name workspacebot --zip-file fileb://function.zip || exit

echo "Removing package folder"
rm -rf ./package/
rm function.zip
