import json
import logging
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_secret(secret_name: str = "hawwa/datalake/credentials", region_name: str = "us-east-1") -> dict:
    """
    Retrieves secret key-value pairs dynamically from AWS Secrets Manager.
    
    Parameters:
        secret_name (str): The name/path of the secret in AWS Secrets Manager.
        region_name (str): The AWS region where the secret is stored.
        
    Returns:
        dict: Parsed dictionary containing the secret credentials.
    """
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        logging.info(f"Retrieving secret '{secret_name}' from AWS Secrets Manager ({region_name})...")
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logging.error(f"Failed to retrieve secret '{secret_name}'. Error Code: {error_code}")
        
        if error_code == 'ResourceNotFoundException':
            logging.error(f"The requested secret '{secret_name}' was not found in region {region_name}.")
        elif error_code == 'InvalidRequestException':
            logging.error("The request was invalid due to improper parameters.")
        elif error_code == 'InvalidParameterException':
            logging.error("The request had an invalid parameter value.")
        elif error_code == 'AccessDeniedException':
            logging.error("Access denied. Ensure your IAM user/role has 'secretsmanager:GetSecretValue' permissions.")
            
        raise e

    # Decrypts secret using the associated KMS key
    if 'SecretString' in get_secret_value_response:
        secret_data = get_secret_value_response['SecretString']
        return json.loads(secret_data)
    else:
        # Binary secret case (rare for JSON credentials)
        binary_data = get_secret_value_response['SecretBinary']
        return json.loads(binary_data.decode('utf-8'))


if __name__ == "__main__":
    # Test script execution
    try:
        credentials = get_secret(secret_name="hawwa/datalake/credentials", region_name="us-east-1")
        logging.info("✅ Successfully retrieved secrets!")
        
        # Safely log keys without printing secret values
        print("\nRetrieved Keys:")
        for key in credentials.keys():
            print(f"  - {key}")
            
    except Exception as err:
        logging.error(f"Script execution failed: {err}")