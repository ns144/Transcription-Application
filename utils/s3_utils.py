import boto3

def get_s3_client(secret):
    SECRET_KEY =  secret["SECRET_KEY"]
    ACCESS_KEY =  secret["ACCESS_KEY"]
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    return s3

def get_file(filename, secret):
    BUCKET_NAME = secret["BUCKET_NAME"]

    s3 = get_s3_client(secret)
    s3.download_file(BUCKET_NAME, filename, filename)

def upload_file(filename, secret):
    s3 = get_s3_client(secret)
    BUCKET_NAME = secret["BUCKET_NAME"]
    try:
        response = s3.upload_file(filename, BUCKET_NAME, str(filename))
    except Exception as error:
        print("An exception occurred:", error)