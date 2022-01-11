from rdm.reddit.reddit import Reddit
from pathlib import Path
import logging
import os
import psycopg2
import yaml


class DownloadManager:
    def __init__(self, config=None):
        if config:
            self.reddit = Reddit(config=config)
        else:
            self.reddit = Reddit()
        self.sql_errors = 0
        self.total_posts = 0

    def get_posts(self):
        try:
            self.reddit.get_posts()
            self.reddit.generate_new_timestamp()
        finally:
            self.dump_file = self.reddit.yaml_dump()

    def connect_to_db(self):
        filepath = str(Path.home())
        filepath += "/.secrets/database.yaml"
        with open(filepath, "r") as sf:
            SECRETS = yaml.load(sf, Loader=yaml.Loader)

        db = psycopg2.connect(
            dbname=SECRETS["name"],
            user=SECRETS["user"],
            password=SECRETS["password"],
            host=SECRETS["host"],
        )

        return db

    def execute_sql(self, sql, values):
        db = self.connect_to_db()
        with db:
            with db.cursor() as cur:
                try:
                    cur.execute(sql, values)
                except Exception as e:
                    self.sql_errors += 1
                    logging.warning(e)

    def get_id(self, sql, values=None):
        db = self.connect_to_db()
        with db:
            with db.cursor() as cur:
                try:
                    cur.execute(sql, values)
                    id = int(cur.fetchone()[0])
                    return id
                except Exception as e:
                    logging.error(e)
                    self.sql_errors += 1
                    return None

    def get_file(self, sql, values=None):
        db = self.connect_to_db()
        with db:
            with db.cursor() as cur:
                try:
                    cur.execute(sql, values)
                    file = cur.fetchone()
                    print(file)
                    return file
                except Exception as e:
                    logging.error(e)
                    self.sql_errors += 1
                    return None

    def update_db(self, dump_file):
        with open(dump_file, "r") as f:
            dump = yaml.load(f, Loader=yaml.Loader)
        self.total_posts = len(dump)
        count = 0
        for i in dump:
            for k, v in i.items():
                if k != "reddit_meta_data":
                    self.insert_media(v)
                else:
                    self.insert_reddit_meta(v)
            self.insert_post(i)
            count += 1

            print(
                f"Posts: {count}/{self.total_posts}\033[K",
                end="\r",
            )

    def insert_post(self, post):
        id_select_sql = "select id from reddit_meta where reddit_id = %s"
        id_select_value = (post["reddit_meta_data"]["id"],)
        reddit_id = self.get_id(id_select_sql, id_select_value)

        for key in post:
            if key == "reddit_meta_data":
                continue
            else:
                media_id = self.get_id(
                    "select id from media where file_name = %s",
                    (post[key]["file_name"],),
                )

            if reddit_id and media_id:
                self.execute_sql(
                    "insert into post_link values(%s, %s)", (media_id, reddit_id)
                )

    def insert_reddit_meta(self, values):
        self.execute_sql(
            """
            insert into reddit_meta
            (author, created, reddit_id, permalink, score, subreddit, title, url)
            values(%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                values["author"],
                values["created"],
                values["id"],
                values["permalink"],
                values["score"],
                values["subreddit"],
                values["title"],
                values["url"],
            ),
        )

    def insert_media(self, values):
        self.execute_sql(
            """insert into media
                (file_name, format, height, width, aspect_ratio, media_type, size)
                values(%s, %s, %s, %s, %s, %s, %s)
                """,
            (
                values["file_name"],
                values["format"],
                values["height"],
                values["width"],
                values["aspect_ratio"],
                values["type"],
                values["size"],
            ),
        )

        if values["type"] == "video":
            media_id = self.get_id("select max(id) from media")
            self.execute_sql(
                """insert into video (media_id, frame_rate, duration)
                    values(%s, %s, %s)""",
                (media_id, values["frame_rate"], values["duration"]),
            )

    def remove_media(self, file_name):
        sql = "select file_name, format from media where file_name=%s"
        file = self.get_file(sql, file_name)
        if not file:
            raise Exception("filename not found")
        filepath = self.reddit.generate_file_path(file, delete=True)
        thumb_path = self.reddit.generate_file_path(file, thumbnail=True, delete=True)

        try:
            os.remove(filepath)
            os.remove(thumb_path)
            print(file[0], "successfully removed from disk.")
            logging.info(file[0], "successfully removed from disk.")
        except OSError as e:
            print(e)
            logging.error(e)

        sql = "delete from media where file_name=%s"
        self.execute_sql(sql, file_name)

    def import_all_yaml_dumps(self, root_dir):
        for directory, subdir, files in os.walk(root_dir):
            print(directory, ":")
            for file in files:
                print(file, ":")
                self.update_db(os.path.join(directory, file))


if __name__ == "__main__":
    dm = DownloadManager(config="config.yaml")
    dm.get_posts()
    dm.update_db(dm.dump_file)

    print(f"Total posts: {dm.total_posts}")
    print(f"SQL Errors: {dm.sql_errors}")
