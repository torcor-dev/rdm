from .imgur_api_wrapper.imgur import Imgur
from .imgur_api_wrapper.imgurmedia import ImgurMedia
from .redditmedia import RedditMedia
from .downloader import Downloader, DownloadException
from PIL import Image
from pyaml import yaml
import datetime
import ffmpeg
import logging
import json
import praw
import os


class Reddit:
    IMAGE_TYPES = ["jpg", "jpeg", "png", "gif"]
    VIDEO_TYPES = ["mp4", "webm", "gifv", "mkv"]
    THUMBNAIL_SIZE = 256

    def __init__(
        self,
        praw_config="bot1",
        user_agent="testing_api_idk",
        config="config.yaml",
        *args,
        **kwargs,
    ):
        with open(config, "r") as f:
            config_file = yaml.load(f, Loader=yaml.Loader)

        self.previous_timestamp = self.get_timestamp(config)

        self.save_path = config_file["save_path"]
        if not os.path.exists(self.save_path):
            os.mkdir(self.save_path)

        self.log_setup(logging.WARNING)
        self.directory_structure = config_file["directory_structure"]
        self.subreddits = config_file["subreddits"]
        self.listing = config_file["listing"]
        self.number_of_posts = config_file["number_of_posts"]
        self.reddit = praw.Reddit(praw_config, user_agent=user_agent)
        self.imgur = Imgur()
        self.cur_post = None
        self.data = []

    def get_timestamp(self, config_name):
        config_name = config_name.split(".")[0]
        self.timestamp_file = f"{config_name}_timestamp"
        if os.path.exists(self.timestamp_file):
            with open(self.timestamp_file, "r") as f:
                return f.read().rstrip("\n")
        else:
            with open(self.timestamp_file, "w") as f:
                f.write("0")
        return 0

    def fetch_media(self, submission):
        if "imgur" in submission.url:
            self.imgur.set_media(submission.url)
            media = ImgurMedia(self.imgur.media)
        elif "redd.it" in submission.url or "reddit.com" in submission.url:
            media = RedditMedia(submission)
        else:
            media = None

        return media

    def handle_media(self, submission):
        media = self.fetch_media(submission)
        if not media:
            raise NoMediaException

        files = []
        for url in media.urls:
            ext = self.parse_extension(url)
            if ext in self.IMAGE_TYPES or ext in self.VIDEO_TYPES:
                downloader = Downloader(url, ext, self.save_path)
                try:
                    downloader.save()
                    filename = downloader.get_filename()
                    file_info = (filename, ext)
                    files.append(file_info)
                except DownloadException:
                    logging.warning(f"Could not download file: {url}")
        if not files:
            raise NoMediaException

        return files

    def handle_files(self, files):
        file_info = {}
        for file in files:
            file_data = {}
            file_path = self.generate_file_path(file)
            if file[1] in self.IMAGE_TYPES:
                img = Image.open(file_path)

                file_data["type"] = "image"
                file_data["width"] = img.width
                file_data["height"] = img.height
                file_data["aspect_ratio"] = img.width / img.height

                self.create_image_thumbnail(img, file)

            elif file[1] in self.VIDEO_TYPES:
                mov = ffmpeg.probe(file_path)

                file_data["type"] = "video"
                file_data["width"] = mov["streams"][0]["width"]
                file_data["height"] = mov["streams"][0]["height"]
                file_data["aspect_ratio"] = file_data["width"] / file_data["height"]
                file_data["duration"] = mov["streams"][0]["duration"]
                file_data["frame_rate"] = mov["streams"][0]["avg_frame_rate"]

                self.create_video_thumbnail(file_path)

            else:
                continue

            file_data["file_name"] = file[0]
            file_data["format"] = file[1]
            file_data["size"] = os.path.getsize(file_path)
            file_info[file[0]] = file_data

        return file_info

    def create_video_thumbnail(self, file):
        try:
            (
                ffmpeg.input(filename=file, ss=0.1)
                .filter("scale", self.THUMBNAIL_SIZE, -1)
                .output(self.generate_file_path(file, thumbnail=True), vframes=1)
                .overwrite_output()
                .run(quiet=True)
            )
        except Exception as e:
            logging.error(f"Could not generate thumbnail.\nError: {e}")

    def create_image_thumbnail(self, img, file):
        try:
            thumb_path = self.generate_file_path(file, thumbnail=True)
            size = self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.thumbnail(size)
            img.save(thumb_path)
        except Exception as e:
            logging.error(f"Could not generate thumbnail.\nError: {e}")

    def generate_file_path(self, file, thumbnail=False, delete=False):
        file_directories = f"{file[0][:2]}/{file[0][2:4]}/{file[0][4:6]}/"
        if thumbnail:
            prefix = "thumbs"
            ext = "jpg"
        else:
            prefix = file[1]
            ext = file[1]

        file_path = f"{prefix}/{file_directories}"
        absolute_path = f"{self.save_path}{file_path}{file[0]}.{ext}"

        if not delete:
            if not os.path.exists(self.save_path + file_path):
                os.makedirs(self.save_path + file_path)

        return absolute_path

    def parse_extension(self, url):
        ext = url.split(".")[-1:][0].lower()
        if ext == "jpeg":
            ext = "jpg"
        return ext

    def track_stats(method):
        from functools import wraps

        @wraps(method)
        def wrapper(self):
            start_time = datetime.datetime.utcnow().timestamp()
            method(self)
            endtime = datetime.datetime.utcnow().timestamp()
            time_taken = endtime - start_time
            time_taken = "{0:02.0f} minutes {1:02.0f} seconds".format(
                *divmod(time_taken, 60)
            )
            print("\nFinished downloading submissions.")
            print("Total submissions downloaded:", len(self.data))
            print("Total subreddits scanned:", len(self.subreddits))
            print(f"Time taken: {time_taken}")

            logging.info(
                f"Downloads: {len(self.data)}. Subreddits: {len(self.subreddits)}. Time taken: {time_taken}."
            )

        return wrapper

    @track_stats
    def get_posts(self):
        count = 0
        for subreddit in self.subreddits:
            subreddit = self.reddit.subreddit(subreddit)
            if not self.subreddit_is_accessible(subreddit):
                continue

            logging.info(f"Scanning {subreddit.display_name}")
            count += 1
            print(
                f"Scanning {subreddit.display_name}, {count}/{len(self.subreddits)}\033[K",
                end="\r",
            )

            listing = getattr(subreddit, self.listing, subreddit.hot)
            for submission in listing(limit=self.number_of_posts):
                if submission.stickied:
                    continue
                if submission.created < float(self.previous_timestamp):
                    continue
                try:
                    msg = f"Submission: {submission.id} - "
                    files = self.handle_media(submission)
                    file_info = self.handle_files(files)
                    file_info["reddit_meta_data"] = self.collect_reddit_meta_data(
                        submission
                    )
                    self.data.append(file_info)
                    msg += f"saved {file_info['reddit_meta_data']['title']}"
                    logging.info(msg)
                except NoMediaException:
                    msg += "No valid media."
                    logging.info(msg)

    def subreddit_is_accessible(self, subreddit):
        try:
            subreddit.subreddit_type
        except Exception as e:
            logging.error(
                f"Could not access subreddit: {subreddit.display_name}\nError: {e}"
            )
            return False
        return True

    def collect_reddit_meta_data(self, submission):
        meta = {}
        meta["id"] = submission.id
        if submission.author:
            meta["author"] = submission.author.name
        else:
            meta["author"] = "deleted"
        meta["subreddit"] = submission.subreddit.display_name
        meta["title"] = submission.title
        meta["url"] = submission.url
        meta["created"] = submission.created_utc
        meta["permalink"] = submission.permalink
        meta["score"] = submission.score

        return meta

    def yaml_dump(self):
        dump_file = self.generate_dump_file("yaml")
        with open(dump_file, "w") as f:
            yaml.dump(self.data, f, Dumper=yaml.SafeDumper)
        return dump_file

    def json_dump(self):
        dump_file = self.generate_dump_file("json")
        with open(dump_file, "w") as f:
            json.dump(self.data, f)
        return dump_file

    def get_dump_directory(self, save_format):
        return f"{self.save_path}dumps/{save_format}/"

    def generate_dump_file(self, save_format):
        base_directory = self.get_dump_directory(save_format)
        time = datetime.datetime.now()
        directory = f"{base_directory}{time.year}/{time.month}/"
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_name = time.strftime("%d_%H_%M_%S") + "." + save_format
        dump_file = directory + file_name
        return dump_file

    def generate_new_timestamp(self):
        with open(self.timestamp_file, "w") as f:
            new_timestamp = datetime.datetime.utcnow().timestamp() - 1800
            f.write(str(new_timestamp))

    def log_setup(self, level):
        directory = f"{self.save_path}logs/"
        time = datetime.datetime.now()
        if not os.path.exists(directory):
            os.makedirs(directory)

        logging.basicConfig(
            filename=f"{directory}reddit_{time.year}.log",
            encoding="utf-8",
            level=level,
            format=("%(asctime)s %(name)s - %(levelname)s: %(message)s"),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def add_subbreddit(self, subreddit):
        self.subreddits.append(subreddit)


class NoMediaException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
