import argparse
import os
import cv2
import datetime
import filetype as ft
import numpy as np
from pathlib import Path
from PIL import Image
import boto3
from io import BytesIO
from facedetector import FaceDetector

from app.s3_iterate_bucket import DEFAULT_BUCKET_NAME, iterate_files_in_bucket
from app.image_extractor import iterate_images


def getFiles(path):
    files = list()
    if os.path.isdir(path):
        dirFiles = os.listdir(path)
        for file in dirFiles:
            filePath = os.path.join(path, file)
            if os.path.isdir(filePath):
                files = files + getFiles(filePath)
            else:
                kind = ft.guess(filePath)
                basename = os.path.basename(filePath)
                files.append({
                    'dir': os.path.abspath(path),
                    'path': filePath,
                    'mime': None if kind == None else kind.mime,
                    'filename': os.path.splitext(basename)[0]
                })
    else:
        kind = ft.guess(path)
        basename = os.path.basename(path)
        files.append({
            'dir': os.path.abspath(os.path.dirname(path)),
            'path': path,
            'mime': None if kind == None else kind.mime,
            'filename': os.path.splitext(basename)[0]
        })

    return files


def upload_to_s3(image, bucket_name, folder_in_bucket, object_name, aws_access_key_id, aws_secret_access_key, aws_session_token=None):
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

        print(bucket_name, object_name, image.format)

        # Convert the PIL.Image.Image object to bytes
        image_byte_arr = BytesIO()
        image.save(image_byte_arr, format='JPEG')
        image_byte_arr = image_byte_arr.getvalue()

        presentDate = datetime.datetime.now()
        unix_timestamp = datetime.datetime.timestamp(presentDate)*1000

        # Upload the image bytes to the specified bucket with the given object name
        s3.upload_fileobj(BytesIO(image_byte_arr),
                          bucket_name, folder_in_bucket + str(int(unix_timestamp)) + ".jpg")

        print(
            f"Image '{object_name}' uploaded to '{bucket_name}' successfully.")
        return True
    except Exception as e:
        print(f"Error uploading image: {e}")
        return False


class Statistics:
    def __init__(self):
        self.total_images_iterated = 0
        self.total_faces_found = 0

def is_too_small(face):
    bbox = face['bounding_box']
    return bbox['width'] < 10 or bbox['height'] < 10

def crop_face(face):
    bbox = face['bounding_box']
    pivotX, pivotY = face['pivot']

    left = pivotX - bbox['width'] / 2.0 * padding
    top = pivotY - bbox['height'] / 2.0 * padding
    right = pivotX + bbox['width'] / 2.0 * padding
    bottom = pivotY + bbox['height'] / 2.0 * padding
    cropped = img.crop((left, top, right, bottom))
    return cropped

def build_output_file_name(source_type, file_key, image_index, face_index):
    # Todo: this function isn't working now, as `file_key` contrains '/''
    if source_type == "video":
        return '{}_{:04d}_{}.jpg'.format(
            file_key, image_index, face_index)
    else:
        return '{}_{}.jpg'.format(file_key, face_index)


def face_extractor(
    input_bucket_name: str, input_bucket_folder: str,
    output_bucket_name: str, output_bucket_folder: str,
    access_key, secret_access_key,
    verbose:bool=False,
    padding=2.5
):
    stats = Statistics()

    files_iterator = iterate_files_in_bucket(
        input_bucket_name, input_bucket_folder
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_access_key,
    )
    for image_index, (image, source_file_type, file_key) in enumerate(iterate_images(files_iterator)):
        print(f"    [*] Processing Image {image_index:4d}")
        stats.total_images_iterated += 1

        faces = FaceDetector.detect(image)
        successful_face_index = 1

        for face in faces:
            if is_too_small(face):
                continue

            cropped = crop_face(face)
            target_file_name = build_output_file_name(source_file_type, file_key, image_index, successful_face_index)

            upload_to_s3(
                cropped,
                output_bucket_name, output_bucket_folder,
                target_file_name,
                access_key, secret_access_key,
            )

            successful_face_index += 1
            stats.total_faces_found += 1

    print('=' * 50)
    print(f"Iterated {stats.total_images_iterated} images, and extracted {stats.total_faces_found} faces")


def get_parameters():
    #
    # arguments from CLI
    #
    parser = argparse.ArgumentParser(
        description="Extract faces (from s3 bucket).")
    parser.add_argument("--input-bucket-name",
                        default=DEFAULT_BUCKET_NAME,
                        help="The bucket name from which to extract faces")
    parser.add_argument("--input-bucket-folder",
                        default='',
                        help="The bucket folder from which to extract faces. Default=empty string, meaning all folders")
    parser.add_argument("--output-bucket-name",
                        help="The bucket name in which to store the results")
    parser.add_argument("--output-bucket-folder",
                        default=f"extracted_faces__{datetime.datetime.now().strftime('%Y/%m/%d_%H.%M')}",
                        help="The bucket folder in which to store the results")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    if args.verbose:
        print(f"[*] Initializing with the following arguments: {args}")

    #
    # arguments from environment variables
    #
    aws_access_key = os.getenv("aws_access_key_id")
    if aws_access_key is None:
        raise ValueError("AWS access key missing! please set the environment variable `aws_access_key_id`")

    aws_secret_key = os.getenv("aws_secret_access_key")
    if aws_secret_key is None:
        raise ValueError("AWS access key missing! please set the environment variable `aws_secret_access_key`")

    return args, aws_access_key, aws_secret_key

def main():
    args, aws_access_key, aws_secret_key = get_parameters()
    face_extractor(
        args.input_bucket_name, args.input_bucket_folder,
        args.output_bucket_name, args.output_bucket_folder,
        aws_access_key, aws_secret_key,
        args.verbose
    )

if __name__ == '__main__':
    main()
