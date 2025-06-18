# post_to_pinterest.py
import os
import sys
import feedparser
import requests
from bs4 import BeautifulSoup

# Constants
LAST_POSTED_FILE = 'last_posted_pinterest.txt'
FEED_URL = 'https://www.etsy.com/shop/thesashedits/rss'
PIN_ACCESS_TOKEN = os.getenv('PINTEREST_PIN_ACCESS_TOKEN')
BOARD_ACCESS_TOKEN = os.getenv('PINTEREST_BOARD_ACCESS_TOKEN')
PIN_API_URL = 'https://api-sandbox.pinterest.com/v5/pins'
BOARDS_API_URL = 'https://api.pinterest.com/v5/boards'

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

def extract_price(summary):
    soup = BeautifulSoup(summary, 'html.parser')
    price_tag = soup.find('span', class_='currency-value')
    return price_tag.text.strip() if price_tag else ""

def fetch_boards():
    headers = {
        'Authorization': f'Bearer {BOARD_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    response = requests.get(BOARDS_API_URL, headers=headers)
    if response.status_code == 200:
        boards = response.json().get('items', [])
        if not boards:
            print("❌ No boards found.")
            return []
        print(f"✅ Found {len(boards)} boards.")
        return boards
    else:
        print("❌ Failed to fetch boards.", response.text)
    return []

def select_board(boards, post_title):
    title_keywords = post_title.lower().split()
    for board in boards:
        board_name = board['name'].lower()
        if any(kw in board_name for kw in title_keywords):
            print(f"Using board: {board['name']} (ID: {board['id']})")
            return board['id']
    print("No matching board found, using first available board.")
    return boards[0]['id']

def main():
    try:
        post_limit = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    except Exception:
        print("Invalid arguments. Usage: python post_to_pinterest.py <post_limit>")
        return

    boards = fetch_boards()
    if not boards:
        return

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
        title = entry.title[:99]
        summary = entry.summary

        soup = BeautifulSoup(summary, 'html.parser')
        image_tag = soup.find('img')
        image_url = image_tag['src'] if image_tag else None
        price = extract_price(summary)

        tags = extract_tags(entry)
        hashtags = ' '.join([f"#{tag.replace(' ', '')}" for tag in tags]) if tags else "#Etsy #Handmade #ShopNow"

        description = f"{title} - Editable template on Etsy!\nPrice: {price}\n\n{hashtags}"

        if not image_url:
            print(f"❌ Skipping: {title} — no image found.")
            add_posted_link(link)
            continue

        board_id = select_board(boards, title)

        payload = {
            "board_id": board_id,
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
            'Authorization': f'Bearer {PIN_ACCESS_TOKEN}',
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
            add_posted_link(link)

if __name__ == "__main__":
    main()
