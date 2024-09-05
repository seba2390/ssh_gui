import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel
import json
import platform
import threading
import os
import subprocess

from src.remote_file_browser import RemoteFileBrowser

# Constants for configuration directory and default configuration file
CONFIG_DIR = "configurations"
DEFAULT_CONFIG_FILE = "config.json"

# Ensure the configurations directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)


# Utility functions for configuration management
def load_config(file_path):
    """
    Load configuration data from a JSON file.

    Args:
        file_path (str): The path to the configuration file.

    Returns:
        dict or None: The configuration data, or None if the file doesn't exist.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return None


def save_config(username, ip_address, key_path):
    """
    Save configuration details to a JSON file.
    If an identical configuration already exists in any of the existing files, no new file is created.

    Args:
        username (str): The SSH username.
        ip_address (str): The IP address of the remote server.
        key_path (str): The path to the SSH key file.
    """
    config_data = {
        "username": username,
        "ip_address": ip_address,
        "key_path": key_path
    }

    # Check all existing config files in the configurations directory
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(CONFIG_DIR, filename)
            existing_config = load_config(file_path)

            # If a matching configuration is found, do not create a new file
            if existing_config == config_data:
                return

    # No matching config found, so create a new unique configuration file
    base_name, ext = os.path.splitext(DEFAULT_CONFIG_FILE)
    counter = 1
    new_file_name = f"{base_name}_{counter}{ext}"
    new_file_path = os.path.join(CONFIG_DIR, new_file_name)

    # Ensure the new file name is unique
    while os.path.exists(new_file_path):
        counter += 1
        new_file_name = f"{base_name}_{counter}{ext}"
        new_file_path = os.path.join(CONFIG_DIR, new_file_name)

    # Save the new configuration data to the new file
    with open(new_file_path, 'w') as file:
        json.dump(config_data, file)


# SSH connection and file transfer related functions

def connect_to_instance():
    """
    Establish an SSH connection to a remote server.
    Retrieves the necessary fields and starts a new terminal to SSH into the instance.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()

    if username and ip_address and key_path:
        save_config(username, ip_address, key_path)
        thread = threading.Thread(target=open_new_terminal_and_ssh, args=(key_path, username, ip_address))
        thread.start()
    else:
        messagebox.showerror("Error", "Please fill in all fields")


def open_new_terminal_and_ssh(key_path, username, ip_address):
    """
    Open a new terminal window and initiate an SSH session.

    Args:
        key_path (str): The path to the SSH key file.
        username (str): The SSH username.
        ip_address (str): The IP address of the remote server.
    """
    ssh_command = f"ssh -i {key_path} -o StrictHostKeyChecking=no {username}@{ip_address}"
    current_os = platform.system()

    # Open a terminal depending on the OS
    if current_os == "Darwin":  # macOS
        terminal_command = f'''
        tell application "Terminal"
            do script "{ssh_command}"
            activate
        end tell
        '''
        subprocess.Popen(["osascript", "-e", terminal_command])

    elif current_os == "Linux":
        terminal_command = f"gnome-terminal -- bash -c '{ssh_command}; exec bash'"
        subprocess.Popen(terminal_command, shell=True)

    else:
        messagebox.showerror("Error", f"Unsupported operating system: {current_os}")


def download_file():
    """
    Download files from a remote server using Rsync.
    Starts a new thread to run rsync commands for downloading.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()
    remote_path = remote_file_entry.get()
    local_path = local_path_entry.get()

    if username and ip_address and key_path and remote_path and local_path:
        # Start the rsync process in a separate thread
        thread = threading.Thread(target=run_rsync_command,
                                  args=(key_path, username, ip_address, remote_path, local_path, "download"))
        thread.start()
    else:
        messagebox.showerror("Error", "Please fill in all fields for downloading")


def upload_file():
    """
    Upload files to a remote server using Rsync.
    Starts a new thread to run rsync commands for uploading.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()
    local_path = local_file_entry.get()
    remote_path = remote_path_upload_entry.get()

    if username and ip_address and key_path and local_path and remote_path:
        # Start the rsync process in a separate thread
        thread = threading.Thread(target=run_rsync_command,
                                  args=(key_path, username, ip_address, local_path, remote_path, "upload"))
        thread.start()
    else:
        messagebox.showerror("Error", "Please fill in all fields for uploading")


