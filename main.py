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
import bot  # Enthält unter anderem die Funktion send_offer
from discord.ext import commands
import os

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Klasse für Angebote
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

# Aktualisiere die JSON-Datei für einen einzelnen Monitor-Channel
def update_channel_json(file_path, new_offers, firstsearch):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    existing_offers = data.get("angebote", [])
    existing_numbers = {offer.get("number") for offer in existing_offers}
    # Füge nur Angebote hinzu, die noch nicht existieren
    additional_offers = [offer for offer in new_offers if offer.get("number") not in existing_numbers]
    data["angebote"] = existing_offers + additional_offers
    data["searchobject_fistsearch"] = firstsearch

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print(f"{file_path} successfully updated.")

async def scrape_product_page(product_url, driver):
    await asyncio.to_thread(driver.get, product_url)
    await asyncio.sleep(5)  # Warte, bis die Seite vollständig geladen ist

    print(f"Scraping: {product_url}")
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    # Standardwerte
    condition = "Unbekannt"
    description = "Keine Beschreibung gefunden"
    image_url = "Kein Bild gefunden"
    size = "Keine Größe gefunden"

    # Beschreibung extrahieren
    description_tag = soup.find("div", itemprop="description")
    if description_tag:
        description = description_tag.get_text(strip=True)[:1024]

    # Bild extrahieren
    img_tag = soup.find("img", class_="web_ui__Image__content", attrs={"data-testid": "item-photo-1--img"})
    if img_tag:
        image_url = img_tag['src']

    # Zustand extrahieren
    condition_tag = soup.find("div", {"data-testid": "item-attributes-status"})
    if condition_tag:
        condition_value = condition_tag.find("span", class_="web_ui__Text__bold")
        if condition_value:
            condition = condition_value.text.strip()

    # Größe extrahieren
    size_tag = soup.find("div", {"data-testid": "item-attributes-size"})
    if size_tag:
        size_value = size_tag.find("span", class_="web_ui__Text__bold")
        if size_value:
            size = size_value.text.strip()

    return condition, size, description, image_url

