import re
from urllib.parse import quote

import bs4
import requests

import os

ASTRODX_TESTFLIGHT = "https://testflight.apple.com/join/rACTLjPL"
ASTRODX_TESTFLIGHTS = {
    "Group A": "https://testflight.apple.com/join/rACTLjPL",
    "Group B": "https://testflight.apple.com/join/ocj3yptn",
}


def main():
    with open("README.md", newline="\n") as f:
        readme = f.read()

    statuses = {}
    for name, link in ASTRODX_TESTFLIGHTS.items():
        page = requests.get(
            link,
            headers={
                "Accept-Language": "en-us"
            }
        ).text

        soup = bs4.BeautifulSoup(page, 'html.parser')
        status_text = soup.select(".beta-status span")[0].get_text()
        if "This beta is full." in status_text:
            status = "full"
        elif "This beta isn't accepting" in status_text:
            status = "closed"
        else:
            status = "open"

        statuses[name] = status

    anyOpen = "open" in statuses.values()

    content = ""
    color = 16711680

    if anyOpen:
        content = "<@&1190732170126442557>"
        color = 65280
    
    webhookUrl = os.environ["DISCORD_WEBHOOK_URL"]

    description = []

    for name, status in statuses.items():
        description.append(name + ": " + status)

    description = "\n".join(description)

    fields = []

    for name, link in ASTRODX_TESTFLIGHTS.items():
        fields.append({
            "name": name,
            "value": value,
            "inline": True
        })

    requests.post(webhookUrl, json={
        "content": content,
        "embeds": [
            {
                "color": color,
                "description": description,
                "fields": fields
            }
        ]
    })

    


if __name__ == "__main__":
    main()

