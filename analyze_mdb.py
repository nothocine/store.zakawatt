

import sys
import pyodbc
import os
import requests
import json

# Path to your .mdb file

mdb_file = os.path.abspath('zakawatt_2025.mdb')

# Database password
db_password = 'Group'

# Connection string for Access .mdb files (32-bit driver) with password
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={mdb_file};PWD={db_password};'
)




def sync_products_with_woocommerce(tarif_id=7):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Get WooCommerce credentials from environment variables
        wc_url = os.environ.get('WC_URL', 'https://store.zakawatt.dz')
        wc_ck = os.environ.get('Consumer_key')
        wc_cs = os.environ.get('Consumer_secret')
        if not wc_ck or not wc_cs:
            print('WooCommerce API keys not found in environment variables.')
            return

        # Select reference, designation, quantity from Produit and prixvente from PrixVente
        query = '''
            SELECT p.Reference, p.Designation, p.Quantite, pv.PrixVente
            FROM Produit p
            INNER JOIN PrixVente pv ON p.CleProduit = pv.CleProduit
            WHERE pv.CleTarif = ?
        '''
        cursor.execute(query, (tarif_id,))
        rows = cursor.fetchall()

        session = requests.Session()
        session.auth = (wc_ck, wc_cs)
        headers = {'Content-Type': 'application/json'}

        for row in rows:
            ref = row.Reference if row.Reference is not None else ""
            des = row.Designation if row.Designation is not None else ""
            qty = row.Quantite if row.Quantite is not None else 0
            prix = row.PrixVente if row.PrixVente is not None else 0

            # Check if product exists by SKU (reference)
            get_url = f"{wc_url}/wp-json/wc/v3/products?sku={ref}"
            r = session.get(get_url, headers=headers)
            if r.status_code == 200 and r.json():
                # Update existing product
                product_id = r.json()[0]['id']
                update_url = f"{wc_url}/wp-json/wc/v3/products/{product_id}"
                data = {
                    "name": des,
                    "regular_price": str(prix),
                    "stock_quantity": qty,
                    "manage_stock": True
                }
                resp = session.put(update_url, headers=headers, data=json.dumps(data))
                print(f"Updated: {ref} - {des} (ID: {product_id}) Status: {resp.status_code}")
            else:
                # Create new product
                create_url = f"{wc_url}/wp-json/wc/v3/products"
                data = {
                    "name": des,
                    "sku": ref,
                    "regular_price": str(prix),
                    "stock_quantity": qty,
                    "manage_stock": True,
                    "type": "simple"
                }
                resp = session.post(create_url, headers=headers, data=json.dumps(data))
                print(f"Created: {ref} - {des} Status: {resp.status_code}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")



if __name__ == "__main__":
    # Ensure UTF-8 output for Windows terminals
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    sync_products_with_woocommerce(7)