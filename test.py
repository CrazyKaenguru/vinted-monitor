from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json
from bs4 import BeautifulSoup
import re
import config
import bot

#from bot import send_offer
#from bot import startbot
# Definiere die Klasse Angebot

from dotenv import load_dotenv
import os
load_dotenv()  # Load environment variables from .env file


firstsearch=True
class Angebot:
    def __init__(self, title, price, size, link,number,condition,description):
        self.title = title
        self.price = price
        self.size = size
        self.link = link
        self.number = number
        self.condition = condition
        self.description = description

    def to_dict(self):
        return {
            "title": self.title,
            "price": self.price,
            "size": self.size,
            "link": self.link,
            "number":self.number,
            "condition":self.condition,
            "description":self.description
        }


def update_json_file(file_path, searchobject_channel, angebote, firstsearch):
    """
    Aktualisiert die db.json, ohne bestehende externe Einträge zu löschen.
    """
    try:
        # Lade bestehende Daten
        with open(file_path, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    # Suche nach dem passenden Channel-Eintrag
    updated = False
    for entry in existing_data:
        if entry['searchobject_channel'] == searchobject_channel:
            # Füge neue Angebote hinzu, die noch nicht existieren
            existing_numbers = {offer['number'] for offer in entry.get('angebote', [])}
            new_offers = [offer for offer in angebote if offer['number'] not in existing_numbers]
            entry['angebote'].extend(new_offers)
            entry['searchobject_fistsearch'] = firstsearch  # Update firstsearch
            updated = True
            break

    # Wenn kein Eintrag für den Channel existiert, füge einen neuen hinzu
    if not updated:
        existing_data.append({
            "searchobject_channel": searchobject_channel,
            "searchobject_fistsearch": firstsearch,
            "angebote": angebote
        })

    # Speichere die aktualisierten Daten zurück in die Datei
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    print("db.json erfolgreich aktualisiert.")


# Funktion zum Scrapen der Produktseite
async def scrape_product_page(product_url, driver):
    # Öffne die Produktseite
    await asyncio.to_thread(driver.get, url) 
    await asyncio.sleep(2)
    print("scraping: "+product_url)
    # Holen des HTML-Codes der Seite
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    # Extrahieren von Produktdetails
    condition = "Unbekannt"
    description = "Keine Beschreibung gefunden"

    # Beispiel für das Extrahieren der Produktbeschreibung und Zustand
    description_tag = soup.find("div", itemprop="description")
    if description_tag:
         description = description_tag.get_text(strip=True)  # Clean up the text by stripping whitespace
         description = description[:1024]
    else:
        description = "Keine Beschreibung gefunden"  # Default value if no description is found

    condition_tag = soup.find("div", class_="details-list__item-value", itemprop="status")
   
    if condition_tag:
        condition = condition_tag.text.strip()  # Clean up the text by stripping whitespace
    else:
        condition = "Unbekannt"  # Default value if no condition is found

    return condition, description
    
    
# Funktion zum Scrapen einer Vinted-Seite mit Selenium
async def scrape_vinted_page(data,searchobject_channel):
    for entry in data:
     if entry['searchobject_channel'] == searchobject_channel:
        url=entry['searchobject_url']
        print("url:" +url)
        firstsearch=entry['searchobject_fistsearch']
        alteangebote=entry['angebote']
        
    
    # Chrome Options für den Headless-Modus (optional)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Optional: Läuft ohne UI
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-unsafe-swiftshader")  # Verwendet Software-WebGL (ohne Fehler)
    chrome_options.add_argument("--disable-logging")  # Unterdrückt Logging
    chrome_options.add_argument("--log-level=3")  # Reduziert Logs auf Warnungen und Fehler

    # Pfad zum WebDriver (z.B. ChromeDriver)
    service = Service(os.getenv("chromium"))

    # Starte den WebDriver
    driver = await asyncio.to_thread(webdriver.Chrome, service=service, options=chrome_options)
    
    await asyncio.to_thread(driver.get, url)  # Die get-Methode ausführen
    await asyncio.sleep(5) 
    # Optional: Warten, bis die Seite vollständig geladen ist
   

    

    # Hole den HTML-Code der Seite
    page_source = driver.page_source

    # Verwende BeautifulSoup, um den HTML-Code zu parsen
    soup = BeautifulSoup(page_source, "html.parser")

    # Suche nach allen Containern mit der Klasse "new-item-box__container"
    items = soup.find_all("div", class_="new-item-box__container")[:10]
    
    # Liste für die Angebote
    angebote = []
    
    # Extrahiere die Daten für jedes gefundene Angebot
    if items:
        for item in items:
            # Extrahiere den Link des Artikels
            item_link = item.find("a", class_="new-item-box__overlay")
            link = item_link['href'] if item_link else "Kein Link gefunden"
            
            # Extrahiere den Titel des Artikels
            title = item.find("p", class_="web_ui__Text__text web_ui__Text__caption web_ui__Text__left web_ui__Text__truncated")
            title_text = title.text.strip() if title else "Kein Titel gefunden"
            
            # Suche nach allen 'new-item-box__description' Divs und extrahiere die Größe
            size = "Keine Größe gefunden"
            descriptions = item.find_all("div", class_="new-item-box__description")
            for desc in descriptions:
                size_paragraph = desc.find("p", class_="web_ui__Text__text web_ui__Text__caption web_ui__Text__left")
                if size_paragraph:
                    size = size_paragraph.text.strip()
                    break  # Wenn die Größe gefunden wurde, stoppe die Suche

            # Extrahiere den Preis des Artikels
            price = item.find("p", class_="web_ui__Text__text web_ui__Text__caption web_ui__Text__left web_ui__Text__muted")
            price_text = price.text.strip() if price else "Kein Preis gefunden"
            #Extrahieren der Nummer:
            
            
            match = re.search(r'/items/(\d+)-', link)
            if match:
                number = match.group(1)  # Extrahiere die erste gefundene Gruppe
            else:
                 print("Keine Nummer gefunden.")
                 number=0
            # Erstelle ein Angebot-Objekt und füge es zur Liste hinzu
            condition="0"
            description="0"
            angebot = Angebot(title_text, price_text, size, link,number,condition,description)
            angebote.append(angebot.to_dict())

    else:
        print("Keine Artikel auf der Seite gefunden.")

   
    
    
    
    
    #Scrapen der Details
    #laden der bereits existirenden eangebote
    def load_json_file(file_path):
     try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)  # Lade die JSON-Datei als Python-Objekt
     except FileNotFoundError:
        print("Datei nicht gefunden, erstelle eine neue Liste.")
        return []  # Falls Datei nicht existiert, starte mit leerer Liste
    
    
    def is_offer_existing(angebote, neue_nummer):
     for angebot in angebote:
        if angebot.get("number") == neue_nummer:  # Vergleiche die Nummern
            return True
     return False


    
    if not firstsearch:
     for angebot in angebote:
        number=angebot.get("number","no number")
        
        if(number!="no number" and (is_offer_existing(alteangebote,number)==False)):
                title = angebot.get("title", "Kein Titel")   # Sicherer Zugriff auf 'title'
                price = angebot.get("price", "Kein Preis")  # Sicherer Zugriff auf 'price'
                size = angebot.get("size", "Keine Größe")   # Sicherer Zugriff auf 'size'
                link = angebot.get("link", "Kein Link")     # Sicherer Zugriff auf 'link'
                print("neues Angebot: "+link)
                condition, description = await scrape_product_page(link, driver)
                angebot = Angebot(title, price, size, link, number, condition, description)
                await  bot.send_offer(angebot,int(searchobject_channel))
    
     # Schließe den WebDriver
    firstsearch=False
    driver.quit()
    # Speichern der Angebote in einer JSON-Datei
   # with open("angebote.json", "w", encoding="utf-8") as json_file:
     #   json.dump(angebote, json_file, ensure_ascii=False, indent=4)4
    
    
    update_json_file('db.json', searchobject_channel, angebote, firstsearch)
    
    
    print("Angebote wurden in 'angebote.json' gespeichert.")

