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


# Funktion zum Scrapen der Produktseite
async def scrape_product_page(product_url, driver):
    # Öffne die Produktseite
    driver.get(product_url)
    time.sleep(5)  # Warten, bis die Seite geladen ist
    print("scraping new")
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
async def scrape_vinted_page(url, token=None):
    global firstsearch
    # Chrome Options für den Headless-Modus (optional)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Optional: Läuft ohne UI
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-unsafe-swiftshader")  # Verwendet Software-WebGL (ohne Fehler)
    chrome_options.add_argument("--disable-logging")  # Unterdrückt Logging
    chrome_options.add_argument("--log-level=3")  # Reduziert Logs auf Warnungen und Fehler

    # Pfad zum WebDriver (z.B. ChromeDriver)
    service = Service("C:/Users/Quirin/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe",)

    # Starte den WebDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Lade die Seite
    driver.get(url)

    # Optional: Warten, bis die Seite vollständig geladen ist
    time.sleep(5)  # Warte 5 Sekunden, um sicherzustellen, dass die Seite vollständig geladen ist

    # Optionales Token (Falls erforderlich)
    if token:
        driver.execute_script(f"window.localStorage.setItem('token', '{token}')")

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


    alteangebote= load_json_file("angebote.json")
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
                await  bot.send_offer(angebot)
    
     # Schließe den WebDriver
    firstsearch=False
    driver.quit()
    # Speichern der Angebote in einer JSON-Datei
    with open("angebote.json", "w", encoding="utf-8") as json_file:
        json.dump(angebote, json_file, ensure_ascii=False, indent=4)
    
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
async def main():
    # Starte den Bot
    bot_task = asyncio.create_task(bot.start_bot())
    await asyncio.sleep(5)
    # Führe die restlichen Tasks (z.B. Scraping) aus
    while True:
        await scrape_vinted_page(url)
       # await asyncio.sleep(5)  # Warte 15 Sekunden bevor der nächste Scrape ausgeführt wird

    # Warte darauf, dass der Bot die Verbindung hält
    await bot_task

# Starte alles im Event-Loop
asyncio.run(main())