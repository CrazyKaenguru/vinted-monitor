import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio
from dotenv import load_dotenv
import os
import json

# Lade Umgebungsvariablen
load_dotenv()  # Lädt die Variablen aus der .env-Datei
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Definiere den vorgesehenen Command Channel und die Kategorie-ID für Monitor Channels
COMMAND_CHANNEL_ID = int(os.getenv("COMMAND_CHANNEL_ID", "1349831728625094698"))
MONITOR_CATEGORY_ID = int(os.getenv("MONITOR_CATEGORY_ID", "1319676360674775193"))

# Erstelle ein Bot-Objekt (Prefix wird intern benötigt)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Hilfsfunktion zum Speichern einer JSON-Datei
async def save_json_file(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Slash Command: set_monitor
@bot.tree.command(name="set_monitor", description="Erstellt einen neuen Monitor Channel und setzt die URL")
async def set_monitor(interaction: discord.Interaction, url: str):
    print("🔹 set_monitor Befehl empfangen!")
    
    # Überprüfe, ob der Command im vorgesehenen Command Channel ausgeführt wird
    if interaction.channel_id != COMMAND_CHANNEL_ID:
        await interaction.response.send_message(
            f"Bitte benutze den dafür vorgesehenen Channel: <#{COMMAND_CHANNEL_ID}>",
            ephemeral=True
        )
        return

    # Hole die Guild und die Zielkategorie
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("Guild nicht gefunden.", ephemeral=True)
        return

    category = guild.get_channel(MONITOR_CATEGORY_ID)
    if category is None:
        await interaction.response.send_message("Monitor-Kategorie nicht gefunden.", ephemeral=True)
        return

    # Erstelle einen neuen Textchannel unter der Zielkategorie
    # Der Channel-Name wird aus dem Benutzernamen abgeleitet (in Kleinbuchstaben, Leerzeichen ersetzt)
    channel_name = f"monitor-{interaction.user.name}".lower().replace(" ", "-")
    new_channel = await guild.create_text_channel(name=channel_name, category=category)

    # Antwort sofort an den Benutzer senden
    await interaction.response.send_message(
        f"✅ Monitor Channel erstellt: {new_channel.mention}\nURL gesetzt: `{url}`"
    )

    # Erstelle die JSON-Datei für den neu erstellten Monitor Channel
    database_folder = "databases"
    os.makedirs(database_folder, exist_ok=True)
    json_file_path = os.path.join(database_folder, f"{new_channel.id}.json")
    
    data = {
        "searchobject_channel": str(new_channel.id),
        "searchobject_url": url,
        "angebote": [],
        "searchobject_fistsearch": True,
        "removed": False
    }

    # Asynchron speichern, ohne den Bot zu blockieren
    await save_json_file(json_file_path, data)
    print("✅ Monitor Channel erstellt und URL gespeichert!")



# Slash Command: remove_monitor
@bot.tree.command(name="remove_monitor", description="Setzt den Status eines Monitor Channels auf entfernt")
async def remove_monitor(interaction: discord.Interaction):
    print("🔹 remove_monitor Befehl empfangen!")


    # Hole die Guild und den Channel
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("Guild nicht gefunden.", ephemeral=True)
        return

    # Überprüfe, ob der Channel, in dem der Befehl ausgeführt wird, ein Monitor Channel ist
    channel = guild.get_channel(interaction.channel_id)
    if channel is None or channel.category_id != MONITOR_CATEGORY_ID:
        await interaction.response.send_message("Dieser Befehl kann nur in einem Monitor Channel ausgeführt werden.", ephemeral=True)
        return

    # Aktualisiere die zugehörige JSON-Datenbank
    json_file_path = os.path.join("databases", f"{channel.id}.json")
    if os.path.exists(json_file_path):
        # Lade die JSON-Daten
        with open(json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Setze "removed" auf True
        data["removed"] = True

        # Speichere die aktualisierten Daten zurück in die Datei
        await save_json_file(json_file_path, data)
        print(f"✅ Status für Channel {channel.name} auf 'removed' gesetzt.")

        # Lösche den Channel
        await channel.delete()
        print(f"✅ Monitor Channel {channel.name} entfernt.")

        # Bestätige den Erfolg
        await interaction.response.send_message(f"✅ Monitor Channel {channel.mention} wurde entfernt und als 'removed' markiert.", ephemeral=True)
    else:
        print(f"⚠️ Keine Datenbankdatei für Channel {channel.id} gefunden.")
        await interaction.response.send_message("❌ Keine Datenbankdatei für diesen Channel gefunden.", ephemeral=True)


@bot.event
async def on_ready():
    print(f"✅ Bot ist eingeloggt als {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Commands wurden synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Synchronisieren der Commands: {e}")

# Beispiel-Funktion zum Versenden eines Angebots (unverändert)
async def send_offer(angebot, channel_id):
    class AngebotView(ui.View):
        def __init__(self, link):
            super().__init__()
            self.link = link
            self.add_item(ui.Button(label="Angebot ansehen", url=self.link))
        
    # Dieser Teil nutzt weiterhin die Datei "db.json". Falls du auch hier auf die per-Channel JSON-Dateien umstellen möchtest, passe den Code an.
    file_path = 'db.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            loaded_database = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Fehler beim Laden der Datenbank.")
        return

    #entry = next((entry for entry in loaded_database if entry['searchobject_channel'] == str(channel_id)), None)
    #if not entry:
     #   print(f"⚠️ Kein Eintrag für die Channel-ID {channel_id} gefunden. Angebot wird nicht gesendet.")
      #  return

    embed = discord.Embed(
        title=angebot.title,
        url=angebot.link,
        color=5814783
    )
    embed.add_field(name="Preis", value=f"{angebot.price}€", inline=True)
    embed.add_field(name="Größe", value=angebot.size, inline=True)
    embed.add_field(name="Zustand", value=angebot.condition, inline=True)
    embed.add_field(name="Beschreibung", value=angebot.description, inline=True)
    if angebot.image_url != "Kein Bild gefunden":
        embed.set_image(url=angebot.image_url)

    view = AngebotView(angebot.link)
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
