class ImgurMedia:
    MEDIA_TYPES = ["unknown", "video", "gallery", "image"]

    def __init__(self, media):
        self.media = media
        self.urls = []
        self.media_type = self.MEDIA_TYPES[0]
        self.data = {
            "urls": self.urls,
        }
        if self.media:
            self.find_media_type()
        self.data["type"] = self.media_type

    def find_media_type(self):
        if self.media.type.startswith("video"):
            self.media_type = self.MEDIA_TYPES[1]
            self.urls.append(self.media.link)
        elif self.media.type.startswith("image"):
            self.media_type = self.MEDIA_TYPES[3]
            self.urls.append(self.media.link)
        elif self.media.type == "gallery" or self.media.type == "album":
            self.media_type = self.MEDIA_TYPES[2]
            for img in self.media.images:
                self.urls.append(img.link)
