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


def face_extractor(input, bucket_name, folder_in_bucket, access_key, secret_access_key, verbose:bool=False, padding=2.5):
    files = getFiles(input)

    inputDir = os.path.abspath(os.path.dirname(input)) if os.path.isfile(
        input) else os.path.abspath(input)

    images = []
    for file in files:
        dir, path, mime, filename = file.values()

        if mime is None:
            continue
        if mime.startswith('video'):
            print('[INFO] extracting frames from video...')
            video = cv2.VideoCapture(path)
            while True:
                success, frame = video.read()
                if success and isinstance(frame, np.ndarray):
                    image = {
                        "file": frame,
                        "sourcePath": path,
                        "sourceType": "video",
                        "filename": filename
                    }
                    images.append(image)
                else:
                    break
            video.release()
            cv2.destroyAllWindows()
        elif mime.startswith('image'):
            image = {
                "file": cv2.imread(path),
                "sourcePath": path,
                "sourceType": "image",
                "filename": filename
            }
            images.append(image)

    total = 0
    for (i, image) in enumerate(images):
        print("[INFO] processing image {}/{}".format(i + 1, len(images)))
        faces = FaceDetector.detect(image["file"])

        array = cv2.cvtColor(image['file'], cv2.COLOR_BGR2RGB)
        img = Image.fromarray(array)

        j = 1
        for face in faces:
            bbox = face['bounding_box']
            pivotX, pivotY = face['pivot']

            if bbox['width'] < 10 or bbox['height'] < 10:
                continue

            left = pivotX - bbox['width'] / 2.0 * padding
            top = pivotY - bbox['height'] / 2.0 * padding
            right = pivotX + bbox['width'] / 2.0 * padding
            bottom = pivotY + bbox['height'] / 2.0 * padding
            cropped = img.crop((left, top, right, bottom))
            targetFilename = ''
            if image["sourceType"] == "video":
                targetFilename = '{}_{:04d}_{}.jpg'.format(
                    image["filename"], i, j)
            else:
                targetFilename = '{}_{}.jpg'.format(image["filename"], j)

            upload_to_s3(cropped, bucket_name, folder_in_bucket, targetFilename,
                         access_key, secret_access_key)
            # targetDir = image['targetDir']
            # if not os.path.exists(targetDir):
            #     os.makedirs(targetDir)

            # targetFilename = ''
            # if image["sourceType"] == "video":
            #     targetFilename = '{}_{:04d}_{}.jpg'.format(
            #         image["filename"], i, j)
            # else:
            #     targetFilename = '{}_{}.jpg'.format(image["filename"], j)

            # outputPath = os.path.join(targetDir, targetFilename)

            # cropped.save(outputPath)
            total += 1
            j += 1

    print("[INFO] found {} face(s)".format(total))


def get_parameters():
    #
    # arguments from CLI
    #
    parser = argparse.ArgumentParser(
        description="Extract faces (from s3 bucket).")
    parser.add_argument("input_folder",
                        help="The (local) folder (or file) from which to extract faces")
    parser.add_argument("output_bucket_name",
                        help="The bucket name in which to store the results")
    parser.add_argument("output_bucket_folder", nargs='?', default=f"extracted_faces__{datetime.datetime.now().strftime('%Y/%m/%d_%H.%M')}",
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
    face_extractor(args.input_folder, args.output_bucket_name, args.output_bucket_folder, aws_access_key, aws_secret_key, args.verbose)

if __name__ == '__main__':
    main()
