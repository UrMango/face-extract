from typing import Iterable, Tuple
from collections import namedtuple

import cv2
import numpy as np

FileKey = str
FileContent = bytes

ImageType = namedtuple("ImageType", [
	"image",
	"source_file_extension",
	"source_key",
	"file_index",
	"image_index_in_file",
])

def iterate_images(files_iterator: Iterable[Tuple[FileKey, FileContent]]):
	for file_index, (file_key, file_content) in enumerate(files_iterator):
        print(f"[*] Processing Image {file_index:4d}")

        file_extension = obj['Key'].split('.')[-1].lower()

		if file_extension == "jpg":
            image_np_array = np.frombuffer(file_content, np.uint8)
            image = cv2.imdecode(image_np_array, cv2.IMREAD_COLOR)
			yield ImageType(image, file_extension, file_key, file_index, 0)

		elif file_extension == "mp4":
			yield from extract_images_from_video(...)

def old_code():	
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
