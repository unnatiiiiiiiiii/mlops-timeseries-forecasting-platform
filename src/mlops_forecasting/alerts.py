import json
import os
from urllib import request


def send_slack_alert(message: str) -> None:
    webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        return

    data = json.dumps({"text": message}).encode("utf-8")
    req = request.Request(webhook, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=10):
        pass
