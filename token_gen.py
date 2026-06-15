import tkinter as tk
from tkinter import ttk,font,simpledialog, messagebox
import requests
import evdev
import threading
import json
import time
from PIL import Image, ImageTk
from io import BytesIO
import logging
from datetime import datetime
from escpos.printer import File
from evdev import InputDevice

global ready
ready = True

import socket

def is_connected(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

# Wait for internet connection before proceeding
while not is_connected():
    print("Waiting for internet connection...")
    time.sleep(2)


product_get_url_Verification= 'https://registrationandtouristcare.uk.gov.in/api/verification/scan/verifyuserbydevice'
product_post_url_Token= 'https://registrationandtouristcare.uk.gov.in/api/verification/scan/generatemachinetoken'
point_url = 'https://registrationandtouristcare.uk.gov.in/api/masterretrieval/common/tokenverificationpoint'

p = File("/dev/usb/lp0")

# Barcode Scanner Setup
dev = evdev.InputDevice('/dev/input/event0')

# Scan code mapping
scan_codes = {
    0: None, 1: 'ESC', 2: '1', 3: '2', 4: '3', 5: '4', 6: '5', 7: '6', 8: '7', 9: '8',
    10: '9', 11: '0', 12: '-', 13: '=', 14: 'BKSP', 15: 'TAB', 16: 'Q', 17: 'W', 18: 'E', 19: 'R',
    20: 'T', 21: 'Y', 22: 'U', 23: 'I', 24: 'O', 25: 'P', 26: '[', 27: ']', 28: 'CRLF', 29: 'LCTRL',
    30: 'A', 31: 'S', 32: 'D', 33: 'F', 34: 'G', 35: 'H', 36: 'J', 37: 'K', 38: 'L', 39: ';',
    40: '"', 41: '', 42: 'LSHFT', 43: '\\', 44: 'Z', 45: 'X', 46: 'C', 47: 'V', 48: 'B', 49: 'N',
    50: 'M', 51: ',', 52: '.', 53: '/', 54: 'RSHFT', 56: 'LALT', 100: 'RALT'
}



# Tkinter GUI
root = tk.Tk()
root.title("Uttarakhand Tourism Verification")

# Make the window fullscreen and get the screen width and height
root.attributes('-fullscreen', True)
root.bind("<Escape>", lambda event: root.attributes('-fullscreen', False))

# Get screen width and height dynamically
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()


# Set the window size to match the screen size
root.geometry(f"{screen_width}x{screen_height}")
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Label for instructions
op = tk.Label(root, text="Scan Barcode:", font=("Arial", int(screen_width / 60)), anchor="center")
op.pack(pady=2.5)

# Entry Field (Auto-focus cursor)
barcode_entry = tk.Entry(root, font=("Arial", int(screen_width / 60)), justify="center")
barcode_entry.pack(pady=2.5)
barcode_entry.place(relx=0.65, rely=0.01, anchor="nw")
barcode_entry.focus()  # Keep cursor active

# Loader Label
loader_label = tk.Label(root, text="", font=("Arial", int(screen_width / 30)), fg="blue")
loader_label.pack(pady=5)
loader_label.place(relx=0.07, rely=0.15, anchor="nw")

# Label for displaying results
result_text = tk.StringVar()
result_label = tk.Label(root, textvariable=result_text, font=("Arial", int(screen_width / 80)), fg="blue", wraplength=350)
result_label.pack(pady=8)

# Calculate the row height dynamically based on screen size


row_height = screen_height // 5.5  # Divide available height by number of rows (5 rows)

# Style for the Treeview
style = ttk.Style()
style.configure("Treeview", font=("Arial", int(screen_width / 30)), rowwidth=100, rowheight=row_height)

# Image display area
image_label = tk.Label(root, width=int(screen_width / 3.7), height=int(screen_height / 1.8))  # Set area
image_label.pack(pady=20)
image_label.place(relx=0.015, rely=0.25, anchor="nw")  # Use relative positioning



# Constants
CORRECT_PASSWORD = "red"
# ---- Fetch category options from API ----
def fetch_category_options():
    try:
        response = requests.get(point_url)
        response.raise_for_status()
        data = response.json()

        if "data" in data and isinstance(data["data"], list):
            options = {
                str(item["ID"]): item["Name"]
                for item in data["data"]
                if "ID" in item and "Name" in item
            }
            print("Fetched category options:", options)
            return options
        else:
            raise ValueError("Unexpected JSON structure")
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        messagebox.showerror("Error", f"Failed to fetch categories.\n{e}")
        return {}


dropdown_font_size = min(8, int(screen_width / 95))
dropdown_width_chars = max(25, int(screen_width / 35))

click_count = 0  # For admin access tracking

category_options = fetch_category_options()

# Handle case when category_options is empty
if not category_options:
    messagebox.showerror("Error", "No category options available.")
    root.destroy()  # Exit app gracefully
    exit()





# Set default key and value intelligently
default_key = "32" if "32" in category_options else next(iter(category_options))
default_value = category_options[default_key]

selected_option = tk.StringVar(value=default_value)
selected_category_key = tk.StringVar(value=default_key)



print("Dropdown options:", category_options)
print("Selected key:", selected_category_key.get())


label = tk.Label(root, text=f"Selected Key: {selected_category_key.get()}", font=("Arial", 14))
label.place(relx=0.5, rely=0.1, anchor="center")


def update_main_label():
    label.config(text=f"Selected Key: {selected_category_key.get()}")
# ---- Admin Panel Logic ----

def open_admin_window():
    admin_window = tk.Toplevel(root)
    admin_window.title("Admin Panel")

    # Optional: set size and center
    width = int(screen_width / 2.5)
    height = int(screen_height / 2.5)
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2)
    admin_window.geometry(f"{width}x{height}+{x}+{y}")

    # Flag to track if dropdown is unlocked (specific to this window)
    dropdown_unlocked = tk.BooleanVar(value=False)
    
   
    # Function called when dropdown value changes
    def on_dropdown_change(event):
        global selected_category_key
        if dropdown_unlocked.get():		
            for key, val in category_options.items():
                if val == selected_option.get():
                    selected_category_key.set(key)
                    update_main_label()
                    break
            dropdown.config(state="disabled")
            dropdown_unlocked.set(False)
            messagebox.showinfo("Locked", "Dropdown locked after one change.")
            admin_window.destroy()  # Close admin window after selection
	
	
	
    # Dropdown (disabled by default)
    dropdown = ttk.Combobox(
        admin_window,
        values=list(category_options.values()),
        font=("Arial", dropdown_font_size),
        state="disabled",
        width=dropdown_width_chars,
        textvariable=selected_option
    )
    dropdown.set(category_options[selected_category_key.get()])
    dropdown.place(relx=0.5, rely=0.2, anchor="n")

    dropdown.bind("<<ComboboxSelected>>", on_dropdown_change)

		
	

    # Password prompt to unlock dropdown
   
    
    def ask_password():
        password = simpledialog.askstring("Password", "Enter password:", show='*', parent=admin_window)
        if password == CORRECT_PASSWORD:
            dropdown.config(state="readonly")
            dropdown_unlocked.set(True)
        else:
            print('wrong password')

    unlock_button = tk.Button(admin_window, text="Unlock Dropdown", command=ask_password)
    unlock_button.place(relx=0.5, rely=0.5, anchor="n")



