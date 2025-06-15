# post_to_pinterest.py
import os
import feedparser
import requests
from bs4 import BeautifulSoup

# Constants
LAST_POSTED_FILE = 'last_posted_facebook.txt'
FEED_URL = 'https://www.etsy.com/shop/thesashedits/rss'
BOARD_ID = os.getenv('PINTEREST_BOARD_ID')
ACCESS_TOKEN = os.getenv('PINTEREST_ACCESS_TOKEN')
PIN_API_URL = 'https://api.pinterest.com/v5/pins'

# Read last posted links from file
def get_last_posted_links():
    if not os.path.exists(LAST_POSTED_FILE):
        return set()
    with open(LAST_POSTED_FILE, 'r') as file:
        return set(file.read().splitlines())

# Save new posted link to file
def add_posted_link(link):
    with open(LAST_POSTED_FILE, 'a') as file:
        file.write(link + '\n')

# Extract tags from RSS entry
def extract_tags(entry):
    return [tag.term for tag in entry.tags] if 'tags' in entry else []

def main():
    posted_links = get_last_posted_links()
    feed = feedparser.parse(FEED_URL)
    new_posts = [entry for entry in feed.entries if entry.link not in posted_links]

    if not new_posts:
        print("No new posts. Skipping.")
        return

    print(f"Found {len(new_posts)} new post(s)! Posting to Pinterest...")

    for entry in reversed(new_posts):
        link = entry.link
        title = entry.title
        summary = entry.summary

        # Extract image from summary HTML
        soup = BeautifulSoup(summary, 'html.parser')
        image_tag = soup.find('img')
        image_url = image_tag['src'] if image_tag else None

        tags = extract_tags(entry)
        hashtags = ' '.join([f"#{tag.replace(' ', '')}" for tag in tags]) if tags else "#Etsy #Handmade #ShopNow"

        description = f"{summary}\n\n{hashtags}"

        if not image_url:
            print(f"❌ Skipping: {title} — no image found.")
            continue

        payload = {
            "board_id": BOARD_ID,
            "title": title,
            "description": description,
            "alt_text": title,
            "link": link,
            "media_source": {
                "source_type": "image_url",
                "url": image_url
            }
        }

        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }

        response = requests.post(PIN_API_URL, json=payload, headers=headers)

        if response.status_code == 201:
            print(f"✅ Pin created: {title}")
            add_posted_link(link)
        else:
            print(f"❌ Failed to post: {title}. Status code: {response.status_code}")
            print(response.json())

if __name__ == "__main__":
    main()
