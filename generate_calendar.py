from datetime import datetime, timezone
import requests
import os

from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
DATASOURCE_ID = os.environ["NOTION_DATASOURCE_ID"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json",
}


def check_auth():
    url = "https://api.notion.com/v1/users"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["results"]


def fetch_database():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def fetch_events():
    url = f"https://api.notion.com/v1/data_sources/{DATASOURCE_ID}/query"
    response = requests.post(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["results"]


def format_dt(dt_str):
    # Notion returns ISO strings; ICS wants UTC in YYYYMMDDTHHMMSSZ
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def generate_ics(events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//DnB Events//Subscribed Calendar//EN",
    ]

    for e in events:
        props = e["properties"]

        title = props["Event Name"]["title"][0]["plain_text"]
        uid = props["ID"]["unique_id"]["number"]

        date = props["Date"]['date']
        start = format_dt(date["start"])
        end = format_dt(date.get("end"))

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{format_dt(datetime.utcnow().isoformat())}",
            f"DTSTART:{start}",
        ])

        if end:
            lines.append(f"DTEND:{end}")

        lines.append(f"SUMMARY:{title}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


if __name__ == "__main__":
    events = fetch_events()
    ics_text = generate_ics(events)
    with open("calendar.ics", "w", encoding="utf-8") as f:
        f.write(ics_text)