def get_selected_category_id():
    label = selected_option.get()
    for key, val in category_options.items():
        if val == label:
          return key
    return None
verification_point_id = get_selected_category_id()
print("Selected key:", verification_point_id)
    
    
    

# ---- Admin Button in Main Window ----

def on_admin_button_click():
    global click_count
    click_count += 1
    print(f"Admin button clicked {click_count} times")

    if click_count == 5:
        open_admin_window()
        click_count = 0  # Reset counter

admin_button = tk.Button(root, text="        ", command=on_admin_button_click)
admin_button.place(relx=0.15, rely=0.9, anchor="n")





# Treeview for displaying results as a table
columns = ("Key", "Value")
tree = ttk.Treeview(root, columns=columns, show="headings", height=5)
tree.place(relx=0.3, rely=0.05, width=int(screen_width * 0.7), height=int(screen_height * 1))  # Relative position and size

tree.heading("Key", text="")
tree.heading("Value", text="")
tree.column("Key", width=int(screen_width * 0.15))
tree.column("Value", width=int(screen_width * 0.7))

# Function to toggle between fullscreen and smaller window
def toggle_fullscreen():
    current_state = root.attributes('-fullscreen')
    if current_state:
        # If fullscreen, switch to normal size
        root.geometry("1400x1050")  # Set to normal size (adjust as needed)
        root.attributes('-fullscreen', False)  # Disable fullscreen
    else:
        # If not fullscreen, switch to fullscreen
        root.attributes('-fullscreen', True)

