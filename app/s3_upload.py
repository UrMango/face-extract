import boto3
from io import BytesIO
import datetime


def upload_to_s3(
    image,
    bucket_name: str, folder_in_bucket: str,
    object_name: str,
    aws_access_key_id, aws_secret_access_key, aws_session_token=None,
    verbose: bool = False
):
    """
    Uploads a PIL.Image.Image object to an S3 bucket using AWS IAM credentials.

    Args:
        image (PIL.Image.Image): The PIL.Image.Image object to upload.
        bucket_name (str): The name of the S3 bucket to upload the image to.
        object_name (str): The name to give to the uploaded image in the S3 bucket.
        aws_access_key_id (str): AWS Access Key ID.
        aws_secret_access_key (str): AWS Secret Access Key.
        aws_session_token (str, optional): AWS Session Token for temporary credentials.

    Returns:
        bool: True if the upload was successful, False otherwise.
    """
    try:
        # Create an S3 client with IAM credentials
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )

        if verbose:
            print(f"        [*] Attempting to upload: '{object_name}' , {image.format}")

        # Convert the PIL.Image.Image object to bytes
        image_byte_arr = BytesIO()
        image.save(image_byte_arr, format='JPEG')
        image_byte_arr = image_byte_arr.getvalue()

        # folder_in_bucket is guarenteed to end with '/' due to line 111 in main,py in the argparse section
        output_file_name = f"{folder_in_bucket}{datetime.datetime.now().isoformat().replace(':','_')}.jpg"
        presentDate = datetime.datetime.now()
        unix_timestamp = datetime.datetime.timestamp(presentDate)*1000

        # Upload the image bytes to the specified bucket with the given object name
        s3.upload_fileobj(
            BytesIO(image_byte_arr),
            bucket_name,
            output_file_name,
        )

        if verbose:
            print(f"    [*] Image '{object_name}' uploaded to '{bucket_name}' as '{output_file_name}' successfully.")
        return True
    except Exception as e:
        print(f"Error uploading image: {e}")
        return False
