#!/usr/bin/env bash

pipenv run pytest *.py workspaces/*.py 

mv setup.txt setup.cfg

if [ -f function.zip ]; then   
    rm function.zip
fi

if [ -z "${1}" ]; then
    if [ "${1}" == "clean" ]; then
        echo "Removing old package"
        rm -rf package/

        echo "Updating python libs"
        pip3 install --upgrade --target ./package -r requirements.txt

    else
        echo "Don't know what ${1} means, try clean?"
    fi
fi


mv setup.cfg setup.txt 

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


