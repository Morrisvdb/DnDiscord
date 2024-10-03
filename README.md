# DnDiscord

This is a simple discord bot that will help you to manage your D&D games.

## Running (Official Image)

The bot is available as a docker image in the docker hub. To run it you can use the following command:

First pull the image:
```bash
docker pull morrisjvdb/dndiscord:latest
```

Then run the image with the following command:

```bash
docker run -d --name dndiscord \
    -e DISCORD_TOKEN=${DISCORD_TOKEN} \
    -e DATABASE_NAME=${DATABASE_NAME} \
    -e DATABASE_USER=${DATABASE_USER} \
    -e DATABASE_PASSWORD=${DATABASE_PASSWORD} \
    -e DATABASE_HOST=${DATABASE_HOST} \
    --restart unless-stopped \
    dndiscord:latest
```

This will run the bot in detached mode and will take the credentials from a `.env` file. (see the Building section for more information)

## Building

To run the bot you will have to have an SQLdatabase.

Also make sure you have a `.env` file in the root of the project with the following content:

```.env
DISCORD_TOKEN=XXXXXXXX
DATABASE_NAME=bot
DATABASE_USER=bot
DATABASE_PASSWORD=XXXXXXXX
DATABASE_HOST=127.0.0.1
```

Then run the command `docker-compose up` to build and start the bot.


## Usage

For instructions on how to use the bot run the `/help` command in your discord server.