import logging
import requests


class RedditMedia:
    MEDIA_TYPES = ["unknown", "self_post", "video", "gallery", "image"]

    def __init__(self, submission):
        self.submission = submission
        self.urls = []
        self.media_type = self.MEDIA_TYPES[0]
        self.data = {
            "urls": self.urls,
        }
        self.find_media_type()
        self.data["type"] = self.media_type

    def find_media_type(self):
        if self.submission.is_self:
            self.is_media = False
            self.media_type = self.MEDIA_TYPES[1]

        elif self.submission.is_video:
            self.is_media = True
            self.media_type = self.MEDIA_TYPES[2]
            self.set_video_url()

        elif "gallery" in self.submission.url:
            self.is_media = True
            self.media_type = self.MEDIA_TYPES[3]
            self.set_gallery_urls()

        elif self.submission.is_reddit_media_domain:
            self.is_media = True
            self.media_type = self.MEDIA_TYPES[4]
            self.urls.append(self.submission.url)

        else:
            self.is_media = False
            self.media_type = self.MEDIA_TYPES[0]

    def set_video_url(self):
        video_url = self.submission.media["reddit_video"]["fallback_url"]
        video_url = video_url[: video_url.rfind("?")]
        self.data["audio_url"] = self.get_audio_url(video_url)
        self.urls.append(video_url)

    def get_audio_url(self, video_url):
        audio_url = video_url[: video_url.rfind("/")]
        audio_url += "/DASH_audio.mp4"
        response = requests.get(audio_url)
        if response:
            return audio_url
        return None

    def set_gallery_urls(self):
        try:
            # There are some weird things that can happen with galleries.
            # Empty, deleted or bugged (?) galleries can crash us.
            # If they are crossposted we can only access
            # media metadata thorugh the original.
            if hasattr(self.submission, "crosspost_parent_list"):
                media_metadata = self.submission.crosspost_parent_list[0][
                    "media_metadata"
                ]
            else:
                media_metadata = self.submission.media_metadata

            for key in media_metadata.keys():
                image_id = media_metadata[key]["id"]
                extension = media_metadata[key]["m"].split("/")[1]
                image_url = f"https://i.redd.it/{image_id}.{extension}"
                self.urls.append(image_url)
        except Exception as e:
            logging.error(f"Error fetching gallery: {self.submission.url}\n{e}")
