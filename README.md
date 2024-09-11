# DnDiscord

This is a simple discord bot that will help you to manage your D&D games.

## Installation

For now you can only build the code from the source yourself. We will soon add a docker image.

To run this bot locally simple clone this repo and make sure you have a database available or modify the code to use a different storage.

Make sure you have a `.env` file in the root of the project with the following content:

```.env
DISCORD_TOKEN=XXXXXXXX
DATABASE_NAME=bot
DATABASE_USER=bot
DATABASE_PASSWORD=XXXXXXXX
DATABASE_HOST=127.0.0.1
```

To run the bot simply run the `main.py` file.

## Usage

For instructions on how to use the bot run the `/help` command in your discord server.