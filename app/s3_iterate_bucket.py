from typing import Iterable, Tuple

import boto3

FileKey = str
FileContent = bytes

DEFAULT_BUCKET_NAME = 'dh83ks92md-is-raw-footage'

def iterate_files_in_response(bucket_name: str, response_contents):
    for obj in response_contents:
        key = obj['Key']

        # Download the file
        file_obj = s3.get_object(Bucket=bucket_name, Key=obj['Key'])

        # Read the file's content as bytes
        file_content_bytes = file_obj['Body'].read()

        yield key, file_content_bytes


def iterate_files_in_bucket(bucket_name: str, prefix: str='', *s3_args, **s3_kwargs) -> Iterable[Tuple[FileKey, FileContent]]:
    s3 = boto3.client('s3', *s3_args, **s3_kwargs)

    # Initialize a continuation token for pagination
    continuation_token = None
    
    while True:
        if continuation_token:
            continuation_params = {'ContinuationToken': continuation_token}
        else:
            continuation_params = {}

        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, **continuation_params)
        
        if 'Contents' in response:
            yield from iterate_files_in_response(bucket_name, response['Contents'])

        # Check if there are more objects to retrieve
        if not response['IsTruncated']:
            break
        
        # Update the continuation token for the next iteration
        continuation_token = response['NextContinuationToken']

# Replace 'your-bucket-name' with the actual bucket name
bucket_name = 'your-bucket-name'
list_files_in_bucket(bucket_name)
