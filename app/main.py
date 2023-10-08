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
from app.s3_upload import upload_to_s3


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

def build_output_file_name(source_file_extension, file_key, image_index, face_index):
    formatted_key = file_key.replace('/', '__')

    return f"{formatted_key}_from_{source_file_extension}_{image_index:04d}_{face_index}.jpg"


def face_extractor(
    input_bucket_name: str, input_bucket_folder: str,
    output_bucket_name: str, output_bucket_folder: str,
    access_key, secret_access_key,
    verbose:bool=False,
    padding=2.5
):
    stats = Statistics()

    files_iterator = iterate_files_in_bucket(
        input_bucket_name, input_bucket_folder,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_access_key,
    )
    for image_index, image_tuple in enumerate(iterate_images(files_iterator)):
        print(f"    [*] Processing Image {image_index:4d}")
        stats.total_images_iterated += 1

        faces = FaceDetector.detect(image_tuple.image)
        successful_face_index = 1

        for face in faces:
            if is_too_small(face):
                continue

            cropped = crop_face(face)
            target_file_name = build_output_file_name(
                image_tuple.source_file_extension,
                image_tuple.source_key,
                image_index,
                successful_face_index
            )

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
