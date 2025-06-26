import os
import requests


def send_lark(subject, body):
    url = os.getenv("LARK_URL")
    if not url:
        return

    data = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": subject,
                    "content": [[{"tag": "text", "text": body + "\n"}]],
                }
            }
        },
    }

    requests.post(url, json=data)
