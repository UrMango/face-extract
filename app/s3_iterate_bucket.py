from typing import Iterable, Tuple

import boto3

FileKey = str
FileContent = bytes

DEFAULT_BUCKET_NAME = 'dh83ks92md-is-raw-footage'


def iterate_files_in_response(s3, bucket_name: str, response_contents) -> Iterable[Tuple[FileKey, FileContent]]:
    for obj in response_contents:
        key = obj['Key']
        if key.endswith('/'):
            continue

        # Download the file
        file_obj = s3.get_object(Bucket=bucket_name, Key=key)

        # Read the file's content as bytes
        file_content_bytes = file_obj['Body'].read()

        yield key, file_content_bytes


def iterate_files_in_bucket(bucket_name: str, prefix: str = '', verbose:bool = False, *s3_args, **s3_kwargs) -> Iterable[Tuple[FileKey, FileContent]]:
    s3 = boto3.client('s3', *s3_args, **s3_kwargs)

    # Initialize a continuation token for pagination
    continuation_token = None

    while True:
        if continuation_token:
            continuation_params = {'ContinuationToken': continuation_token}
        else:
            continuation_params = {}

        if verbose:
            print(f"[v] sending request for s3 data. continuation_token={continuation_token}")

        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, **continuation_params)

        if 'Contents' in response:
            yield from iterate_files_in_response(s3, bucket_name, response['Contents'])
        else:
            if verbose:
                print("    [v] got no Contents in response")

        # Check if there are more objects to retrieve
        if not response['IsTruncated']:
            if verbose:
                print("    [v] response is not truncated - ending while loop")

            break

        # Update the continuation token for the next iteration
        continuation_token = response['NextContinuationToken']
