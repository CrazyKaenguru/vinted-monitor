import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import os
import json

# Lade Umgebungsvariablen
load_dotenv()  # Lädt die Umgebungsvariablen aus der .env-Datei
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Erstelle ein Bot-Objekt mit den entsprechenden Präfixen
intents = discord.Intents.default()
intents.message_content = True  # Ermöglicht es dem Bot, Nachrichten zu lesen
bot = commands.Bot(command_prefix='!', intents=intents)

# Ereignis: Bot ist online und bereit
@bot.event
async def on_ready():
    print(f'✅ Bot ist eingeloggt als {bot.user}')

# Funktion zum Laden der JSON-Datei
async def load_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)  # Lade die JSON-Datei als Python-Objekt
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Datei nicht gefunden oder leer. Eine neue Datenbank wird erstellt.")
        return []  # Falls Datei nicht existiert oder leer ist, starte mit leerer Liste

# Funktion zum Speichern der JSON-Datei
async def save_json_file(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Bot-Befehl: URL hinzufügen
@bot.command()
async def seturl(ctx, url: str):
    print("🔹 seturl Befehl empfangen!")
    channel_id = str(ctx.channel.id)
    file_path = 'db.json'

    # Lade die Datenbank
    loaded_database = await load_json_file(file_path)

    # Prüfe, ob bereits eine URL existiert
    for entry in loaded_database:
        if entry['searchobject_channel'] == channel_id:
            await ctx.send(f"⚠️ In diesem Channel wurde bereits eine URL gesetzt: `{entry.get('searchobject_url', 'Keine URL vorhanden')}`")
            return

    # Füge einen neuen Eintrag hinzu
    new_entry = {
        "searchobject_channel": channel_id,
        "searchobject_url": url,
        "angebote": [],
        "searchobject_fistsearch": True
    }
    loaded_database.append(new_entry)

    # Speichere die Änderungen
    await save_json_file(file_path, loaded_database)
    print("✅ URL erfolgreich gespeichert!")
    await ctx.send(f"✅ Die URL wurde erfolgreich gesetzt: `{url}`")



# Bot-Befehl: URL entfernen
@bot.command()
async def removeurl(ctx):
    print("🔹 removeurl Befehl empfangen!")
    channel_id = str(ctx.channel.id)
    file_path = 'db.json'

    # Lade die bestehende Datenbank
    loaded_database = await load_json_file(file_path)
    print("🔍 Datenbank geladen.")

    # Finde den Eintrag, der die Channel-ID enthält und entferne ihn
    new_database = [entry for entry in loaded_database if entry['searchobject_channel'] != channel_id]

    # Prüfe, ob ein Eintrag entfernt wurde
    if len(new_database) < len(loaded_database):
        await save_json_file(file_path, new_database)  # Speichere die Änderungen
        print("✅ Eintrag entfernt.")
        await ctx.send(f"✅ Der Eintrag für diesen Channel wurde erfolgreich entfernt.")
    else:
        print("⚠️ Kein Eintrag zum Entfernen gefunden.")
        await ctx.send(f"⚠️ Kein Eintrag für diesen Channel gefunden.")


# Funktion, um ein Angebot an Discord zu senden
import discord
from discord.ui import Button, View
from discord.utils import utcnow
from datetime import timedelta

# Funktion, um ein Angebot an Discord zu senden
async def send_offer(angebot, channel_id):
    # Lade die Datenbank, um sicherzustellen, dass der Eintrag existiert
    file_path = 'db.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            loaded_database = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Fehler beim Laden der Datenbank.")
        return

    # Überprüfe, ob der Eintrag mit der gegebenen Channel-ID existiert
    entry = next((entry for entry in loaded_database if entry['searchobject_channel'] == str(channel_id)), None)
    if not entry:
        print(f"⚠️ Kein Eintrag für die Channel-ID {channel_id} gefunden. Angebot wird nicht gesendet.")
        return

    # Erstelle das Embed für das Angebot
    embed = discord.Embed(
        title=angebot.title,
        description=angebot.title,
        url=angebot.link,
        color=5814783
    )

    embed.add_field(name="Preis", value=f"{angebot.price}€", inline=True)
    embed.add_field(name="Größe", value=angebot.size, inline=True)
    embed.add_field(name="Zustand", value=angebot.condition, inline=True)
    embed.add_field(name="Beschreibung", value=angebot.description, inline=True)
    if angebot.image_url != "Kein Bild gefunden":
        embed.set_image(url=angebot.image_url)

    # Hole den Channel und sende das Embed
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(embed=embed)
        print(f"✅ Angebot an Channel {channel_id} gesendet.")
    else:
        print(f"⚠️ Kanal-ID {channel_id} nicht gefunden!")



# Funktion zum Starten des Bots
async def start_bot():
    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"❌ Fehler beim Starten des Bots: {e}")
