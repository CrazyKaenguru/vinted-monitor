
# bot.py
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import os
load_dotenv()  # Load environment variables from .env file
TOKEN = os.getenv("DISCORD_BOT_TOKEN")


# Erstelle ein Bot-Objekt mit den entsprechenden Präfixen
intents = discord.Intents.default()
intents.message_content = True  # Ermöglicht es dem Bot, Nachrichten zu lesen
bot = commands.Bot(command_prefix='!', intents=intents)

# Beispielangebot
angebot = {
    "titel": "Ralph Lauren Hemd",
    "beschreibung": "Stylisches Ralph Lauren Hemd in gutem Zustand.",
    "preis": "25,00",
    "größe": "M / 38 / 10",
    "zustand": "Gut",
    "marke": "Ralph Lauren",
    "link": "https://www.vinted.de/items/5541013082-pantalon-ralph-lauren-bleu-clair-w40",
    "bilder": [
        "https://example.com/image1.jpg",  # Hauptbild
        "https://example.com/image2.jpg",  # Thumbnail
        "https://example.com/image3.jpg",  # Weitere Bilder
        "https://example.com/image4.jpg"   # Weitere Bilder
    ],
    "benutzername": "ronnyvintage13",
    "benutzer_link": "https://www.vinted.de/member/199626532-ronnyvintage13",
    "benutzer_bild": "https://example.com/user_image.jpg",
}

# Ereignis: Bot ist online und bereit
@bot.event
async def on_ready():
    print(f'Bot ist eingeloggt als {bot.user}')
   # await send_offer()

# Funktion, um ein Angebot an Discord zu senden
async def send_offer(angebot):
    embed = discord.Embed(
        title=angebot.title,
        description=angebot.title,
        url=angebot.link,
        color=5814783
    )

    embed.add_field(name="price", value=f"{angebot.price}€", inline=True)
    embed.add_field(name="size", value=angebot.size, inline=True)
    embed.add_field(name="condition", value=angebot.condition, inline=True)
    embed.add_field(name="description", value=angebot.description, inline=True)
    
    #embed.set_image(url=angebot['bilder'][0])  # Hauptbild
    #embed.set_thumbnail(url=angebot['bilder'][1])  # Thumbnail
    
    #embed.add_field(name="Weitere Bilder", value='\n'.join([f"[Bild {i+1}]({bild})" for i, bild in enumerate(angebot['bilder'][2:])]), inline=False)
    #embed.add_field(name="Details", value=f"[Zum Angebot]({angebot['link']})", inline=False)

    # Sende das Embed in einen Channel
    channel = bot.get_channel(950418591088529451)  # Ersetze mit der echten Kanal-ID
    await channel.send(embed=embed)

# Funktion zum Starten des Bots
async def start_bot():
    await bot.start(TOKEN)

