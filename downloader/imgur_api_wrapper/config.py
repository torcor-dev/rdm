import yaml
import os

credential_file = os.path.join(os.environ["SECRETS"], "imgur.yaml")
with open(credential_file, "r") as f:
    SECRETS = yaml.load(f, Loader=yaml.Loader)

CLIENT_ID = SECRETS["client_id"]
CLIENT_SECRET = SECRETS["client_secret"]