def run_rsync_command(key_path, username, ip_address, src_path, dest_path, direction):
    """
    Run an rsync command to transfer files between local and remote servers efficiently.

    Args:
        key_path (str): The path to the SSH key file.
        username (str): The SSH username.
        ip_address (str): The IP address of the remote server.
        src_path (str): The source path of the file or folder.
        dest_path (str): The destination path for the file or folder.
        direction (str): "download" or "upload" to indicate the transfer direction.
    """
    # Base rsync command with options:
    # -a preserves symbolic links, permissions, timestamps, etc.
    # -P shows progress and handles partial transfers
    # -e 'ssh -i {key_path}' uses the provided SSH key for the connection

    if direction == "download":
        command = f"rsync -azP -e 'ssh -i {key_path}' {username}@{ip_address}:{src_path} {dest_path}"
        subprocess.run(["/bin/bash", "-c", command])
    elif direction == "upload":
        command = f"rsync -azP -e 'ssh -i {key_path}' {src_path} {username}@{ip_address}:{dest_path}"
        subprocess.run(["/bin/bash", "-c", command])


# File dialog utility functions

def browse_key_file():
    """
    Open a file dialog to select the SSH key file.
    """
    key_path = filedialog.askopenfilename(
        title="Select SSH Key",
        filetypes=(("PEM files", "*.pem"), ("All files", "*.*")),
    )
    key_file_entry.delete(0, tk.END)
    key_file_entry.insert(0, key_path)


def browse_local_path():
    """
    Open a directory dialog to select the local destination directory for downloading files.
    """
    local_path = filedialog.askdirectory(
        title="Select Local Destination"
    )
    local_path_entry.delete(0, tk.END)
    local_path_entry.insert(0, local_path)


def browse_local_file():
    """
    Replaces the 'Browse' button with a dropdown menu to choose between selecting a file or directory.
    """
    # Remove the current Browse button and replace it with an OptionMenu
    browse_local_file_button.grid_remove()

    # Options for the dropdown menu
    options = ["Select File", "Select Directory"]

    # Variable to store the selected option
    selected_option = tk.StringVar(root)
    selected_option.set("Select")  # Placeholder text

    # Create the OptionMenu dropdown
    dropdown = tk.OptionMenu(upload_frame, selected_option, *options, command=handle_local_selection)
    dropdown.grid(row=0, column=2, padx=5)

    # Once the user makes a choice, the `handle_local_selection` will take care of it


def handle_local_selection(selection):
    """
    Handle the user's selection from the dropdown.
    """
    if selection == "Select File":
        select_file()
    elif selection == "Select Directory":
        select_directory()

    # After the selection is made and the dialog is opened, restore the original Browse button
    restore_browse_button()


def restore_browse_button():
    """
    Restore the original 'Browse' button after a file/directory has been selected.
    """
    # Remove the dropdown and bring back the Browse button
    browse_local_file_button.grid()


def select_file():
    """
    Open a file dialog to select a single file and display the path in the entry.
    """
    local_path = filedialog.askopenfilename(title="Select File to Upload")
    if local_path:  # If a file is selected, insert it into the entry
        local_file_entry.delete(0, tk.END)
        local_file_entry.insert(0, local_path)


def select_directory():
    """
    Open a directory dialog to select a directory and display the path in the entry.
    """
    local_directory = filedialog.askdirectory(title="Select Directory to Upload")
    if local_directory:  # If a directory is selected, insert it into the entry
        local_file_entry.delete(0, tk.END)
        local_file_entry.insert(0, local_directory)


def browse_remote_file():
    """
    Open a remote file browser dialog to select a file from the remote server.
    Requires connection details such as username, IP address, and SSH key.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()

    if username and ip_address and key_path:
        ssh_command = f"ssh -i {key_path} {username}@{ip_address}"
        remote_browser_window = tk.Toplevel(root)
        remote_browser_window.title("Select Remote File")

        def on_select(path):
            remote_file_entry.delete(0, tk.END)
            remote_file_entry.insert(0, path)

        remote_browser = RemoteFileBrowser(remote_browser_window, ssh_command, on_select)
    else:
        messagebox.showerror("Error", "Please fill in all connection fields")


def browse_remote_path():
    """
    Open a remote file browser dialog to select a path from the remote server.
    Requires connection details such as username, IP address, and SSH key.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()

    if username and ip_address and key_path:
        ssh_command = f"ssh -i {key_path} {username}@{ip_address}"
        remote_browser_window = tk.Toplevel(root)
        remote_browser_window.title("Select Remote Path")

        def on_select(path):
            remote_path_upload_entry.delete(0, tk.END)
            remote_path_upload_entry.insert(0, path)

        remote_browser = RemoteFileBrowser(remote_browser_window, ssh_command, on_select)
    else:
        messagebox.showerror("Error", "Please fill in all connection fields")


