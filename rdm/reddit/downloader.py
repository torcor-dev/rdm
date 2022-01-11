import hashlib
import os
import requests


class Downloader:
    def __init__(self, url, ext, base_path):
        self.url = url
        self.ext = ext
        self.base_path = base_path
        self.filename = ""

    def save(self):
        response = requests.get(self.url)
        if response:
            img_data = requests.get(self.url).content
        else:
            raise DownloadException

        self.filename = hashlib.sha3_256(img_data).hexdigest()
        save_path = self.generate_directory()
        save_path += f"{self.filename}.{self.ext}"

        with open(save_path, "wb") as handler:
            handler.write(img_data)

    def generate_directory(self):
        fn = self.filename
        file_path = f"{self.ext}/{fn[:2]}/{fn[2:4]}/{fn[4:6]}/"
        absolute_path = f"{self.base_path}{file_path}"

        if not os.path.exists(absolute_path):
            os.makedirs(absolute_path)

        return absolute_path

    def get_filename(self):
        return self.filename


class DownloadException(Exception):
    def __init__(self, *arg):
        super().__init__(*arg)
