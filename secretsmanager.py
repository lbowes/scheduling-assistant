# https://stackoverflow.com/questions/58000751/using-aws-secrets-manager-with-python-lambda-console
import boto3
import json
import base64
from botocore.exceptions import ClientError


class SecretsManager:
    def __init__(self, region: str) -> None:
        self._session = boto3.session.Session()
        self._client = self._session.client(
            'secretsmanager',
            region_name=region
        )


    def get_secret(self, name: str) -> str:
        try:
            get_secret_value_response = self._client.get_secret_value(SecretId=name)
        except ClientError as e:
            error_code = e.response['Error']['Code'] 
            
            if error_code == 'AccessDeniedException':
                print(str(e.reponse))
                raise e
            if error_code == 'DecryptionFailureException':
                # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif error_code == 'InternalServiceErrorException':
                # An error occurred on the server side.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif error_code == 'InvalidParameterException':
                # You provided an invalid value for a parameter.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif error_code == 'InvalidRequestException':
                # You provided a parameter value that is not valid for the current state of the resource.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif error_code == 'ResourceNotFoundException':
                # We can't find the resource that you asked for.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
        else:
            # Decrypts secret using the associated KMS CMK.
            # Depending on whether the secret is a string or binary, one of these fields will be populated.
            if 'SecretString' in get_secret_value_response:
                secret = get_secret_value_response['SecretString']
            else:
                secret = base64.b64decode(get_secret_value_response['SecretBinary'])

            return secret