# Add a button at the top-left corner
fullscreen_button = tk.Button(root, text="            ", font=("Arial", 12), command=toggle_fullscreen)
fullscreen_button.place(x=0, y=0)  # Place the button at the top-left corner (x=0, y=0)




def get_newline(line):
	result = '' 
	for x in range(line):
		result += '\n'
	return result

def fetch_image(url, size=(100, 100)):  # Resize image to fit cell
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image = image.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print("Error loading image:", e)
        return None

def wrap_text(text, max_width, font_name="Arial", font_size=35):
    """Splits text into multiple lines based on column width"""
    f = font.Font(family=font_name, size=font_size)
    words = text.split()
    lines = []
    line = ""

    for word in words:
        if f.measure(line + " " + word) > max_width:
            lines.append(line)
            line = word  # Start new line
        else:
            line += " " + word if line else word

    lines.append(line)  # Add last line
    return "\n".join(lines)  # Return text with line breaks

# Define a tag with a background color
tree.tag_configure("success", background="lightgreen", font=("Arial", int(screen_width/50),"bold"))  
tree.tag_configure("error", background="red", font=("Arial", int(screen_width/50),"bold"))  
tree.tag_configure("normal", background="white", font=("Arial", int(screen_width/50),"bold"))
tree.tag_configure("name", background="white", font=("Arial", int(screen_width/40),"bold"))


# token verification 

