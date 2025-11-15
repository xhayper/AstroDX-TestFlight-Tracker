import datetime
import json
import time
import sys
import os
import requests
import bs4

ASTRODX_TESTFLIGHTS = {
    "Group A": "https://testflight.apple.com/join/d7rx8Gce",
    "Group B": "https://testflight.apple.com/join/vZkqCBaW",
    "Group C": "https://testflight.apple.com/join/6ySgqPyW",
    "Group D": "https://testflight.apple.com/join/71vbKTKq",
    "Group E": "https://testflight.apple.com/join/AYFe4Qyh",
    "Group F": "https://testflight.apple.com/join/yFhEejR9",
    "Group G": "https://testflight.apple.com/join/d67RmvFG",
    "Group H": "https://testflight.apple.com/join/taNXJKTM",
}


def readData() -> dict:
    try:
        with open("data.json", "r", encoding="utf-8") as openfile:
            return json.load(openfile)
    except FileNotFoundError:
        return {}


def writeData(data: dict):
    with open("data.json", "w+", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def constructEmbed(status: str, name: str, link: str) -> dict:
    def upperCaseFirstLetter(s): return s[0].upper() + s[1:]
    return {
        "title": f"TestFlight {name} status",
        "color": 65280 if status == "open" else 16711680,
        "thumbnail": {
            "url": "https://is1-ssl.mzstatic.com/image/thumb/Purple116/v4/76/51/3a/76513ae3-9498-ae0a-83e0-787a90f763f9/AppIcon-0-0-1x_U007emarketing-0-7-0-85-220.png/1920x1080bb-80.png"
        },
        "fields": [
            {
                "name": "Status",
                "value": upperCaseFirstLetter(status),
                "inline": True,
            },
            {"name": "Link", "value": link, "inline": True},
        ],
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
    }


def getTestFlightStatuses() -> dict[str, str]:
    statuses = {}

    for name, link in ASTRODX_TESTFLIGHTS.items():
        page = requests.get(
            link, headers={"Accept-Language": "en-us"}, timeout=5).text

        soup = bs4.BeautifulSoup(page, "html.parser")
        status_text = soup.select(".beta-status span")

        if len(status_text) == 0:
            statuses[name] = "unknown"
            continue

        status_text = status_text[0].get_text()
        if "This beta is full." in status_text:
            status = "full"
        elif "This beta isn't accepting" in status_text:
            status = "closed"
        else:
            status = "open"

        statuses[name] = status

    return statuses


def main():
    data = readData()
    discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if discord_webhook_url is None:
        print("DISCORD_WEBHOOK_URL environment variable not set")
        return

    statuses = getTestFlightStatuses()

    embeds = []

    for name, status in statuses.items():
        embeds.append(constructEmbed(status, name, ASTRODX_TESTFLIGHTS[name]))

    message = {
        "embeds": embeds,
    }

    edit_message = "messageId" in data

    if edit_message:
        requests.patch(
            f"{discord_webhook_url}/messages/{data['messageId']}", json=message, timeout=5
        )
    else:
        response = requests.post(
            f"{discord_webhook_url}?wait=true",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=message,
            timeout=5
        )
        data["messageId"] = response.json()["id"]

    writeData(data)


def mainLoop():
    while True:
        try:
            print("Updating messages...")
            main()
        except KeyboardInterrupt:
            sys.exit(130)
        time.sleep(60)


if __name__ == "__main__":
    try:
        mainLoop()
    except KeyboardInterrupt:
        sys.exit(130)
