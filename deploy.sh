#!/usr/bin/env bash

mv setup.txt setup.cfg
echo "Removing old package"

if [ -f function.zip ]; then   
    rm function.zip
fi
rm -rf package/

echo "Updating python libs"
pip3 install --upgrade --target ./package -r requirements.txt
mv setup.cfg setup.txt 
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


