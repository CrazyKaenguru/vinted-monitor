from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv
import asyncio
import bot

# Load environment variables from .env file
load_dotenv()

# Global variable for first search flag
firstsearch = True

class Angebot:
    def __init__(self, title, price, size, link, number, condition, description, image_url):
        self.title = title
        self.price = price
        self.size = size
        self.link = link
        self.number = number
        self.condition = condition
        self.description = description
        self.image_url = image_url

    def to_dict(self):
        return {
            "title": self.title,
            "price": self.price,
            "size": self.size,
            "link": self.link,
            "number": self.number,
            "condition": self.condition,
            "description": self.description,
            "image_url": self.image_url
        }

# Function to update the JSON database
def update_json_file(file_path, searchobject_channel, angebote, firstsearch):
    try:
        # Load existing data from the JSON file
        with open(file_path, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    updated = False
    for entry in existing_data:
        if entry['searchobject_channel'] == searchobject_channel:
            existing_numbers = {offer['number'] for offer in entry.get('angebote', [])}
            new_offers = [offer for offer in angebote if offer['number'] not in existing_numbers]
            entry['angebote'].extend(new_offers)
            entry['searchobject_fistsearch'] = firstsearch
            updated = True
            break

    if not updated:
        existing_data.append({
            "searchobject_channel": searchobject_channel,
            "searchobject_fistsearch": firstsearch,
            "angebote": angebote
        })

    # Write the updated data back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    print("db.json successfully updated.")

# Function to scrape product details (like condition, description, and image) from the product page
async def scrape_product_page(product_url, driver):
    # Load the product page using Selenium WebDriver
    await asyncio.to_thread(driver.get, product_url)  # Run Selenium actions in a background thread
    await asyncio.sleep(5)  # Allow some time for the page to load

    print(f"Scraping: {product_url}")

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    
    # Extract product details
    condition = "Unbekannt"
    description = "Keine Beschreibung gefunden"
    image_url = "Kein Bild gefunden"

    # Description extraction
    description_tag = soup.find("div", itemprop="description")
    if description_tag:
        description = description_tag.get_text(strip=True)[:1024]

    # Image extraction
    # Find the img tag with the correct class and data-testid
    img_tag = soup.find("img", class_="web_ui__Image__content", attrs={"data-testid": "item-photo-1--img"})
    if img_tag:
        image_url = img_tag['src']
    else:
     image_url = "Kein Bild gefunden"

  
    # Condition extraction
    condition_tag = soup.find("div", class_="details-list__item-value--redesign", itemprop="status")
    if condition_tag:
    # Find the <span> inside this div and extract its text
        condition = condition_tag.find("span").text.strip() if condition_tag.find("span") else "Unbekannt"
    return condition, description, image_url

# Function to scrape the Vinted page for product listings
async def scrape_vinted_page(data, searchobject_channel):
    for entry in data:
        if entry['searchobject_channel'] == searchobject_channel:
            url = entry['searchobject_url']
            print(f"Scraping URL: {url}")
            firstsearch = entry['searchobject_fistsearch']
            alteangebote = entry['angebote']

    # Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode (no UI)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")

    # Set path for the WebDriver
    service = Service(os.getenv("chromium"))  # Assuming the path is set in .env

    # Initialize the WebDriver
    driver = await asyncio.to_thread(webdriver.Chrome, service=service, options=chrome_options)

    # Fetch the main Vinted page
    await asyncio.to_thread(driver.get, url)
    await asyncio.sleep(5)  # Allow the page to load

    # Parse the page with BeautifulSoup
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    # Find product listings
    items = soup.find_all("div", class_="new-item-box__container")[:10]
    
    angebote = []
    if items:
        for item in items:
            item_link = item.find("a", class_="new-item-box__overlay")
            link = item_link['href'] if item_link else "Kein Link gefunden"
            
            title = item.find("p", class_="web_ui__Text__text web_ui__Text__caption web_ui__Text__left web_ui__Text__truncated")
            title_text = title.text.strip() if title else "Kein Titel gefunden"

            size = "Keine Größe gefunden"
            descriptions = item.find_all("div", class_="new-item-box__description")
            for desc in descriptions:
                size_paragraph = desc.find("p", class_="web_ui__Text__text web_ui__Text__caption web_ui__Text__left")
                if size_paragraph:
                    size = size_paragraph.text.strip()
                    break

            price = item.find("p", class_="web_ui__Text__text web_ui__Text__caption web_ui__Text__left web_ui__Text__muted")
            price_text = price.text.strip() if price else "Kein Preis gefunden"
            
            # Extract item number from the link
            match = re.search(r'/items/(\d+)-', link)
            number = match.group(1) if match else 0

            # Create Angebot object and append to the list
            condition, description, image_url = "0", "0", "0"
            angebot = Angebot(title_text, price_text, size, link, number, condition, description, image_url)
            angebote.append(angebot.to_dict())
    else:
        print("Keine Artikel auf der Seite gefunden.")

    # Scrape additional details if not the first search
    if not firstsearch:
        for angebot in angebote:
            number = angebot.get("number", "no number")
            if number != "no number" and not any(existing_offer.get("number") == number for existing_offer in alteangebote):
                title = angebot.get("title", "Kein Titel")
                price = angebot.get("price", "Kein Preis")
                size = angebot.get("size", "Keine Größe")
                link = angebot.get("link", "Kein Link")
                print(f"Neues Angebot: {link}")
                condition, description, image_url = await scrape_product_page(link, driver)
                angebot = Angebot(title, price, size, link, number, condition, description, image_url)
                await bot.send_offer(angebot, int(searchobject_channel))

    firstsearch = False
    driver.quit()  # Quit the driver when done

    # Update JSON with the latest offers
    update_json_file('db.json', searchobject_channel, angebote, firstsearch)
    print("Angebote wurden in 'db.json' gespeichert.")

# Main scraping loop
async def run_scraping_loop():
    while True:
        try:
            with open('db.json', 'r', encoding='utf-8') as file:
                loaded_database = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print("⚠️ Fehler beim Laden der Datenbank. Warte 10 Sekunden und versuche es erneut...")
            await asyncio.sleep(10)
            continue

        tasks = []
        for entry in loaded_database:
            searchobject_channel = entry['searchobject_channel']
            tasks.append(asyncio.create_task(scrape_vinted_page(loaded_database, searchobject_channel)))

        if tasks:
            await asyncio.gather(*tasks)
            print("🔄 Eine Runde Scraping abgeschlossen. Starte neu...")
        else:
            print("⚠️ Keine Einträge in der Datenbank gefunden.")

# Main function to start the bot and scraping tasks
async def main():
    bot_task = asyncio.create_task(bot.start_bot())
    await asyncio.sleep(6)

    scraping_task = asyncio.create_task(run_scraping_loop())
    await asyncio.gather(bot_task, scraping_task)

if __name__ == "__main__":
    asyncio.run(main())
