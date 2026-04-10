from tikhub import Client
import os



client = Client(base_url="https://api.tikhub.io", 
                api_key=os.getenv("TIKTOK_HUB_API_KEY", ""),
                proxies=None,
                max_retries=3,
                max_connections=50,
                timeout=60,
                max_tasks=50)

