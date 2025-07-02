import os
import requests
import json

# Get WooCommerce credentials from environment variables
wc_url = os.environ.get('WC_URL', 'https://store.zakawatt.dz')
wc_ck = os.environ.get('Consumer_key')
wc_cs = os.environ.get('Consumer_secret')

if not wc_ck or not wc_cs:
    print('WooCommerce API keys not found in environment variables.')
    exit(1)

session = requests.Session()
session.auth = (wc_ck, wc_cs)
headers = {'Content-Type': 'application/json'}

# Get all products (up to 100 per page)
page = 1
while True:
    get_url = f"{wc_url}/wp-json/wc/v3/products?per_page=100&page={page}"
    r = session.get(get_url, headers=headers)
    products = r.json()
    if not products:
        break
    for product in products:
        product_id = product['id']
        del_url = f"{wc_url}/wp-json/wc/v3/products/{product_id}?force=true"
        resp = session.delete(del_url, headers=headers)
        print(f"Deleted product ID: {product_id} Status: {resp.status_code}")
    page += 1
print("All products deleted.")
