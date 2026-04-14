from cloudflare import Cloudflare
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import requests
import os

load_dotenv()
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", None)
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", None)
# Using an image generation model instead of llama
MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0" 

url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{MODEL}"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# 2. The Prompt
payload = {
    "prompt": "A futuristic cyberpunk city with neon lights and flying cars, high detail, 8k"
}

# 3. Execution
response = requests.post(url, headers=headers, json=payload)

# 4. Handling the Output
if response.status_code == 200:
    # Image models return binary data (the actual image bytes)
    with open("generated_image.png", "wb") as f:
        f.write(response.content)
    print("Success! Image saved as generated_image.png")
else:
    print(f"Error {response.status_code}: {response.text}")