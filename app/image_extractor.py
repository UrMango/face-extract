from typing import Iterable, Tuple
from collections import namedtuple

import cv2
import numpy as np
import filetype as ft
from PIL import Image
import tempfile

FileKey = str
FileContent = bytes

ImageType = namedtuple("ImageType", [
    "image",
    "source_file_extension",
    "source_file_type",
    "source_key",
    "file_index",
    "image_index_in_file",
])

def iterate_images(files_iterator: Iterable[Tuple[FileKey, FileContent]]):
    for file_index, (file_key, file_content) in enumerate(files_iterator):
        print(f"[*] Processing Image {file_index:4d}")

        file_extension = file_key.split('.')[-1].lower()
        file_kind = ft.guess(file_content)

        if file_extension == "jpg":
            image_np_array = np.frombuffer(file_content, np.uint8)
            image_array = cv2.imdecode(image_np_array, cv2.IMREAD_COLOR)
            image = Image.fromarray(image_array)
            yield ImageType(image, file_extension, file_kind, file_key, file_index, 0)

        elif file_extension == "mp4":
            with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_file:
                temp_file.write(file_content_bytes)
                temp_file.seek(0)

                # Open the video using cv2.VideoCapture
                video_capture = cv2.VideoCapture(temp_file.name, cv2.CAP_FFMPEG)

                frame_index = 0
                while True:
                    ret, frame = video_capture.read()
                    if not ret:
                        break

                    image = Image.fromarray(frame)
                    yield ImageType(frame, file_extension, file_kind, file_key, file_index, frame_index)
                    frame_index += 1

                video_capture.release()
                cv2.destroyAllWindows()