# Funktion, um die Vinted-Seite für einen Monitor-Channel zu scrapen
async def scrape_vinted_page_for_channel(searchobject_channel):
    database_folder = "databases"
    file_path = os.path.join(database_folder, f"{searchobject_channel}.json")
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"⚠️ Datei {file_path} nicht gefunden oder ungültig.")
        return
    
    
    # Wenn "removed" auf True gesetzt ist, ignoriere die Datei
    if data.get("removed", False):
        print(f"⚠️ Channel {searchobject_channel} wurde entfernt, überspringe.")
        return
    
    
    url = data.get("searchobject_url")
    if not url:
        print(f"Keine URL für Channel {searchobject_channel} gefunden.")
        return

    # Falls der URL-String nicht mit "http" beginnt, voranstellen
    if not url.startswith("http"):
        url = "https://" + url

    firstsearch_flag = data.get("searchobject_fistsearch", True)
    alteangebote = data.get("angebote", [])

    # Konfiguriere Chrome für Headless-Browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")

    service = Service(os.getenv("chromium"))
    driver = await asyncio.to_thread(webdriver.Chrome, service=service, options=chrome_options)
    
    # Abruf der Hauptseite mit Fehlerbehandlung, falls die URL nicht erreichbar ist
    try:
        await asyncio.to_thread(driver.get, url)
        await asyncio.sleep(5)
    except Exception as e:
        error_msg = f"⚠️ Die URL {url} ist nicht erreichbar. Fehler: {e}"
        print(error_msg)
    #    discord_channel = bot.get_channel(int(searchobject_channel)) 
       # if discord_channel:
       #     await discord_channel.send(error_msg)
        driver.quit()
        return

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    # Finde Produktlisten – hier werden die ersten 10 Elemente verarbeitet
    items = soup.find_all("div", class_="new-item-box__container")[:10]
    
    scraped_offers = []
    if items:
        for item in items:
            
            item_link = item.find("a", class_="new-item-box__overlay")
            link = item_link['href'] if item_link else "Kein Link gefunden"
            
            overlay_link = soup.find("a", class_="new-item-box__overlay new-item-box__overlay--clickable")
            full_title = overlay_link["title"].strip() if overlay_link and overlay_link.has_attr("title") else "Kein Titel gefunden"

            # Extrahiere den Teil vor dem ersten Komma, also nur "Jogging Nike Tech Gris"
            title_text = full_title.split(",")[0].strip()
            print(title_text)
            size = "Keine Größe gefunden"
            descriptions = item.find_all("div", class_="new-item-box__description")
            for desc in descriptions:
                size_paragraph = desc.find("p", class_="web_ui__Text__text web_ui__Text__caption web_ui__Text__left")
                if size_paragraph:
                    size = size_paragraph.text.strip()
                    break

            price_tag = item.find("p", class_="web_ui__Text__text web_ui__Text__caption web_ui__Text__left web_ui__Text__muted")
            price_text = price_tag.text.strip() if price_tag else "Kein Preis gefunden"
            
            match = re.search(r'/items/(\d+)-', link)
            number = match.group(1) if match else 0

            # Zunächst werden Standardwerte gesetzt; spätere Detailinfos nur bei neuen Angeboten
            condition = "Unbekannt"
            desc_text = "Keine Beschreibung gefunden"
            image_url = "Kein Bild gefunden"
            offer = Angebot(title_text, price_text, size, link, number, condition, desc_text, image_url)
            scraped_offers.append(offer.to_dict())
    else:
        print("Keine Artikel auf der Seite gefunden.")
    
    # Falls nicht der erste Durchlauf: Detailinfos für neue Angebote ermitteln
    if not firstsearch_flag:
        for offer_dict in scraped_offers:
            number = offer_dict.get("number")
            if number and not any(existing.get("number") == number for existing in alteangebote):
                print(f"Neues Angebot: {offer_dict.get('link')}")
                condition, size, desc_text, image_url = await scrape_product_page(offer_dict.get("link"), driver)
                offer_dict.update({
                    "condition": condition,
                    "description": desc_text,
                    "image_url": image_url,
                    "size":size
                })
                # Sende das Angebot über den Bot
                await bot.send_offer(
                    Angebot(
                        offer_dict.get("title"),
                        offer_dict.get("price"),
                        offer_dict.get("size"),
                        offer_dict.get("link"),
                        number,
                        condition,
                        desc_text,
                        image_url
                    ),
                    int(searchobject_channel)
                )
    
    # Aktualisiere die JSON-Datei für diesen Channel mit den neuen Angeboten
    update_channel_json(file_path, scraped_offers, False)
    
    driver.quit()
    print(f"Scraping für Channel {searchobject_channel} abgeschlossen.")

# Hauptschleife: Iteriere über alle JSON-Dateien im Ordner "databases" und starte für jeden Scraping-Task
async def run_scraping_loop():
    database_folder = "databases"
    while True:
        if not os.path.exists(database_folder):
            print("Keine Datenbank-Dateien gefunden.")
            await asyncio.sleep(10)
            continue

        json_files = [f for f in os.listdir(database_folder) if f.endswith(".json")]
        if not json_files:
            print("⚠️ Keine Einträge in der Datenbank gefunden.")
            await asyncio.sleep(10)
            continue
        
        tasks = []
        for filename in json_files:
            # Extrahiere die Channel-ID aus dem Dateinamen (z. B. "123456789.json")
            channel_id = os.path.splitext(filename)[0]
            tasks.append(asyncio.create_task(scrape_vinted_page_for_channel(channel_id)))
        
        if tasks:
            await asyncio.gather(*tasks)
            print("🔄 Eine Runde Scraping abgeschlossen. Starte neu...")
        else:
            print("⚠️ Keine Tasks erstellt.")
        await asyncio.sleep(1)  # 60 Sekunden Pause bis zur nächsten Runde

# Main-Funktion: Starte den Bot und den Scraping-Loop gleichzeitig
async def main():
    bot_task = asyncio.create_task(bot.start_bot())
    await asyncio.sleep(6)  # Kleine Wartezeit, damit der Bot initialisiert ist
    scraping_task = asyncio.create_task(run_scraping_loop())
    await asyncio.gather(bot_task, scraping_task)

if __name__ == "__main__":
    asyncio.run(main())
