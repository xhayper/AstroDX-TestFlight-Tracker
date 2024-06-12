#!/usr/bin/env python3

import datetime
import requests
import json
import time
import bs4
import os

ASTRODX_TESTFLIGHTS = {
    "Group A": "https://testflight.apple.com/join/rACTLjPL",
    "Group B": "https://testflight.apple.com/join/ocj3yptn",
    "Group C": "https://testflight.apple.com/join/CuMxZE2M",
}


def readData() -> dict:
    try:
        with open("data.json", "r") as openfile:
            return json.load(openfile)
    except FileNotFoundError:
        return {}


def writeData(data: dict):
    with open("data.json", "w+") as file:
        json.dump(data, file, indent=4)


data = readData()


def constructEmbed(status: str, name: str, link: str) -> dict:
    upperCaseFirstLetter = lambda s: s[0].upper() + s[1:]
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
        page = requests.get(link, headers={"Accept-Language": "en-us"}).text

        soup = bs4.BeautifulSoup(page, "html.parser")
        status_text = soup.select(".beta-status span")[0].get_text()
        if "This beta is full." in status_text:
            status = "full"
        elif "This beta isn't accepting" in status_text:
            status = "closed"
        else:
            status = "open"

        statuses[name] = status

    return statuses


def main():
    discordWebhookUrl = os.environ.get("DISCORD_WEBHOOK_URL")

    if discordWebhookUrl is None:
        print("DISCORD_WEBHOOK_URL environment variable not set")
        return

    statuses = getTestFlightStatuses()

    embeds = []

    for name, status in statuses.items():
        embeds.append(constructEmbed(status, name, ASTRODX_TESTFLIGHTS[name]))

    message = {
        "embeds": embeds,
    }

    editMessage = "messageId" in data

    if editMessage:
        requests.patch(
            f"{discordWebhookUrl}/messages/{data['messageId']}", json=message
        )
    else:
        response = requests.post(
            f"{discordWebhookUrl}?wait=true",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=message,
        )
        data["messageId"] = response.json()["id"]

    writeData(data)


def mainLoop():
    while True:
        try:
            print("Updating messages...")
            main()
        except:
            print("woops")     
        time.sleep(60)


if __name__ == "__main__":
    try:
        mainLoop()
    except:
        print("woops")
