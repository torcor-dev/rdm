import logging
import requests
import re
from .posts import Gallery, Album, Image


class Requestor:
    def __init__(self, client_id, client_secret=None):
        self.client_id = client_id

    def parse_url(self, url):
        api_url = "https://api.imgur.com/3/"
        if "imgur.com" not in url:
            raise Exception("Non imgur link")
        if "/gallery/" in url:
            api_url += "gallery/"
            id = re.search("(?<=\\/gallery\\/)\\w+", url)
            api_url += id[0]
            self.type = "gallery"
        elif "/a/" in url:
            api_url += "album/"
            id = re.search("(?<=\\/a\\/)\\w+", url)
            api_url += id[0]
            self.type = "album"
        else:
            api_url += "image/"
            id = re.search("(?<=imgur.com\\/)\\w+", url)
            api_url += id[0]
            self.type = "image"
        return api_url

    def request_json(self, url):
        url = self.parse_url(url)
        headers = {"Authorization": f"Client-ID {self.client_id}"}
        return requests.request(
            "GET",
            url,
            headers=headers,
        ).json()

    def get_imgur_media(self, url):
        try:
            response = self.request_json(url)
        except Exception as e:
            logging.error(f"Imgur media error: {e}")
            return None
        if self.type == "gallery":
            return Gallery(response)
        elif self.type == "album":
            return Album(response)
        elif self.type == "image":
            return Image(response)

    def request_gallery(self, url):
        return Gallery(self.request_json(url))

    def request_album(self, url):
        return Album(self.request_json(url))

    def request_image(self, url):
        return Image(self.request_json(url))
