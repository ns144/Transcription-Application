# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/
import base64
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def get_secret():

    secret_name = "transcription_service_api_key"
    region_name = "eu-central-1"

    # Create a Secrets Manager client
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = get_secret_value_response['SecretString']
        secret = base64.b64decode(secret)
        secret = json.loads(secret)
    except ClientError as e:
        # For a list of exceptions thrown, see
        print("Error when attempting to get secret:" + str(e))
        with open('env.json') as secret_file:
            secret = json.load(secret_file)
    except NoCredentialsError as e:
        print("Error when attempting to get secret:" + str(e))
        with open('env.json') as secret_file:
            secret = json.load(secret_file)

    return secret


# print(get_secret())
