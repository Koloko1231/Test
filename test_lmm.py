import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import requests
import time
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
from copy import deepcopy






def fetch_all_products(headers, store_url):
    products_url = f"{store_url}/products.json?limit=250"
    products = []
    while products_url:
        response = requests.get(products_url, headers=headers)
        data = response.json()
        products.extend(data["products"])
        link_header = response.headers.get("Link")
        if link_header is None:
            break
        links = link_header.split(", ")
        next_link = None
        for link in links:
            if "rel=\"next\"" in link:
                next_link = link[link.index("<") + 1:link.index(">")]
                break
        products_url = next_link
    return products




def add_product_from_xml(headers, store_url, product_data, sku_to_product, import_images=True):
    sku_text = product_data.find('pro_sifra').text
    sku = sku_text.split()[0] if "AKC" in sku_text else sku_text
    if sku in sku_to_product:
        print(f"Product with SKU {sku} already exists. Skipping.")
        return False
    ean = product_data.find('ean').text
    title = f"{product_data.find('proizvajalec').text} {product_data.find('naziv').text} {product_data.find('mera').text} ({sku})"
    body_html = product_data.find('opis').text
    inventory_text = product_data.find('zaloga').text
    inventory = 10 if inventory_text == '10+' else int(inventory_text)
    price = round(float(product_data.find('cena').text) * 1.22 * 1.35, 2)
    vendor = product_data.find('proizvajalec').text
    image_url = product_data.find('slika').text

    # Get current date for the tag
    date_tag = time.strftime("%Y-%m-%d")
    
    # Create the product
    product = {
        "product": {
            "title": title,
            "body_html": body_html,
            "vendor": vendor,
            "tags": date_tag,
            "variants": [
                {
                    "sku": sku,
                    "price": price,
                    "barcode": ean,
                    "inventory_management": "shopify",  # Enable inventory tracking
                    "inventory_policy": "continue"  # Continue selling when out of stock    
                }
            ],
        }
    }

    # Only add the image if import_image is True
    if import_images:
        product["product"]["images"] = [{"src": image_url}]



    create_product_url = f"{store_url}/products.json"
    create_product_response = requests.post(create_product_url, json=product, headers=headers)

    if create_product_response.status_code != 201:
        print(f"Error creating product with SKU {sku}: {create_product_response.status_code} {create_product_response.text}")
        failed_products.append(product_data)  # Append the product data to the failed products tree
        return False

    created_product = create_product_response.json()["product"]
    variant_id = created_product["variants"][0]["id"]
    inventory_item_id = created_product["variants"][0]["inventory_item_id"]

    # Set the inventory quantity
    locations_url = f"{store_url}/locations.json"
    locations_response = requests.get(locations_url, headers=headers)
    locations_data = locations_response.json()
    location_id = locations_data["locations"][0]["id"]

    inventory_levels_update_data = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available": inventory,
    }
    inventory_levels_update_url = f"{store_url}/inventory_levels/set.json"
    inventory_levels_update_response = requests.post(inventory_levels_update_url, json=inventory_levels_update_data, headers=headers)

    if inventory_levels_update_response.status_code != 200:
        print(f"Error setting inventory for product {sku}: {inventory_levels_update_response.status_code} {inventory_levels_update_response.text}")
        return False

    print(f"Added product with SKU {sku}.")
    return sku
time.sleep(0.6)