def process_barcode_verification(barcode):
    verification_point_id = get_selected_category_id()
    payload = {'UniqueCode': barcode, 'VerificationPointId': verification_point_id, 'MachineCode': '171'}
    print("point",verification_point_id)
    loader_label.config(text="Loading...") 
    logging.info(f'payload for product_post_url_Token = {payload}') # Show loader
    root.update()
    
    try:
        response = requests.get(product_get_url_Verification, params=payload)
        data = response.json()
        logging.info(data)
       	
        if str(data.get('status')) == "True":
            print("Green On")
            time.sleep(0.2)
            if len(barcode) == 12:
            #   print(barcode_str)
                process_barcode_Token(barcode)
                
            print(barcode)

            a = data.get('data')
            if a != 'NULL':
                # Clear previous data from the table
                for row in tree.get_children():
                    tree.delete(row)

         
                for key, value in a.items():
                    if key == "Filepath":  # If the key is "filepath", load image
                        img = fetch_image(value, size=(int(screen_width//3.7),int(screen_height//1.8) ))
             
                        if img:
                            image_label.config(image=img)# Display image
                            image_label.image = img  # Prevent garbage collection
                        else:
                            tree.insert("", "end", values=(key, "Invalid Image URL"),tags=("error",))
                            logging.info("Invalid Image URL")
                    elif key == "Name":
                        style.configure("Treeview", rowheight=int(screen_height//5.5))
                        logging.info(f"Name : {value}")
                        wrapped_value = wrap_text(value, max_width=850) # Wrap long text
                        tree.insert("", "end", values=(key, wrapped_value),tags=("name",))                        
                    elif key == "Age":
                        logging.info(f"Age : {value}")
                        tree.insert("", "end", values=(key, value),tags=("normal",))
                    elif key == "Gender":
                        logging.info(f"Gender : {value}")
                        tree.insert("", "end", values=(key, value),tags=("normal",))
                    else:
                        continue
                style.configure("Treeview", rowheight=int(screen_height//5.5))
                place = category_options.get(verification_point_id, "Unknown")
                tree.insert("", "end", values=("Place", place), tags=("normal",)) 
                tree.insert("", "end", values=("Status","✅ Verified"),tags=("success",))
                logging.info("Verification successfully")

            else :
                tree.insert("", "end", values=("Status", "❌ Failed"),tags=("error",)) # when data is null
                logging.info("Verification Failed")
                
                print("Red On")
                
                time.sleep(1)
                
                print("Red Off")

        else:
            # Clear previous data and show failed message
            for row in tree.get_children():
                tree.delete(row)
            logging.info("Not Registered")
            tree.insert("", "end", values=("Status", "❌ Not Registered"),tags=("error",))

    except requests.exceptions.RequestException:
        #result_text.set("⚠️ Network Error! Please try again.")
        logging.info("Network Error!!!")
        tree.insert("", "end", values=("Status", "⚠️ Network Error! Please try again."),tags=("error",))
        for x in range (5):
            time.sleep(0.2)
            time.sleep(0.2)
        
    finally:
        loader_label.config(text="")  # Hide loader









#generate token and varification
def process_barcode_Token(bar_code):
    global ready
    gen_point_id = get_selected_category_id()
    payload = {'UniqueCode': bar_code, 'VerificationPointId': gen_point_id, 'MachineCode': '171'}
    logging.info(f'payload for product_post_url_Token = {payload}')

    try:
        t = requests.post(product_post_url_Token, params=payload)
        #print(t.text)
        result = json.loads(t.text)
        logging.info(f'response from product_post_url_Token = {result}')
        data_dict = [t.json()]
        #print(data_dict)
        for item in data_dict:
            responce = str(item.get('status'))
            curDTObj = datetime.now()
            dateStr = curDTObj.strftime("%d %b, %Y")
            p.set(align=u"center",width=1,height=1)
    
            if (str(responce) == str(True)):
                for index, x in enumerate(result['data']['header']): 
                    if index == 0 :
                        p.set(bold=True)
                        p.text("\x1B\x45\x01")  
                        p.text("\x1D\x21\x11") 
                        p.text(x['Label'] + get_newline(x['newlineback']))
                        p.text("\x1B\x45\x00")
                        p.text("\x1D\x21\x00")
                    elif index == 2 :
                        p.set(bold=True)
                        p.set(align= u"" + x['align'],width=x['width'],height=x['height'])
                        p.text( x['Label'] + get_newline(x['newlineback']))
                    else:
                        p.set(align= u"" + x['align'],width=x['width'],height=x['height'])
                        p.text(x['Label'] + get_newline(x['newlineback']))
                    
                    # Reset bold after setting it
                    if index == 0 or index == 2:
                        p.set(bold=False)

                response_barcode=item['data'].get('uniqueCode')


                p.set(align=u"center")
                p.text("------------------------")
                #p.qr(barcode_str,size=8)
                p.text("\x1B\x33" + chr(5))
                p.qr(response_barcode,size=10.5)
                p.text("\x1B\x33" + chr(5))
                p.text("\x1B\x32")
                p.text("\n") 
                p.set(align=u"center",width=1 ,height=1)
                p.text("\x1D\x21\x10")
                p.text(response_barcode +"\n")
                p.text("\x1D\x21\x00")

                p.set(align=u"center",width=2 ,height=2)



                for index, x in enumerate(result['data']['body']):  # Assuming it's a list
                    

                    # Apply bold only for the 1st and 3rd iteration (index 0 and 2)
                    if index == 2 or index == 3:
                        p.set(bold=True)

                    p.set(align= u"" + x['align'],width=x['width'] ,height=x['height'])
                    p.text(get_newline(x['newlinefront']) + x['Label'] + get_newline(x['newlineback']))

                    # Reset bold after setting it
                    if index == 2 or index == 3:
                        p.set(bold=False)

                p.text("------------------------------------------------\n")
                p.set(align=u"center",width=1,height=1)
                            
                for index, x in enumerate(result['data']['footer']):  # Assuming it's a list
                   

                    # Apply bold only for the 1st and 3rd iteration (index 0 and 2)
                    if index == 0 :
                        p.set(bold=True)

                    p.set(align= u"" + x['align'],width=x['width'] ,height=x['height'])
                    p.text(get_newline(x['newlinefront']) + x['Label'] + get_newline(x['newlineback']))

                    # Reset bold after setting it
                    if index == 0:
                        p.set(bold=False)


                p.cut()

            else:
                p.set(align=u"center",width=1,height=1)
                p.text("\x1B\x45\x01")  
                p.text("\x1D\x21\x11") 
                p.textln(center_text("Uttarakhand Tourism "))
                p.text("\x1B\x45\x00")  
                p.text("\x1D\x21\x00") 
                p.text(center_text("------------------------\n\n\n"))
                p.text("\x1D\x21\x10")
                p.text(center_text("No Slots Available Now"))
                p.text("\n\n\n")
                p.text("\x1D\x21\x00")
                p.set(align=u"center",width=1 ,height=1)
                curDTObj = datetime.now()
                dateStr = curDTObj.strftime("%d %b, %Y")
                p.text("\x1D\x21\x11") 
                p.textln(center_text("Date : " + dateStr +" "))
                p.text("\x1B\x45\x00")
                p.text("\x1D\x21\x00")
                p.textln(center_text("------------------------------------------------"))
                p.set(align=u"center",width=1,height=1)
                p.text("\x1B\x45\x01")
                p.text("\x1D\x21\x01")
                p.textln(center_text("Powered by: Ethics Infotech"))
                p.text("\x1D\x21\x00")
                p.text("\x1B\x45\x00")
                p.cut()
    except requests.exceptions.RequestException as e:
        print("Network error occurred")
        logging.info(f'Network error occurred')
        
def center_text(text, width=29):
    pad = (width - len(text) - 5) // 2
    return " " * pad + text



ready = True  # Flag to check if barcode is ready to be processed
barcode = ""  # Store the scanned barcode


scanning = False  
def handle_barcode(barcode):
    try:
        global scanning
        if scanning:
            return
        scanning = True
        image_label.config(image=None)  # Process 1
        image_label.image=None
        process_barcode_verification(barcode)
        barcode_entry.after(0, lambda: barcode_entry.delete(0, tk.END))
        scanning = False
   
    finally:
        global ready
        ready = True

def on_return_key(event):
    global ready
    barcode = barcode_entry.get()
    if ready:  # Check if the barcode is ready to be processed
        ready = False
        threading.Thread(target=handle_barcode, args=(barcode,)).start()

barcode_entry.bind("<Return>", on_return_key)

def barcode_reader_loop():
    global ready
    barcode = ""
    for event in dev.read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            data = evdev.categorize(event)
            if data.keystate == 1:  # Key Down (Barcode key press)
                key_lookup = scan_codes.get(data.scancode)
                if key_lookup == "CRLF":  # End of barcode scan (Enter key or CRLF)
                    if ready:  # Only process if ready is True
                        ready = False  # Set to False while processing
                        barcode_entry.after(0, lambda: barcode_entry.delete(0, tk.END))  # Clear entry
                        print(f"Scanned: {barcode}")
                        threading.Thread(target=handle_barcode, args=(barcode,)).start()
                    barcode = ""  # Reset barcode after processing
                elif key_lookup and len(key_lookup) == 1:  # Valid character
                    barcode += key_lookup  # Add the character to the barcode

# Run scanner in a separate thread
scanner_thread = threading.Thread(target=barcode_reader_loop, daemon=True)
scanner_thread.start()

# Run the GUI
root.mainloop()