# post_to_facebook.py
import os
import sys
import feedparser
import requests
from bs4 import BeautifulSoup

# Constants
LAST_POSTED_FILE = 'last_posted_facebook.txt'
FEED_URL = 'https://www.etsy.com/shop/thesashedits/rss'
FB_ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN')  # User token to fetch page ID
FB_PAGE_ACCESS_TOKEN = os.getenv('FB_PAGE_ACCESS_TOKEN')  # Page token to post
FB_API_URL = 'https://graph.facebook.com/v23.0/me/accounts'
FB_PHOTO_URL_TEMPLATE = 'https://graph.facebook.com/v23.0/{page_id}/photos'

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

def extract_image(summary):
    soup = BeautifulSoup(summary, 'html.parser')
    image_tag = soup.find('img')
    return image_tag['src'] if image_tag else None

def fetch_page_id():
    response = requests.get(FB_API_URL, params={"access_token": FB_ACCESS_TOKEN})
    if response.status_code == 200:
        data = response.json()
        pages = data.get("data", [])
        if not pages:
            print("❌ No Facebook pages found.")
            return None
        page = pages[0]
        print(f"✅ Using Facebook page: {page['name']} (ID: {page['id']})")
        return page['id']
    else:
        print("❌ Failed to fetch Facebook page ID.", response.text)
        return None

def main():
    post_limit = int(os.getenv("POST_LIMIT", "1"))

    page_id = fetch_page_id()
    if not page_id:
        return

    if not FB_PAGE_ACCESS_TOKEN:
        print("❌ FB_PAGE_ACCESS_TOKEN environment variable is required to post.")
        return

    posted_links = get_last_posted_links()
    feed = feedparser.parse(FEED_URL)
    new_posts = [entry for entry in feed.entries if entry.link not in posted_links]

    if not new_posts:
        print("No new posts. Skipping.")
        return

    print(f"Found {len(new_posts)} new post(s)! Posting up to {post_limit} post(s) to Facebook...")

    posted_count = 0
    for entry in reversed(new_posts):
        if posted_count >= post_limit:
            break

        link = entry.link
        title = entry.title
        summary = entry.summary
        image_url = extract_image(summary)
        message = f"{title}"

        if image_url:
            post_url = FB_PHOTO_URL_TEMPLATE.format(page_id=page_id)
            response = requests.post(
                post_url,
                data={
                    'url': image_url,
                    'caption': message,
                    'link': link,
                    'access_token': FB_PAGE_ACCESS_TOKEN
                }
            )
        else:
            print(f"❌ No image found for {title}, skipping image post.")
            continue

        if response.status_code == 200:
            print(f"✅ Successfully posted: {title}")
            add_posted_link(link)
            posted_count += 1
        else:
            print(f"❌ Failed to post: {title}. Status code: {response.status_code}")
            print(response.json())
            add_posted_link(link)

if __name__ == "__main__":
    main()
