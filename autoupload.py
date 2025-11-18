import sys
import os
import json
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

def log(msg):
    print(f"[AUTOUPLOAD] {msg}")


def ensure_file(path):
    if not os.path.exists(path):
        log(f"ERROR: File not found: {path}")
        sys.exit(1)

def upload_youtube(video_path, title, caption):
    log("Uploading to YouTube...")

    creds = Credentials.from_authorized_user_file("tokens/yt_token.json")
    youtube = build("youtube", "v3", credentials=creds)

    request_body = {
        "snippet": {
            "categoryId": "22",
            "title": title,
            "description": caption
        },
        "status": {"privacyStatus": "public"}
    }

    media = MediaFileUpload(video_path, chunksize=2 * 1024 * 1024, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = request.execute()
    log(f"YouTube upload complete → Video ID: {response.get('id')}")


def upload_tiktok(video_path, caption):
    log("Uploading to TikTok...")

    token = json.load(open("tokens/tiktok_token.json"))["access_token"]
    video_bytes = open(video_path, "rb").read()

    upload_res = requests.post(
        "https://open.tiktokapis.com/v2/video/upload/",
        headers={"Authorization": f"Bearer {token}"},
        files={"video": video_bytes}
    ).json()

    upload_id = upload_res.get("upload_id")
    log(f"TikTok upload ID: {upload_id}")

    publish_res = requests.post(
        "https://open.tiktokapis.com/v2/video/publish/",
        headers={"Authorization": f"Bearer {token}"},
        json={"upload_id": upload_id, "text": caption}
    ).json()

    log(f"TikTok publish result: {publish_res}")

def upload_facebook(video_path, caption):
    log("Uploading to Facebook...")

    access_token = open("tokens/meta_token.txt").read().strip()
    page_id = open("tokens/fb_page_id.txt").read().strip()

    url = f"https://graph-video.facebook.com/v19.0/{page_id}/videos"

    files = {"source": open(video_path, "rb")}
    data = {"description": caption, "access_token": access_token}

    res = requests.post(url, files=files, data=data).json()
    log(f"Facebook upload result: {res}")

def upload_instagram(video_url, caption):
    log("Uploading to Instagram...")

    access_token = open("tokens/meta_token.txt").read().strip()
    ig_user_id = open("tokens/ig_user_id.txt").read().strip()

    create = requests.post(
        f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
        data={"video_url": video_url, "caption": caption, "media_type": "REELS"},
        params={"access_token": access_token}
    ).json()

    creation_id = create.get("id")
    log(f"Instagram creation ID: {creation_id}")

    publish = requests.post(
        f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
        data={"creation_id": creation_id},
        params={"access_token": access_token}
    ).json()

    log(f"Instagram publish result: {publish}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python autoupload.py <video_path> <captions_json_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    captions_path = sys.argv[2]

    ensure_file(video_path)
    ensure_file(captions_path)

    captions = json.load(open(captions_path))

    yt_title = captions.get("title", "My Video")
    yt_caption = captions.get("youtube", "")
    ig_caption = captions.get("instagram", "")
    tt_caption = captions.get("tiktok", "")
    fb_caption = captions.get("facebook", "")
    ig_video_url = captions.get("instagram_video_url", None)

    log("Starting uploads...")

    upload_youtube(video_path, yt_title, yt_caption)
    upload_tiktok(video_path, tt_caption)
    upload_facebook(video_path, fb_caption)

    # Instagram requires public video URL
    if ig_video_url:
        upload_instagram(ig_video_url, ig_caption)
    else:
        log("Instagram skipped → no public video URL provided in captions.json")

    log("All uploads completed!")


if __name__ == "__main__":
    main()
