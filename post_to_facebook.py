import os
import feedparser
import requests
from bs4 import BeautifulSoup

# Constants
LAST_POSTED_FILE = 'last_posted.txt'
feed_url = 'https://www.etsy.com/shop/thesashedits/rss'  # Replace YOURSHOPNAME
fb_page_id = os.getenv('FB_PAGE_ID')
access_token = os.getenv('FB_ACCESS_TOKEN')

def get_last_posted_links():
    if not os.path.exists(LAST_POSTED_FILE):
        return set()
    with open(LAST_POSTED_FILE, 'r') as file:
        links = file.read().splitlines()
        return set(links)

def add_posted_link(link):
    with open(LAST_POSTED_FILE, 'a') as file:
        file.write(link + '\n')

def extract_tags(entry):
    # Etsy RSS puts tags in category
    tags = [tag.term for tag in entry.tags] if 'tags' in entry else []
    return tags

def main():
    # Load all previously posted links
    posted_links = get_last_posted_links()

    # Parse Etsy RSS Feed
    feed = feedparser.parse(feed_url)
    new_posts = []

    for entry in feed.entries:
        link = entry.link
        if link not in posted_links:
            new_posts.append(entry)

    if not new_posts:
        print("No new posts. Skipping.")
        return

    print(f"Found {len(new_posts)} new post(s)! Posting to Facebook...")

    for entry in reversed(new_posts):  # oldest first → newest last
        link = entry.link
        title = entry.title
        summary = entry.summary

        tags = extract_tags(entry)
        hashtags = ' '.join([f"#{tag.replace(' ', '')}" for tag in tags]) if tags else "#Etsy #Handmade #ShopNow"

        post_message = f"{title}\n\nCheck it out here 👉 {link}\n\n{hashtags}"

        # Post to Facebook feed with link → clickable image post
        fb_api_url = f"https://graph.facebook.com/{fb_page_id}/feed"

        response = requests.post(fb_api_url, data={
            'message': post_message,
            'link': link,
            'access_token': access_token
        })

        if response.status_code == 200:
            print(f"✅ Post successful: {title}")
            add_posted_link(link)
        else:
            print(f"❌ Failed to post: {title}. Status code: {response.status_code}")
            print(response.json())

if __name__ == "__main__":
    main()
