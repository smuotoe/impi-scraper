import os

from discord.ext import tasks
import datetime as dt
import discord

from main import read_file


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # an attribute we can access from our task
        self.impi_status = read_file('impi_status.txt', '0')

        # start the task to run in the background
        # self.my_background_task.start()

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    @tasks.loop(seconds=60)  # task runs every 60 seconds
    async def my_background_task(self):
        channel = self.get_channel(9241)  # channel ID goes here
        self.counter = read_file('impi_status.txt', '0')
        if not self.counter:

            await channel.send(f'{dt.datetime.now()}: Script running...')

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in


client = MyClient()
client.run('ODg0MjMyNDAwNzkwNTA3NTMy.YTVfmA.s1pm-Dmd8Uurg9CDL-uNUzGIoK4')
