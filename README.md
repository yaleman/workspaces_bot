# Role requirements

Attach policies:

*  `AmazonWorkSpacesAdmin` - Amazon managed policy

inline plicy to let it edit itself:

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "lambda:UpdateFunctionConfiguration",
                    "lambda:GetFunctionConfiguration"
                ],
                "Resource": [
                    "arn:aws:lambda:*:*:function:workspacebot"
                ]
            }
        ]
    }