def load_config_file():
    """
    Open a file dialog to load a previously saved configuration from a JSON file.
    Populates the fields (username, IP address, key path) with the loaded data.
    """
    file_path = filedialog.askopenfilename(
        title="Select Configuration File",
        initialdir=CONFIG_DIR,
        filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
    )
    if file_path:
        config = load_config(file_path)
        if config:
            username_entry.delete(0, tk.END)
            username_entry.insert(0, config.get("username", ""))
            ip_entry.delete(0, tk.END)
            ip_entry.insert(0, config.get("ip_address", ""))
            key_file_entry.delete(0, tk.END)
            key_file_entry.insert(0, config.get("key_path", ""))


# GUI setup

# Create the main window
root = tk.Tk()
root.title("SSH Connect")

# Configure grid layout for three columns
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)

# ---- Column 1: Connection ----
connect_frame = tk.LabelFrame(root, text="Connecting to instance", padx=10, pady=10)
connect_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

tk.Label(connect_frame, text="Username:").grid(row=0, column=0, sticky="w")
username_entry = tk.Entry(connect_frame)
username_entry.grid(row=0, column=1)

tk.Label(connect_frame, text="IP Address:").grid(row=1, column=0, sticky="w")
ip_entry = tk.Entry(connect_frame)
ip_entry.grid(row=1, column=1)

tk.Label(connect_frame, text="SSH Key File:").grid(row=2, column=0, sticky="w")
key_file_entry = tk.Entry(connect_frame)
key_file_entry.grid(row=2, column=1)

browse_button = tk.Button(connect_frame, text="Browse", command=browse_key_file)
browse_button.grid(row=2, column=2, padx=5)

connect_button = tk.Button(connect_frame, text="Connect", command=connect_to_instance)
connect_button.grid(row=3, column=0, columnspan=3, pady=10)

load_config_button = tk.Button(connect_frame, text="Load Config", command=load_config_file)
load_config_button.grid(row=4, column=0, columnspan=3, pady=10)

# ---- Column 2: Download ----
download_frame = tk.LabelFrame(root, text="Download from instance", padx=10, pady=10)
download_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

tk.Label(download_frame, text="Remote File Path:").grid(row=0, column=0, sticky="w")
remote_file_entry = tk.Entry(download_frame)
remote_file_entry.grid(row=0, column=1)

browse_remote_file_button = tk.Button(download_frame, text="Browse", command=browse_remote_file)
browse_remote_file_button.grid(row=0, column=2, padx=5)

tk.Label(download_frame, text="Local Destination Path:").grid(row=1, column=0, sticky="w")
local_path_entry = tk.Entry(download_frame)
local_path_entry.grid(row=1, column=1)

browse_local_button = tk.Button(download_frame, text="Browse", command=browse_local_path)
browse_local_button.grid(row=1, column=2, padx=5)

download_button = tk.Button(download_frame, text="Download", command=download_file)
download_button.grid(row=2, column=0, columnspan=3, pady=10)

# ---- Column 3: Upload ----
upload_frame = tk.LabelFrame(root, text="Upload to instance", padx=10, pady=10)
upload_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

tk.Label(upload_frame, text="Local File Path:").grid(row=0, column=0, sticky="w")
local_file_entry = tk.Entry(upload_frame)
local_file_entry.grid(row=0, column=1)

browse_local_file_button = tk.Button(upload_frame, text="Browse", command=browse_local_file)
browse_local_file_button.grid(row=0, column=2, padx=5)

tk.Label(upload_frame, text="Remote Destination Path:").grid(row=1, column=0, sticky="w")
remote_path_upload_entry = tk.Entry(upload_frame)
remote_path_upload_entry.grid(row=1, column=1)

browse_remote_path_button = tk.Button(upload_frame, text="Browse", command=browse_remote_path)
browse_remote_path_button.grid(row=1, column=2, padx=5)

upload_button = tk.Button(upload_frame, text="Upload", command=upload_file)
upload_button.grid(row=2, column=0, columnspan=3, pady=10)

# Run the application
root.mainloop()
