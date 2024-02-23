import datetime
import requests
import json
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


def constructMessage(status: str, name: str, link: str) -> dict:
    upperCaseFirstLetter = lambda s: s[0].upper() + s[1:]
    return {
        "embeds": [
            {
                "title": f"TestFlight {name} status",
                "color": 65280 if status == "open" else 16711680,
                "fields": [
                    {
                        "name": "Status",
                        "value": upperCaseFirstLetter(status),
                        "inline": True,
                    },
                    {"name": "Link", "value": link, "inline": True},
                ],
                "timestamp": datetime.datetime.now().isoformat(),
            }
        ]
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

    for name, status in statuses.items():
        if not "messageId" in data:
            data["messageId"] = {}

        editMessage = False

        if name in data["messageId"]:
            editMessage = True

        embed = constructMessage(status, name, ASTRODX_TESTFLIGHTS[name])

        if editMessage:
            requests.patch(
                f"{discordWebhookUrl}/messages/{data['messageId'][name]}", json=embed
            )
        else:
            response = requests.post(
                f"{discordWebhookUrl}?wait=true",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=embed,
            )
            data["messageId"][name] = response.json()["id"]

    writeData(data)

if __name__ == "__main__":
    main()
