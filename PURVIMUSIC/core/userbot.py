from pyrogram import Client
import config
from ..logging import LOGGER

assistants = []
assistantids = []

class Userbot(Client):
    def __init__(self):
        self.clients = []
        # Hum 5 assistants tak handle karenge
        for i in range(1, 6):
            session = getattr(config, f"STRING{i}", None)
            if session:
                client = Client(
                    name=f"PURVIAss{i}",
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=str(session),
                    no_updates=True,
                )
                setattr(self, f"client{i}", client) # dynamic attributes like self.client1
                self.clients.append((i, client))

        # Backward compatibility ke liye (Purane code ke references ke liye)
        self.one = getattr(self, "client1", None)
        self.two = getattr(self, "client2", None)
        self.three = getattr(self, "client3", None)
        self.four = getattr(self, "client4", None)
        self.five = getattr(self, "client5", None)

    async def start(self):
        LOGGER(__name__).info("Starting Assistants...")
        
        for i, client in self.clients:
            try:
                await client.start()
                
                # Chats Join Karwana
                try:
                    await client.join_chat("Exampurrs")
                    await client.join_chat("FONT_CHANNEL_01")
                except Exception:
                    pass

                # Log Group mein message bhejna
                try:
                    await client.send_message(config.LOGGER_ID, f"Assistant {i} Started")
                except Exception:
                    LOGGER(__name__).error(
                        f"Assistant {i} failed to access Log Group. Promote it as admin!"
                    )
                    # Exit nahi karenge taaki baaki accounts chalte rahein
                
                # User details set karna
                client.me = await client.get_me()
                client.id = client.me.id
                client.name = client.me.mention
                client.username = client.me.username
                
                assistants.append(i)
                assistantids.append(client.id)
                LOGGER(__name__).info(f"Assistant {i} Started as {client.name}")
                
            except Exception as e:
                LOGGER(__name__).error(f"Assistant {i} failed to start: {str(e)}")

    async def stop(self):
        LOGGER(__name__).info("Stopping Assistants...")
        for _, client in self.clients:
            try:
                await client.stop()
            except Exception:
                pass
