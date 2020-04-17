# Introduction 
This is a special microservice to deal with Sesam installations in the AWS environment, and specifically around being able to host and retrieve microservices residing within AWS ECR.

# Getting Started
The microservice simply communicates with the EC2 metadata service to generate a username and password token that work with the 'docker login' function within the microservice service configuration in Sesam. You will need to tell it the IP address of the box Sesam resides on, and provide it with a JWT token so it can store the retrieved token in a sesam global secret: AWS_ECR_TOKEN

The microservice config should be as follows:
---------------------------------------------
```
{
  "_id": "aws-ecr-getlogin",
  "type": "system:microservice",
  "metadata": {
    "tags": ["system"]
  },
  "connect_timeout": 60,
  "docker": {
    "environment": {
      "LOCALIP": "<sesam node box IP here>",
      "SESAM_JWT_TOKEN": "<sesam JWT token able to write secrets to sesam. ie admin>"
    },
    "image": "sesamcommunity/aws-ecr-getlogin:1.0.0",
    "memory": 128,
    "port": 5001,
  },
  "read_timeout": 7200,
  "use_https": false,
  "verify_ssl": true
}

```
You then need a pipe to trigger and schedule retriving the token. They are valid for 12 hours.
```
{
  "_id": "aws-ecr-getlogin-trigger",
  "type": "pipe",
  "source": {
    "type": "json",
    "system": "aws-ecr-getlogin",
    "url": "/"
  },
  "transform": {
    "type": "dtl",
    "rules": {
      "default": [
        ["copy", "_id"]
      ]
    }
  },
  "pump": {
    "cron_expression": "0 */12 * * ?"
  }
}
```

Microservices stored in ECR can then be setup:
---------------------------------------------
The most important bit is to understand that Sesam usually pulls and refreshes a microservice on a configuration change. This means it will do this every 12 hours unless we tell it not to.

This is achieved by setting: "skip_pull": true

Which means to pull a newer version, you will need to set this to false, and then pull and restart the microservice, setting it back to true afterwards.

```
{
  "_id": "example-ecr-microservices",
  "type": "system:microservice",
  "metadata": {
    "tags": ["test"]
  },
  "connect_timeout": 60,
  "docker": {
    "environment": {},
    "image": "12345.dkr.ecr.eu-central-1.amazonaws.com/example-ecr-microservice:pipeline-1234-git-1234",
    "memory": 512,
    "password": "$SECRET(AWS_ECR_TOKEN)",
    "port": 5001,
    "skip_pull": false,
    "username": "AWS"
  },
  "read_timeout": 7200,
  "use_https": false,
  "verify_ssl": true
}
```
