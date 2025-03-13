import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio
from dotenv import load_dotenv
import os
import json

# Lade Umgebungsvariablen
load_dotenv()  # Lädt die Umgebungsvariablen aus der .env-Datei
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Erstelle ein Bot-Objekt mit den nötigen Intents
intents = discord.Intents.default()
intents.message_content = True  # Ermöglicht es dem Bot, Nachrichten zu lesen
bot = commands.Bot(command_prefix="!", intents=intents)

# Ereignis: Bot ist online und synchronisiert die Slash Commands
@bot.event
async def on_ready():
    print(f"✅ Bot ist eingeloggt als {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Commands wurden synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Synchronisieren der Commands: {e}")

# Funktion zum Laden der JSON-Datei
async def load_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Datei nicht gefunden oder leer. Eine neue Datenbank wird erstellt.")
        return []  # Starte mit leerer Liste

# Funktion zum Speichern der JSON-Datei
async def save_json_file(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Slash Command: URL hinzufügen
@bot.tree.command(name="seturl", description="Setzt die URL für den aktuellen Channel")
async def seturl(interaction: discord.Interaction, url: str):
    print("🔹 seturl Befehl empfangen!")
    channel_id = str(interaction.channel_id)
    file_path = "db.json"

    # Lade die Datenbank
    loaded_database = await load_json_file(file_path)

    # Prüfe, ob bereits eine URL existiert
    for entry in loaded_database:
        if entry["searchobject_channel"] == channel_id:
            await interaction.response.send_message(
                f"⚠️ In diesem Channel wurde bereits eine URL gesetzt: `{entry.get('searchobject_url', 'Keine URL vorhanden')}`",
                ephemeral=True,
            )
            return

    # Füge einen neuen Eintrag hinzu
    new_entry = {
        "searchobject_channel": channel_id,
        "searchobject_url": url,
        "angebote": [],
        "searchobject_fistsearch": True,
    }
    loaded_database.append(new_entry)

    # Speichere die Änderungen
    await save_json_file(file_path, loaded_database)
    print("✅ URL erfolgreich gespeichert!")
    await interaction.response.send_message(f"✅ Die URL wurde erfolgreich gesetzt: `{url}`")

# Slash Command: URL entfernen
@bot.tree.command(name="removeurl", description="Entfernt die URL des aktuellen Channels")
async def removeurl(interaction: discord.Interaction):
    print("🔹 removeurl Befehl empfangen!")
    channel_id = str(interaction.channel_id)
    file_path = "db.json"

    # Lade die bestehende Datenbank
    loaded_database = await load_json_file(file_path)
    print("🔍 Datenbank geladen.")

    # Entferne den Eintrag, der die Channel-ID enthält
    new_database = [entry for entry in loaded_database if entry["searchobject_channel"] != channel_id]

    # Prüfe, ob ein Eintrag entfernt wurde
    if len(new_database) < len(loaded_database):
        await save_json_file(file_path, new_database)
        print("✅ Eintrag entfernt.")
        await interaction.response.send_message("✅ Der Eintrag für diesen Channel wurde erfolgreich entfernt.")
    else:
        print("⚠️ Kein Eintrag zum Entfernen gefunden.")
        await interaction.response.send_message("⚠️ Kein Eintrag für diesen Channel gefunden.", ephemeral=True)

# Klasse zur Erstellung einer Button-View für Angebote
class AngebotView(ui.View):
    def __init__(self, link):
        super().__init__()
        self.link = link
        # Füge einen Button hinzu, der direkt zur Angebotsseite führt
        self.add_item(ui.Button(label="Angebot ansehen", url=self.link))

# Funktion, um ein Angebot an Discord zu senden
async def send_offer(angebot, channel_id):
    file_path = "db.json"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            loaded_database = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Fehler beim Laden der Datenbank.")
        return

    # Überprüfe, ob der Eintrag mit der gegebenen Channel-ID existiert
    entry = next((entry for entry in loaded_database if entry["searchobject_channel"] == str(channel_id)), None)
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

    # Erstelle die View für den Button
    view = AngebotView(angebot.link)

    # Hole den Channel und sende das Embed mit dem Button
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(embed=embed, view=view)
        print(f"✅ Angebot an Channel {channel_id} gesendet.")
    else:
        print(f"⚠️ Kanal-ID {channel_id} nicht gefunden!")

# Funktion zum Starten des Bots
async def start_bot():
    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"❌ Fehler beim Starten des Bots: {e}")

if __name__ == "__main__":
    asyncio.run(start_bot())
