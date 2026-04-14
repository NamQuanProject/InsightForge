import os
import httpx
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Cloudflare Configuration
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
# Using SDXL Base for high-quality generations
MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0" 

# Initialize FastMCP
mcp = FastMCP("ImageGenerating")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool: Generate Image via Cloudflare
# ---------------------------------------------------------------------------

@mcp.tool()
async def generate_image(
    prompt: str,
    output_path: str = "generated_image.png",
    num_steps: int = 20,
    guidance: float = 7.5
) -> dict:
    """
    Generate an image from a prompt using Cloudflare Workers AI (Stable Diffusion XL).

    Args:
        prompt: Detailed description of the image.
        output_path: Local file path to save the resulting PNG.
        num_steps: Number of inference steps (default 20).
        guidance: How closely the model follows the prompt (default 7.5).

    Returns:
        dict: success status, saved_path, or error message.
    """
    if not ACCOUNT_ID or not API_TOKEN:
        return {"success": False, "error": "Cloudflare credentials not set in environment."}

    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{MODEL}"
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
        "num_steps": num_steps,
        "guidance": guidance
    }

    try:
        # Increase timeout for image generation
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"Requesting image generation from Cloudflare for prompt: {prompt[:50]}...")
            
            response = await client.post(url, headers=headers, json=payload)
            
            # Check for Cloudflare specific errors
            if response.status_code != 200:
                return {
                    "success": False, 
                    "error": f"Cloudflare API error {response.status_code}: {response.text}"
                }

            # Cloudflare returns raw binary data for images
            image_bytes = response.content

            # Save to disk
            with open(output_path, "wb") as f:
                f.write(image_bytes)

            logger.info(f"Image successfully saved to {output_path}")

            return {
                "success": True,
                "saved_path": output_path,
                "model_used": MODEL,
                "error": None
            }

    except httpx.RequestError as e:
        return {"success": False, "error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport = "stdio")