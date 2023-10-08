# Face Extractor for Maf'at Project

This Python script is designed to extract faces from images or video frames and upload them to an AWS S3 bucket. It uses OpenCV for image and video processing, the facedetector library for face detection, and the boto3 library for AWS S3 interaction.

## Todo

- [x] Receive images from the bucket
- [ ] Make sure the same image from the bucket processed twice
- [x] Run under docker & docker-compose
- [x] Add execution configuration
- [ ] Run infinitley and wait for new files
	- It may be that S3 triggers can be processed in lambda. I don't really know about that.
	- If that is the case, we can either use lambda, or `while true: process everything all over again` (or store some kind of cache to tell which files have already been processed, e.g. an in-memory list of processed file names)

## Prerequisites

Before using this script, you need to have the following prerequisites in place:

- Python 3.x
- OpenCV
- filetype
- PIL (Python Imaging Library)
- facedetector library
- boto3 (AWS SDK for Python)
- datetime

You can install the required Python libraries using pip:

```bash
pip install -r requirements.txt
```

## Usage

1. Clone or download this repository to your local machine.

2. Navigate to the directory where the script is located.

3. Edit the `face_extractor` function call at the end of the script to specify your input source and AWS S3 bucket details:

```bash
# first, build the docker
docker build . --tag wehelpisrael-face-extractor
# then, execute:
export aws_access_key_id=...
export aws_secret_access_key=...
docker run wehelpisrael-face-extractor <input folder> <output bucket name> <output bucket folder: defaults to `date`>
```

```python
face_extractor("input_directory_or_file", "your-bucket-name", "folder-in-bucket", "your-aws-access-key", "your-aws-secret-key")
```

Replace the placeholders with the following:

- `"input_directory_or_file"`: The path to the directory containing images or a video file from which you want to extract faces.

- `"your-bucket-name"`: The name of your AWS S3 bucket.

- `"folder-in-bucket"`: The folder within your S3 bucket where the extracted faces will be uploaded.

- `"your-aws-access-key"`: Your AWS Access Key ID.

- `"your-aws-secret-key"`: Your AWS Secret Access Key.

4. Run the script:

```bash
python extract.py
```

The script will process the images or video frames, detect faces, crop them, and upload the cropped faces to the specified S3 bucket with current timestamp as the file name.

## License

This project is licensed to [UrMango](https://github.com/UrMango) under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- The facedetector library for face detection.
- The boto3 library for AWS S3 interaction.
- OpenCV and PIL for image and video processing.
