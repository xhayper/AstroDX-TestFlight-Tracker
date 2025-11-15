import json
import time
import sys
import os
import requests
import bs4

ASTRODX_TESTFLIGHTS = {
    "Group A (Kumoumi)": "https://testflight.apple.com/join/d7rx8Gce",
    "Group B (Kumoumi)": "https://testflight.apple.com/join/vZkqCBaW",
    "Group C (Kumoumi)": "https://testflight.apple.com/join/6ySgqPyW",
    "Group D (Kumoumi)": "https://testflight.apple.com/join/71vbKTKq",
    "Group E (Kumoumi)": "https://testflight.apple.com/join/AYFe4Qyh",
    "Group F (Kumoumi)": "https://testflight.apple.com/join/yFhEejR9",
    "Group G (Kumoumi)": "https://testflight.apple.com/join/d67RmvFG",
    "Group H (Kumoumi)": "https://testflight.apple.com/join/taNXJKTM",
    "Group A (Jinale)": "https://testflight.apple.com/join/rACTLjPL",
    "Group B (Jinale)": "https://testflight.apple.com/join/ocj3yptn",
    "Group C (Jinale)": "https://testflight.apple.com/join/CuMxZE2M",
    "Group D (Jinale)": "https://testflight.apple.com/join/T6qKfV6f",
    "Group E (Jinale)": "https://testflight.apple.com/join/sMm1MCYc",
}


def read_data() -> dict:
    try:
        with open("data.json", "r", encoding="utf-8") as openfile:
            return json.load(openfile)
    except FileNotFoundError:
        return {}


def write_data(data: dict):
    with open("data.json", "w+", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def create_message(status: str, name: str, link: str) -> str:
    return f"TestFlight {name}: {'🔴' if status != 'open' else '🟢'} {status.title()} | <{link}>"


def getTestFlightStatuses() -> dict[str, str]:
    statuses = {}

    for name, link in ASTRODX_TESTFLIGHTS.items():
        page = requests.get(
            link, headers={"Accept-Language": "en-us"}, timeout=5).text

        soup = bs4.BeautifulSoup(page, "html.parser")
        status_text = soup.select(".beta-status span")

        if len(status_text) == 0:
            statuses[name] = "unknown"
            time.sleep(.5)
            continue

        status_text = status_text[0].get_text()
        if "This beta is full." in status_text:
            status = "full"
        elif "This beta isn't accepting" in status_text:
            status = "closed"
        else:
            status = "open"

        statuses[name] = status

        time.sleep(.5)

    return statuses


def main():
    data = read_data()
    discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if discord_webhook_url is None:
        print("DISCORD_WEBHOOK_URL environment variable not set")
        return

    statuses = getTestFlightStatuses()

    messages = map(lambda x: create_message(
        x[1], x[0], ASTRODX_TESTFLIGHTS[x[0]]), statuses.items())
    message = {
        "embeds": [],
        "content": "\n".join(messages) +
        f"\n\n-# Last updated: <t:{round(time.time())}>"
    }

    edit_message = "messageId" in data

    if edit_message:
        response = requests.patch(
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

    write_data(data)


def main_loop():
    while True:
        try:
            print("Updating messages...")
            main()
            print("Done!")
        except KeyboardInterrupt:
            sys.exit(130)
        time.sleep(60)


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        sys.exit(130)