def update_product_from_xml(headers, store_url, product_data, sku_to_product, import_images, choices, failed_products):
    sku_text = product_data.find('pro_sifra').text
    sku = sku_text.split()[0] if sku_text and "AKC" in sku_text else sku_text
    if sku not in sku_to_product:
        print(f"Product with SKU {sku} does not exist. Skipping.")
        return False

    # Fetch the product and variant IDs
    product_id = sku_to_product[sku]['id']
    variant_id = sku_to_product[sku]['variants'][0]['id']

    # Prepare the updated product data
    ean = product_data.find('ean').text
    title = f"{product_data.find('proizvajalec').text} {product_data.find('naziv').text} {product_data.find('mera').text} ({sku})"
    inventory_text = product_data.find('zaloga').text
    inventory = 10 if inventory_text == '10+' else int(inventory_text)
    price = round(float(product_data.find('cena').text) * 1.22 * 1.35, 2)
    vendor = product_data.find('proizvajalec').text
    image_url = product_data.find('slika').text

    # Update the product
    product = {
        "product": {
            "id": product_id,
            "title": title,
            "vendor": vendor,
            "variants": [
                {
                    "id": variant_id,
                    "sku": sku,
                    "price": price,
                    "barcode": ean,
                    "inventory_policy": "continue"  # Continue selling when out of stock
                }
            ],
        }
    }

    # Only add the image if import_image is True
    if import_images:
        product["product"]["images"] = [{"src": image_url}] 


    # Update the selected fields
    if '1' in choices:
        product["product"]["title"] = title
    if '2' in choices:
        # Only update body_html if it's not empty
        body_html = product_data.find('opis').text
        if body_html and body_html.strip():
            product["product"]["body_html"] = body_html
    if '3' in choices:
        product["product"]["variants"][0]["price"] = price
    if '4' in choices:
        product["product"]["variants"][0]["inventory_management"] = "shopify"
    if import_images:
        product["product"]["images"] = [
            {
                "src": image_url
            }
        ]
    else:
        product["product"].pop("images", None)

    update_product_url = f"{store_url}/products/{product_id}.json"
    update_product_response = requests.put(update_product_url, json=product, headers=headers)

    if update_product_response.status_code != 200:
        print(f"Error updating product with SKU {sku}: {update_product_response.status_code} {update_product_response.text}")
        failed_products.append(product_data)  # Append the product data to the failed products tree
        return False

    # Update the inventory
    inventory_item_id = sku_to_product[sku]['variants'][0]['inventory_item_id']

    # Set the inventory quantity
    locations_url = f"{store_url}/locations.json"
    locations_response = requests.get(locations_url, headers=headers)
    locations_data = locations_response.json()

    if 'locations' not in locations_data:
        print(f"Error retrieving locations for product {sku}: {locations_response.status_code} {locations_response.text}")
        return False

    location_id = locations_data["locations"][0]["id"]

    inventory_levels_update_data = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available": inventory,
    }
    inventory_levels_update_url = f"{store_url}/inventory_levels/set.json"
    time.sleep(2)  # Add a delay here
    inventory_levels_update_response = requests.post(inventory_levels_update_url, json=inventory_levels_update_data, headers=headers)
    time.sleep(2)  # Add a 2-second delay before the next request

    # After updating the product
    if inventory_levels_update_response.status_code != 200:
        print(f"Error setting inventory for product {sku}: {inventory_levels_update_response.status_code} {inventory_levels_update_response.text}")
        return False

    # Set a unique number as metafield (current timestamp)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    metafield = {
        "metafield": {
            "namespace": "custom",
            "key": "last_update",
            "value": current_time,
            "type": "single_line_text_field",
        }
    }

    metafields_url = f"{store_url}/products/{product_id}/metafields.json"
    metafields_response = requests.post(metafields_url, json=metafield, headers=headers)

    if metafields_response.status_code != 201:
        print(f"Error setting metafield for product {sku}: {metafields_response.status_code} {metafields_response.text}")
        return False

    print(f"Updated product with SKU {sku}.")
    return sku





