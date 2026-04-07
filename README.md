# Discord Server Archive Bot

A Python-based Discord bot designed to archive server history into an LLM-queryable local SQLite database. It performs bulk backups of past messages and continuously listens for new messages to keep the database synchronized.

## Features

* **Smart Scraping:** Remembers the last scraped message ID and only fetches new messages, saving API calls.
* **Continuous Sync:** Automatically adds new messages, links, and attachments to the database in real-time.
* **LLM-Ready Schema:** Organizes data cleanly into `channels` and `messages` tables, making it perfect for Text-to-SQL RAG pipelines.
* **Portable Database:** Dynamically creates the `server_archive.db` file in the same directory as the script, ensuring it works seamlessly across different machines and operating systems.
* **Rate-Limit Handling:** Utilizes `discord.py`'s built-in asynchronous rate-limit management to respect Discord's API limits safely.

## Prerequisites

* Python 3.8 or higher
* A Discord Bot Token

## Installation

1. **Clone the repository:**

   git clone (https://github.com/z2Z7T/Discord-Scraper)
   cd Discord-Scraper


2. **Install the required dependencies:**

   pip install discord.py aiosqlite


## Discord Bot Setup (Critical)

To read message history and content, the bot requires specific permissions from the Discord Developer Portal:

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a New Application and navigate to the **Bot** tab.
3. Under **Privileged Gateway Intents**, you **must** toggle on:
   * **Message Content Intent**
   * **Server Members Intent**
4. Generate your bot token and keep it secure.
5. Under **OAuth2 > URL Generator**, select the `bot` scope and the following text permissions: `Read Messages/View Channels`, `Read Message History`, and `Send Messages`. Use the generated URL to invite the bot to your server.

## Configuration

Open `bot.py` and replace the placeholder at the very bottom with your actual bot token:

bot.run('YOUR_BOT_TOKEN_HERE')


## Usage

1. **Start the bot:**

   python bot.py

   You should see a terminal message indicating the bot has logged in and where the database is routed.

2. **Trigger the initial backup:**
   In any text channel in your Discord server, type:

   !backup

   *Note: Only the owner of the Discord application can trigger this command. The bot will DM the server owner upon completion.*

## Database Structure

The script generates a `server_archive.db` SQLite file with two tables:

**`channels`**
* `channel_id` (INTEGER PRIMARY KEY)
* `channel_name` (TEXT)

**`messages`**
* `message_id` (INTEGER PRIMARY KEY)
* `channel_id` (INTEGER)
* `author` (TEXT)
* `content` (TEXT)
* `timestamp` (TEXT)
* `attachments` (TEXT) - Comma-separated URLs
* `links` (TEXT) - Comma-separated URLs

## Viewing the Data

Because SQLite databases are compiled binaries, do not open `.db` files in standard text editors. To view your data, use one of the following:

* **Command Line:** Run `sqlite3 server_archive.db` in your terminal.
* **VS Code:** Install the **SQLite Viewer** extension.
* **GUI:** Download and open the file in **DB Browser for SQLite**.