import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import xml.etree.ElementTree as ET
from test_lmm import add_product_from_xml, update_product_from_xml, check_new_products, fetch_all_products
from juhuhu import API_ACCESS_TOKEN, STORE_URL
import threading


# Initialize a global variable to hold the file path
global_file_path = ""

# Initialize Tkinter window
root = tk.Tk()
root.title("Shopify Product Manager")

# Move this function definition up here
def threaded_perform_action():
    thread = threading.Thread(target=perform_action)
    thread.start()
# Add this near your other UI Widgets
output_text = tk.Text(root, height=10, width=50)
output_text.grid(row=6, column=0, columnspan=2)
scroll = tk.Scrollbar(root, command=output_text.yview)
scroll.grid(row=6, column=2, sticky='nsew')


# UI Functionality

def load_file():
    global global_file_path  # Declare the variable as global to modify it
    global_file_path = filedialog.askopenfilename()
    xml_tree = ET.parse(global_file_path)
    xml_root = xml_tree.getroot()
    manufacturers = {izdelek.find('proizvajalec').text for izdelek in xml_root.findall('izdelek')}
    manufacturer_dropdown['values'] = list(manufacturers)

def perform_action():
    output_text.insert(tk.END, "Starting perform_action...\n")

    
    global global_file_path  # Declare the variable as global to access it
    
    if not global_file_path:  # Check if a file has been loaded
        output_text.insert(tk.END, "No file loaded. Exiting perform_action.\n")
        return
    
    print(f"Using file: {global_file_path}")
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": API_ACCESS_TOKEN,
    }
    
    output_text.insert(tk.END, "Fetching all products from Shopify...\n")
    all_products_data = fetch_all_products(headers, STORE_URL)
    sku_to_product = {variant["sku"]: product for product in all_products_data for variant in product["variants"]}

    manufacturer = manufacturer_var.get()
    operation = operation_var.get()
    choices = [choice_var.get()]
    import_images = import_images_var.get() == 'Y'
    
    output_text.insert(tk.END, f"Selected Manufacturer: {manufacturer}\n")
    output_text.insert(tk.END, f"Selected Operation: {operation}\n")
    output_text.insert(tk.END, f"Selected Choices: {choices}\n")
    output_text.insert(tk.END, f"Import Images: {import_images}\n")
    
    xml_tree = ET.parse(global_file_path)
    xml_root = xml_tree.getroot()
    
    if operation == "Update":
        output_text.insert(tk.END, "Updating products...\n")
        for izdelek in xml_root.findall('izdelek'):
            proizvajalec = izdelek.find('proizvajalec').text
            if proizvajalec != manufacturer:
                continue
            updated_sku = update_product_from_xml(headers, STORE_URL, izdelek, sku_to_product, import_images, choices, [])
            output_text.insert(tk.END, f"Updated product with SKU {updated_sku}.\n")
        output_text.insert(tk.END, "Update complete.\n")
        
    elif operation == "Add New":
        output_text.insert(tk.END, "Adding new products...\n")
        for izdelek in xml_root.findall('izdelek'):
            proizvajalec = izdelek.find('proizvajalec').text
            if proizvajalec != manufacturer:
                continue
            added_sku = add_product_from_xml(headers, STORE_URL, izdelek, sku_to_product, import_images)
            output_text.insert(tk.END, f"Added product with SKU {added_sku}.\n")
        output_text.insert(tk.END, "Addition complete.\n")
        
    elif operation == "Check New":
        output_text.insert(tk.END, "Checking for new products...\n")
        new_skus = check_new_products(headers, STORE_URL, xml_root, sku_to_product, manufacturer)
        if new_skus:
            output_text.insert(tk.END, f"Found new products with SKUs: {', '.join(new_skus)}\n")
        else:
            output_text.insert(tk.END, "No new products found.\n")
        
    output_text.insert(tk.END, "perform_action complete.\n")




# UI Widgets
operation_var = tk.StringVar()
operation_dropdown = ttk.Combobox(root, textvariable=operation_var)
operation_dropdown['values'] = ['Update', 'Add New', 'Check New']
operation_dropdown.grid(row=0, column=1)
operation_label = tk.Label(root, text="Choose Operation: ")
operation_label.grid(row=0, column=0)

load_file_button = tk.Button(root, text="Load File", command=load_file)
load_file_button.grid(row=1, column=0, columnspan=2)

manufacturer_var = tk.StringVar()
manufacturer_dropdown = ttk.Combobox(root, textvariable=manufacturer_var)
manufacturer_dropdown.grid(row=2, column=1)
manufacturer_label = tk.Label(root, text="Choose Manufacturer: ")
manufacturer_label.grid(row=2, column=0)

choice_var = tk.StringVar()
choice_dropdown = ttk.Combobox(root, textvariable=choice_var)
choice_dropdown['values'] = ['Title', 'Description', 'Price', 'Inventory', 'Images']
choice_dropdown.grid(row=3, column=1)
choice_label = tk.Label(root, text="Choose what to update: ")
choice_label.grid(row=3, column=0)

import_images_var = tk.StringVar()
import_images_check = tk.Checkbutton(root, text="Import Images", variable=import_images_var, onvalue='Y', offvalue='N')
import_images_check.grid(row=4, column=0, columnspan=2)

execute_button = tk.Button(root, text="Execute", command=threaded_perform_action)
execute_button.grid(row=5, column=0, columnspan=2)

# Start Tkinter event loop
root.mainloop()
