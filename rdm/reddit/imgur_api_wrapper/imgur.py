from rdm.resources.config import CLIENT_ID
from rdm.reddit.imgur_api_wrapper.requestor import Requestor


class Imgur:
    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id or CLIENT_ID
        self.requestor = Requestor(self.client_id)

    def set_media(self, url):
        self.media = self.requestor.get_imgur_media(url)
        return self.media

    def get_meta_data(self):
        pass
