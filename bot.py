import discord
from discord.ext import commands
import aiosqlite
from pathlib import Path
import re
import os
from dotenv import load_dotenv

load_dotenv()

# Dynamically get the directory where this exact .py file lives
BASE_DIR = os.getenv('DATABASE_FOLDER')

# Route the database to that exact folder
DB_PATH = BASE_DIR / "server_archive.db"

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def setup_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                channel_id INTEGER PRIMARY KEY,
                channel_name TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                author TEXT,
                content TEXT,
                timestamp TEXT,
                attachments TEXT,
                links TEXT
            )
        ''')
        await db.commit()

@bot.event
async def on_ready():
    await setup_db()
    print(f'Logged in as {bot.user} | DB routed to {DB_PATH}')

@bot.command()
@commands.is_owner() # Only you can run this
async def backup(ctx):
    await ctx.send("Starting server backup. This may take a while depending on server size...")
    guild = ctx.guild
    text_channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
    
    channels_backed_up = 0
    total_channels = len(text_channels)

    async with aiosqlite.connect(DB_PATH) as db:
        for channel in text_channels:
            try:
                # Add channel to DB
                await db.execute('INSERT OR IGNORE INTO channels (channel_id, channel_name) VALUES (?, ?)', 
                                 (channel.id, channel.name))
                
                # Smart Scraping: Check the latest message ID we already have for this channel
                async with db.execute('SELECT MAX(message_id) FROM messages WHERE channel_id = ?', (channel.id,)) as cursor:
                    row = await cursor.fetchone()
                    latest_msg_id = row[0] if row else None

                # Fetch history. discord.py handles rate limits (429s) automatically here.
                # If latest_msg_id exists, we only fetch messages *after* it via the 'after' parameter.
                after_obj = discord.Object(id=latest_msg_id) if latest_msg_id else None
                
                async for msg in channel.history(limit=None, after=after_obj, oldest_first=True):
                    # Extract URLs using regex
                    links = re.findall(r'(https?://[^\s]+)', msg.content)
                    links_str = ",".join(links) if links else None
                    
                    # Extract attachments (files, images, audio)
                    attachments = ",".join([a.url for a in msg.attachments]) if msg.attachments else None

                    await db.execute('''
                        INSERT OR IGNORE INTO messages 
                        (message_id, channel_id, author, content, timestamp, attachments, links) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (msg.id, channel.id, str(msg.author), msg.content, str(msg.created_at), attachments, links_str))
                
                await db.commit()
                channels_backed_up += 1
                print(f"Backed up {channel.name}")

            except discord.Forbidden:
                print(f"Missing access to {channel.name}")
            except Exception as e:
                print(f"Error backing up {channel.name}: {e}")

    # DM the Server Owner
    try:
        await guild.owner.send(f"✅ **Backup Complete:** {channels_backed_up}/{total_channels} channels successfully synced to the database.")
    except discord.Forbidden:
        print("Could not DM the server owner (their DMs are closed).")

@bot.event
async def on_message(message):
    # Ignore the bot's own messages
    if message.author == bot.user:
        return

    # Automatically add new messages to the database to keep it up to speed
    if isinstance(message.channel, discord.TextChannel):
        async with aiosqlite.connect(DB_PATH) as db:
            links = re.findall(r'(https?://[^\s]+)', message.content)
            links_str = ",".join(links) if links else None
            attachments = ",".join([a.url for a in message.attachments]) if message.attachments else None

            await db.execute('''
                INSERT OR IGNORE INTO messages 
                (message_id, channel_id, author, content, timestamp, attachments, links) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (message.id, message.channel.id, str(message.author), message.content, str(message.created_at), attachments, links_str))
            await db.commit()

    # Process commands if there are any
    await bot.process_commands(message)

# Grab the token from the environment variable
TOKEN = os.getenv('DISCORD_TOKEN')

# Run the bot
bot.run(TOKEN)