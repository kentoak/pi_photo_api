from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
import os
from datetime import datetime
from urllib.parse import quote, unquote
###
# systemdで常駐 PATH: /etc/systemd/system/photoapi.service
# 内容は _photoapi.service
#    sudo systemctl daemon-reload
#    sudo systemctl enable photoapi
#    sudo systemctl start photoapi
#    systemctl status photoapi
# リアルタイムログ確認
# journalctl -u photoapi -f
# http://100.117.5.28:8000/queue
# http://100.117.5.28:8000/list
###

app = FastAPI()

UPLOAD_DIR = "uploads"
SENT_FILE = "sent.txt"

os.makedirs(UPLOAD_DIR, exist_ok=True)

from hashlib import md5

# def make_map():
#     table = {}

#     for f in os.listdir(UPLOAD_DIR):
#         if "%" in f:
#             table[md5(f.encode()).hexdigest()] = f
#         else:
#             table[quote(f)] = f

#     return table

def make_map():
    table = {}

    for f in os.listdir(UPLOAD_DIR):
        table[quote(f, safe="%")] = f

    return table

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

#http://100.117.5.28:8000/queue
@app.get("/queue")
def queue():
    sent = get_sent()

    # files = sorted(os.listdir(UPLOAD_DIR))
    files = [
        f for f in os.listdir(UPLOAD_DIR)
        if os.path.isfile(os.path.join(UPLOAD_DIR, f))
    ]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(UPLOAD_DIR, f)))  # 古い順

    unsent = [
        f"http://100.117.5.28:8000/file/{quote(f)}" for f in files
        if f not in sent
    ]

    return {"files": unsent}


@app.get("/file/{key:path}")
def file(key: str):
    # key = quote(key)
    table = make_map()

    if key not in table:
        print("NOT FOUND:", key)
        return FileResponse("noimage.jpg")

    filename = table[key]
    path = os.path.join(UPLOAD_DIR, filename)

    print("filename:", repr(filename))
    print("path:", repr(path))
    print("exists:", os.path.exists(path))
    print("size:", os.path.getsize(path))

    return FileResponse(path)

@app.post("/mark_sent/{filename}")
def mark_sent(filename: str):
    filename = unquote(filename)

    if filename.startswith("http://") or filename.startswith("https://"):
        filename = filename.replace("http://100.117.5.28:8000/file/","")

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