def check_new_products(headers, store_url, xml_root, sku_to_product, manufacturer):
    new_products = []
    new_skus = []  # A list to hold SKUs of new products
    checked_count = 0

    for izdelek in xml_root.findall('izdelek'):
        proizvajalec = izdelek.find('proizvajalec').text
        if proizvajalec != manufacturer:
            continue

        sku_text = izdelek.find('pro_sifra').text

        # Check if sku_text is not None before splitting it
        if sku_text:
            sku = sku_text.split()[0]
            checked_count += 1
            print(f"Checking SKU: {sku}")

            if sku not in sku_to_product:
                print(f"New product found with SKU: {sku}")
                new_products.append(deepcopy(izdelek))
                new_skus.append(sku)  # Add the new SKU to the list


    if new_products:
        new_products_xml = ET.Element("new_products")
        new_products_xml.extend(new_products)
        new_products_tree = ET.ElementTree(new_products_xml)

        with open('new_products.xml', 'wb') as file:
            new_products_tree.write(file)

        print(f"Checked {checked_count} products. Found {len(new_products)} new products. Saved to 'new_products.xml'.")
    else:
        print(f"Checked {checked_count} products. No new products found.")

    return new_skus  # Return the list of new SKUs


def main(operation, xml_path, manufacturer, update_choices=None, import_images=False):
    
    failed_products = ET.Element("failed_products")

    # User can choose to update, add new products, or check for new products
    user_choice = input("Do you want to [U]pdate, [A]dd new products, or [C]heck for new products? ")

    if user_choice.lower() not in ['u', 'a', 'c']:
        print("Invalid input. Please enter either 'U' for Update, 'A' for Add or 'C' for Check.")
        return

    window = tk.Tk()
    window.withdraw()

    xml_path = filedialog.askopenfilename()
    xml_tree = ET.parse(xml_path)
    xml_root = xml_tree.getroot()

    # Fetch all products from Shopify
    from juhuhu import API_ACCESS_TOKEN, STORE_URL

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": API_ACCESS_TOKEN,
    }

    all_products_data = fetch_all_products(headers, STORE_URL)

    # Map SKU to product data
    sku_to_product = {variant["sku"]: product for product in all_products_data for variant in product["variants"]}

    # Collect all unique manufacturers
    manufacturers = {izdelek.find('proizvajalec').text for izdelek in xml_root.findall('izdelek')}

    # Prompt for manufacturer name
    print("Choose a manufacturer from the list below:")
    for i, manufacturer in enumerate(manufacturers, start=1):
        print(f"{i}. {manufacturer}")
    manufacturer_choice = int(input("Enter the number of the manufacturer you want to update: "))
    manufacturer = list(manufacturers)[manufacturer_choice - 1]

    if user_choice.lower() == 'c':
        # Check for new products
        check_new_products(headers, STORE_URL, xml_root, sku_to_product, manufacturer)
        return

    # For updating or adding products, prompt the user for more options
    print("What do you want to update? (Enter numbers separated by comma)")
    print("1. Title")
    print("2. Description")
    print("3. Price")
    print("4. Inventory")
    choices = input("Enter the numbers of the items you want to update: ").split(',')

    # Ask user if they want to import images
    import_images = input("Do you want to import images? (Y/N): ")
    import_images = import_images.lower() == 'y'

    window = tk.Tk()
    window.title("Processing")

    progress = ttk.Progressbar(window, length=500, mode='determinate')
    progress.pack()
    progress['maximum'] = len(xml_root)
    window.update()

    product_found = False
    for izdelek in xml_root.findall('izdelek'):
        sku = izdelek.find('pro_sifra').text
        proizvajalec = izdelek.find('proizvajalec').text

        if proizvajalec != manufacturer:
            continue

        product_found = True
        if user_choice.lower() == 'u':
            # Update the product
            update_product_from_xml(headers, STORE_URL, izdelek, sku_to_product, import_images, choices, failed_products)
        elif user_choice.lower() == 'a':
            # Add new product
            if sku in sku_to_product:
                print(f"Product with SKU {sku} already exists. Skipping.")
                continue
            add_product_from_xml(headers, STORE_URL, izdelek, import_images)

        progress.step()
        window.update()

    # Save the failed products to an XML file
    with open('failed_products.xml', 'wb') as file:
        ET.ElementTree(failed_products).write(file)

    if not product_found:
        print("No products found for this manufacturer. Please try again with a correct manufacturer name.")

    window.destroy()

if __name__ == "__main__":
    main()
