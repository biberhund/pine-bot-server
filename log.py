# coding=utf-8

import logging
import logging.handlers

from config import *

logger = logging.getLogger(__name__)

# Helpers
console_handler = logging.StreamHandler()

# Formatters
shortest_formatter = logging.Formatter('%(message)s')
short_formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
long_formatter = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s')

# Handlers
# console
console_handler = logging.StreamHandler()
console_handler.setFormatter(short_formatter)
console_handler.setLevel(logging.INFO)

# File
file_handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME,
                                                        when='D', backupCount=99, delay=True)
file_handler.setFormatter(long_formatter)
file_handler.setLevel(logging.DEBUG)

# Discord
import threading
import queue
discord_thread = None
discord_queue = queue.Queue()
discord_handler = logging.handlers.QueueHandler(discord_queue)
discord_handler.setFormatter(shortest_formatter)
discord_handler.setLevel(logging.CRITICAL)
discord_conf = dict(
    url=DISCORD_URL,
    name=DISCORD_NAME,
    avatar_url=DISCORD_AVATAR_URL,
)
import requests
def discord_sender ():
    while True:
        msg = discord_queue.get()
        if msg is None:
            break
        if msg.startswith('fail to send to Disocrd'):
            continue
        data = {
            "content": msg,
            "username": discord_conf['name'] or DEFAULT_DISCORD_NAME,
            "avatar_url": discord_conf['avatar_url'] or DEFAULT_DISCORD_AVATAR_URL,
        }
        try:
            r = requests.post(discord_conf['url'], data=data)
            if r.status_code != 204:
                logger.error(f'fail to send to Discord: {r.status_code}')
        except Exception as e:
            logger.error(f'fail to send to Discord: {e}')


## App logger
app_logger = logging.getLogger()
app_logger.addHandler(console_handler)
app_logger.setLevel(logging.DEBUG)

# load logging conf
import os
if os.path.exists('./logging.conf'):
    from logging import config
    config.fileConfig('./logging.conf', disable_existing_loggers=False)

# Turn on additional handler
if LOG_FILENAME:
    app_logger.addHandler(file_handler)
if DISCORD_URL:
    discord_thread = threading.Thread(target=discord_sender, daemon=True)
    discord_thread.start()
    app_logger.addHandler(discord_handler)

## Report incl. discord
def notify (logger, msg):
    logger.info(msg)
    if discord_thread:
        discord_queue.put(msg)