# Beispiel-URL und optionales Token

# main_script.py
  # Importiere das Bot-Modul
import asyncio
import json

# Lade die Konfiguration
def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)
    return config

# Lade die Konfiguration
config = load_config("config.json")
url = config.get("url")

# Scraping-Funktion (hier kannst du deine Scraping-Logik hinzufügen)


# Hauptfunktion, die alles startet



# Optimierte run_scraping_loop-Funktion
async def run_scraping_loop():
    while True:
        try:
            # Lade die db.json-Datei
            with open('db.json', 'r', encoding='utf-8') as file:
                loaded_database = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print("⚠️ Fehler beim Laden der Datenbank. Warte 10 Sekunden und versuche es erneut...")
            await asyncio.sleep(10)
            continue

        # Erstelle parallele Scraping-Tasks für alle Channels
        tasks = []
        for entry in loaded_database:
            searchobject_channel = entry['searchobject_channel']
            tasks.append(asyncio.create_task(scrape_vinted_page(loaded_database, searchobject_channel)))

        # Führe alle Scraping-Tasks gleichzeitig aus
        if tasks:
            await asyncio.gather(*tasks)
            print("🔄 Eine Runde Scraping abgeschlossen. Starte neu...")
        else:
            print("⚠️ Keine Einträge in der Datenbank gefunden.")

        # Verzögerung vor der nächsten Runde
       # await asyncio.sleep(10)

# Hauptfunktion zum Starten des Bots und Scraping-Tasks
async def main():
    # Starte den Bot in einem asynchronen Task
    bot_task = asyncio.create_task(bot.start_bot())
    await asyncio.sleep(6)

    # Starte das Scraping parallel in einem eigenen Task
    scraping_task = asyncio.create_task(run_scraping_loop())

    # Warte darauf, dass beide Tasks laufen
    await asyncio.gather(bot_task, scraping_task)

# Starte alles im Event-Loop
if __name__ == "__main__":
    asyncio.run(main())