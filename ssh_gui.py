import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import platform
import subprocess
import threading

CONFIG_DIR = "configurations"
DEFAULT_CONFIG_FILE = "config.json"

# Ensure the configurations directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config(file_path):
    """
    Load configuration from a JSON file.

    Args:
        file_path (str): Path to the JSON file to load.

    Returns:
        dict or None: The configuration data as a dictionary, or None if the file does not exist.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return None


def save_config(username, ip_address, key_path):
    """
    Save configuration to a JSON file in the configurations directory.

    Args:
        username (str): The username for SSH connection.
        ip_address (str): The IP address of the remote server.
        key_path (str): The file path to the SSH key.
    """
    config_data = {
        "username": username,
        "ip_address": ip_address,
        "key_path": key_path
    }

    # Check if the default configuration file already exists
    default_file_path = os.path.join(CONFIG_DIR, DEFAULT_CONFIG_FILE)
    if os.path.exists(default_file_path):
        existing_config = load_config(default_file_path)
        if existing_config == config_data:
            return  # No changes, do nothing

    # Save to a new file if different
    base_name, ext = os.path.splitext(DEFAULT_CONFIG_FILE)
    counter = 1
    new_file_name = f"{base_name}_{counter}{ext}"
    new_file_path = os.path.join(CONFIG_DIR, new_file_name)
    while os.path.exists(new_file_path):
        counter += 1
        new_file_name = f"{base_name}_{counter}{ext}"
        new_file_path = os.path.join(CONFIG_DIR, new_file_name)

    with open(new_file_path, 'w') as file:
        json.dump(config_data, file)


def connect_to_instance():
    """
    Connect to a remote SSH instance.

    Retrieves user input for SSH connection details, validates them, saves the configuration,
    and initiates a new terminal window for SSH. If any field is missing, an error message is shown.
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
    Open a new terminal and initiate an SSH connection.

    Constructs the SSH command based on the provided key path, username, and IP address,
    and executes it in a new terminal window. Supports macOS and Linux.

    Args:
        key_path (str): The file path to the SSH key.
        username (str): The username for SSH connection.
        ip_address (str): The IP address of the remote server.

    Raises:
        MessageBox: Displays an error message if the operating system is unsupported.
    """
    ssh_command = f"ssh -i {key_path} -o StrictHostKeyChecking=no {username}@{ip_address}"
    current_os = platform.system()

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
    Download a file from the remote instance.

    Retrieves user input for SSH connection details, remote file path, and local destination path.
    Validates the inputs and starts a new thread to execute the SCP command for downloading the file.
    If any field is missing, an error message is shown.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()
    remote_path = remote_file_entry.get()
    local_path = local_path_entry.get()

    if username and ip_address and key_path and remote_path and local_path:
        thread = threading.Thread(target=run_scp_command,
                                  args=(key_path, username, ip_address, remote_path, local_path, "download"))
        thread.start()
    else:
        messagebox.showerror("Error", "Please fill in all fields for downloading")


def upload_file():
    """
    Upload a file to the remote instance.

    Retrieves user input for SSH connection details, local file path, and remote destination path.
    Validates the inputs and starts a new thread to execute the SCP command for uploading the file.
    If any field is missing, an error message is shown.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()
    local_path = local_file_entry.get()
    remote_path = remote_path_upload_entry.get()

    if username and ip_address and key_path and local_path and remote_path:
        thread = threading.Thread(target=run_scp_command,
                                  args=(key_path, username, ip_address, local_path, remote_path, "upload"))
        thread.start()
    else:
        messagebox.showerror("Error", "Please fill in all fields for uploading")


def run_scp_command(key_path, username, ip_address, src_path, dest_path, direction):
    """
    Run an SCP command for file transfer.

    Constructs and executes the SCP command based on the provided parameters for downloading or uploading files.

    Args:
        key_path (str): The file path to the SSH key.
        username (str): The username for SSH connection.
        ip_address (str): The IP address of the remote server.
        src_path (str): The source file path (local or remote).
        dest_path (str): The destination file path (local or remote).
        direction (str): The direction of transfer, either "download" or "upload".
    """
    if direction == "download":
        command = f"scp -i {key_path} -r {username}@{ip_address}:{src_path} {dest_path}"
        subprocess.run(["/bin/bash", "-c", command])
    elif direction == "upload":
        command = f"scp -i {key_path} -r {src_path} {username}@{ip_address}:{dest_path}"
        subprocess.run(["/bin/bash", "-c", command])


def browse_key_file():
    """
    Open a file dialog to select an SSH key file.

    Allows the user to browse and select a file, and then updates the SSH key file entry field
    with the selected file path.
    """
    key_path = filedialog.askopenfilename(
        title="Select SSH Key",
        filetypes=(("PEM files", "*.pem"), ("All files", "*.*")),
    )
    key_file_entry.delete(0, tk.END)
    key_file_entry.insert(0, key_path)


def browse_local_path():
    """
    Open a directory dialog to select a local destination path.

    Allows the user to browse and select a directory, and then updates the local destination
    path entry field with the selected directory path.
    """
    local_path = filedialog.askdirectory(
        title="Select Local Destination"
    )
    local_path_entry.delete(0, tk.END)
    local_path_entry.insert(0, local_path)


def browse_local_file():
    """
    Open a file dialog to select a local file for upload.

    Allows the user to browse and select a file, and then updates the local file path entry
    field with the selected file path.
    """
    local_path = filedialog.askopenfilename(
        title="Select File to Upload"
    )
    local_file_entry.delete(0, tk.END)
    local_file_entry.insert(0, local_path)


def load_config_file():
    """
    Load configuration from a user-selected JSON file.

    Opens a file dialog for the user to select a JSON configuration file, loads its content,
    and updates the GUI fields with the loaded values.
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

upload_button = tk.Button(upload_frame, text="Upload", command=upload_file)
upload_button.grid(row=2, column=0, columnspan=3, pady=10)

# Run the application
root.mainloop()
