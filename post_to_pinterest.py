# post_to_pinterest.py
import os
import feedparser
import requests
from bs4 import BeautifulSoup

# Constants
LAST_POSTED_FILE = 'last_posted_pinterest.txt'
FEED_URL = 'https://www.etsy.com/shop/thesashedits/rss'
BOARD_ID = os.getenv('PINTEREST_BOARD_ID')
ACCESS_TOKEN = os.getenv('PINTEREST_ACCESS_TOKEN')
PIN_API_URL = 'https://api-sandbox.pinterest.com/v5/pins'  # Use sandbox for trial apps

# Ensure the last posted file exists
def ensure_last_posted_file():
    if not os.path.exists(LAST_POSTED_FILE):
        with open(LAST_POSTED_FILE, 'w') as file:
            file.write('')

# Read all posted links from file
def get_last_posted_links():
    ensure_last_posted_file()
    with open(LAST_POSTED_FILE, 'r') as file:
        return set(file.read().splitlines())

# Save new posted link to file (if not already present)
def add_posted_link(link):
    posted = get_last_posted_links()
    if link not in posted:
        with open(LAST_POSTED_FILE, 'a') as file:
            file.write(link + '\n')

# Extract tags from RSS entry
def extract_tags(entry):
    return [tag.term for tag in entry.tags] if 'tags' in entry else []

def main():
    post_limit = 1  # fixed to 1 per run

    posted_links = get_last_posted_links()
    feed = feedparser.parse(FEED_URL)
    new_posts = [entry for entry in feed.entries if entry.link not in posted_links]

    if not new_posts:
        print("No new posts. Skipping.")
        return

    print(f"Found {len(new_posts)} new post(s)! Posting up to {post_limit} pin(s) to Pinterest...")

    posted_count = 0

    for entry in reversed(new_posts):
        if posted_count >= post_limit:
            break

        link = entry.link
        title = entry.title[:99]  # Pinterest max 100 chars
        summary = entry.summary

        # Extract image from summary HTML
        soup = BeautifulSoup(summary, 'html.parser')
        image_tag = soup.find('img')
        image_url = image_tag['src'] if image_tag else None

        tags = extract_tags(entry)
        hashtags = ' '.join([f"#{tag.replace(' ', '')}" for tag in tags]) if tags else "#Etsy #Handmade #ShopNow"

        description = f"{title} - Editable template on Etsy!\n\n{hashtags}"

        if not image_url:
            print(f"❌ Skipping: {title} — no image found.")
            add_posted_link(link)
            continue

        payload = {
            "board_id": BOARD_ID,
            "title": title,
            "description": description[:490],
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

        print("\n📦 Payload:", payload)

        response = requests.post(PIN_API_URL, json=payload, headers=headers)

        if response.status_code == 201:
            print(f"✅ Pin created: {title}")
            add_posted_link(link)
            posted_count += 1
        else:
            print(f"❌ Failed to post: {title}. Status code: {response.status_code}")
            try:
                print("Response:", response.json())
            except:
                print("Raw Response:", response.text)
            # Still record to avoid retry loop
            add_posted_link(link)

if __name__ == "__main__":
    main()
