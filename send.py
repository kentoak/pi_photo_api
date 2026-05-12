import requests

SERVER = "http://100.117.5.28:8000"

with open("wallpaper.heic", "rb") as f:
    requests.post(
        SERVER + "/upload",
        files={"file": f}
    )