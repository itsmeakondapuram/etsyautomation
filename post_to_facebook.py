import os
import feedparser
import requests
from bs4 import BeautifulSoup

# Constants
LAST_POSTED_FILE = 'last_posted.txt'
feed_url = 'https://www.etsy.com/shop/thesashedits/rss'  # Replace YOURSHOPNAME
fb_page_id = os.getenv('FB_PAGE_ID')
access_token = os.getenv('FB_ACCESS_TOKEN')

def get_last_posted():
    if not os.path.exists(LAST_POSTED_FILE):
        return None
    with open(LAST_POSTED_FILE, 'r') as file:
        return file.read().strip()

def set_last_posted(link):
    with open(LAST_POSTED_FILE, 'w') as file:
        file.write(link)

def extract_tags(entry):
    # Etsy RSS puts tags in category
    tags = [tag.term for tag in entry.tags] if 'tags' in entry else []
    return tags

def main():
    # Load last posted link
    last_posted = get_last_posted()

    # Parse Etsy RSS Feed
    feed = feedparser.parse(feed_url)
    latest_entry = feed.entries[0]
    latest_link = latest_entry.link
    latest_title = latest_entry.title
    latest_summary = latest_entry.summary

    # Extract tags
    tags = extract_tags(latest_entry)
    hashtags = ' '.join([f"#{tag.replace(' ', '')}" for tag in tags]) if tags else "#Etsy #Handmade #ShopNow"

    print(f"Latest post found: {latest_title} → {latest_link}")
    print(f"Tags/Hashtags: {hashtags}")

    # Check if new post
    if latest_link != last_posted:
        print("New post detected! Posting to Facebook...")

        post_message = f"{latest_title}\n\nCheck it out here 👉 {latest_link}\n\n{hashtags}"

        # Post to Facebook feed with link → clickable image post
        fb_api_url = f"https://graph.facebook.com/{fb_page_id}/feed"

        response = requests.post(fb_api_url, data={
            'message': post_message,
            'link': latest_link,
            'access_token': access_token
        })

        if response.status_code == 200:
            print("✅ Post successful!")
            set_last_posted(latest_link)
        else:
            print(f"❌ Failed to post. Status code: {response.status_code}")
            print(response.json())
    else:
        print("No new post. Skipping.")

if __name__ == "__main__":
    main()
