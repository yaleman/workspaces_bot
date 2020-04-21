#!/usr/bin/env bash

echo "doing testing"
# shellcheck disable=SC2035
pipenv run pytest *.py
pipenv run pytest workspaces

pipenv run pylint workspaces
echo "done testing, removing old code"
if [ -f function.zip ]; then   
    rm function.zip
fi
rm -rf package/

echo "Updating python libs"
pip3 install --upgrade --target ./package -r requirements.txt
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
AWS_PROFILE=aws-323 aws lambda update-function-code --function-name workspacebot --zip-file fileb://function.zip
