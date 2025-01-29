import requests
from bs4 import BeautifulSoup
import os
import json
from telegram import Bot
import asyncio
import logging

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TRADING_CARDS_URL = 'https://www.pokemoncenter.com/en-gb/category/trading-card-game'  # Verify URL
STORAGE_FILE = 'known_products.json'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_alert(message):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown')
    logger.info(f"Alert sent: {message}")

def load_known_products():
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, 'r') as f:
        return json.load(f)

def save_known_products(products):
    with open(STORAGE_FILE, 'w') as f:
        json.dump(products, f)

def scrape_products():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(TRADING_CARDS_URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    products = {}
    
    # Update selectors based on Pokémon Center’s HTML structure
    product_cards = soup.select('div.product-card')
    for card in product_cards:
        link = card.find('a', href=True)
        if link:
            url = f"https://www.pokemoncenter.com{link['href']}"
            name = card.find('div', class_='product-name').text.strip()
            stock = 'in stock' if 'Add to Cart' in card.text else 'out of stock'
            products[url] = {'name': name, 'stock': stock}
    return products

async def monitor():
    known_products = load_known_products()
    current_products = scrape_products()
    
    # Detect new products
    new_products = {url: data for url, data in current_products.items() if url not in known_products}
    for url, data in new_products.items():
        await send_alert(f"🎉 **New Product Detected!**\n\n*{data['name']}*\n{url}")
    
    # Detect stock changes
    for url, data in current_products.items():
        if url in known_products:
            old_stock = known_products[url]['stock']
            if old_stock == 'out of stock' and data['stock'] == 'in stock':
                await send_alert(f"🛒 **Back in Stock!**\n\n*{data['name']}*\n{url}")
    
    save_known_products(current_products)

if __name__ == '__main__':
    asyncio.run(monitor())
