from typing import Iterable, Tuple

FileKey = str
FileContent = bytes

def iterate_images(files_iterator: Iterable[Tuple[FileKey, FileContent]]):
	for file_index, (file_key, file_content) in enumerate(files_iterator):
        print(f"[*] Processing Image {file_index:4d}")
		# Todo:
		if is_image:
			yield some image
		elif is_video:
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
