from pyrogram import Client
import config
from ..logging import LOGGER

# Global lists to keep track of active assistants
assistants = []
assistantids = []

class Userbot(Client):
    def __init__(self):
        self.one = None
        self.two = None
        self.three = None
        self.four = None
        self.five = None

        # Loop to initialize clients dynamically
        for i in range(1, 6):
            string = getattr(config, f"STRING{i}", None)
            if string:
                client = Client(
                    name=f"PURVIAss{i}",
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=str(string),
                    no_updates=True,
                )
                # Assign to self.one, self.two, etc.
                if i == 1: self.one = client
                elif i == 2: self.two = client
                elif i == 3: self.three = client
                elif i == 4: self.four = client
                elif i == 5: self.five = client

    async def start(self):
        LOGGER(__name__).info("Starting Assistants...")
        
        # List of all potential clients
        clients = [
            (1, self.one), 
            (2, self.two), 
            (3, self.three), 
            (4, self.four), 
            (5, self.five)
        ]

        for i, client in clients:
            if client:
                try:
                    await client.start()
                    
                    # Auto join channels
                    try:
                        await client.join_chat("NOBITA_SUPPORT")
                        await client.join_chat("about_deadly_venom")
                    except Exception:
                        pass # Ignore error if already joined or banned

                    # Send notification to Logger Group
                    try:
                        await client.send_message(config.LOGGER_ID, f"Assistant {i} Started ✅")
                    except Exception:
                        LOGGER(__name__).error(
                            f"Assistant {i} failed to access Log Group. Make sure it is an admin!"
                        )
                        # We don't exit() here so other accounts can continue
                    
                    # Fetch and set account details
                    client.me = await client.get_me()
                    client.id = client.me.id
                    client.name = client.me.mention
                    client.username = client.me.username
                    
                    assistants.append(i)
                    assistantids.append(client.id)
                    
                    LOGGER(__name__).info(f"Assistant {i} Started as {client.me.first_name}")
                
                except Exception as e:
                    LOGGER(__name__).error(f"Assistant {i} failed to start: {str(e)}")

    async def stop(self):
        LOGGER(__name__).info("Stopping Assistants...")
        clients = [self.one, self.two, self.three, self.four, self.five]
        for client in clients:
            if client:
                try:
                    await client.stop()
                except Exception:
                    pass

# Note: This code is much cleaner and avoids the copy-paste errors 
# from the previous version. It handles up to 5 assistants automatically. 
