from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
import os
from datetime import datetime

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

# def get_files():
#     return sorted(
#         [
#             f for f in os.listdir(UPLOAD_DIR)
#             if os.path.isfile(os.path.join(UPLOAD_DIR, f))
#         ],

#         key=lambda f: os.path.getmtime(
#             os.path.join(UPLOAD_DIR, f)
#         ),
#         reverse=True
#     )

def get_files():
    files = []
    for f in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, f)
        if os.path.isfile(path):
            ts = os.path.getmtime(path)
            files.append({
                "name": f,
                "path": path,
                "timestamp": ts
            })

    files.sort(
        key=lambda x: x["timestamp"],
        reverse=True
    )
    return files

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
    if not os.path.isfile(path):
        raise HTTPException(404, "Not found")

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

@app.get("/list")
def list_files():
    files = get_files()
    html = """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: sans-serif;
                padding: 20px;
            }

            .item {
                margin-bottom: 20px;
            }

            img {
                max-width: 250px;
                display: block;
                margin-bottom: 5px;
            }

            .date {
                color: gray;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
    <h1>Uploads</h1>
    """
    for f in files:
        dt = datetime.fromtimestamp(
            f["timestamp"]
        ).strftime("%Y-%m-%d %H:%M:%S")
        html += f"""
        <div class="item">
            <a href="/file/{f['name']}">
                <img src="/file/{f['name']}">
            </a>
            <div>{f['name']}</div>
            <div class="date">{dt}</div>
        </div>
        """
    html += "</body></html>"
    return HTMLResponse(html)

@app.get("/gallery")
def gallery():
    files = get_files()
    html = "<h1>Gallery</h1>"
    for f in files:
        html += f"""
        <div style="margin:20px">
            <a href="/file/{f}">
                <img src="/file/{f}" width="300"><br>
                {f}
            </a>
        </div>
        """
    return HTMLResponse(html)