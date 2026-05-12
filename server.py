from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import os

###
# systemdで常駐 PATH: /etc/systemd/system/photoapi.service
# 内容は _photoapi.service
#    sudo systemctl daemon-reload
#    sudo systemctl enable photoapi
#    sudo systemctl start photoapi
#    systemctl status photoapi
# リアルタイムログ確認
# journalctl -u photoapi -f
###

app = FastAPI()

UPLOAD_DIR = "uploads"
SENT_FILE = "sent.txt"

os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_sent():

    if not os.path.exists(SENT_FILE):
        return set()

    with open(SENT_FILE) as f:
        return set(
            line.strip()
            for line in f
            if line.strip()
        )

@app.get("/queue")
def queue():

    sent = get_sent()

    files = sorted(os.listdir(UPLOAD_DIR))

    unsent = [
        f for f in files
        if f not in sent
    ]

    return {"files": unsent}

@app.get("/file/{filename}")
def file(filename: str):

    path = os.path.join(UPLOAD_DIR, filename)

    return FileResponse(path)

@app.post("/mark_sent/{filename}")
def mark_sent(filename: str):

    with open(SENT_FILE, "a") as f:
        f.write(filename + "\n")

    return {"ok": True}

@app.get("/latest")
def latest():

    files = [
        os.path.join(UPLOAD_DIR, f)
        for f in os.listdir(UPLOAD_DIR)
        if os.path.isfile(os.path.join(UPLOAD_DIR, f))
    ]

    if not files:
        raise HTTPException(404, "No files")

    latest_file = max(files, key=os.path.getmtime)

    return FileResponse(latest_file)