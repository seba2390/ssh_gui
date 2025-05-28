import glob
import json
import os
import platform
import re
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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
        with open(file_path, "r") as file:
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
    config_data = {"username": username, "ip_address": ip_address, "key_path": key_path}

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
    with open(new_file_path, "w") as file:
        json.dump(config_data, file)


def test_connection():
    """
    Test the SSH connection by running a simple SSH command to check if the connection can be established.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()

    if username and ip_address and key_path:
        # SSH command to test connection (we use 'exit' to immediately close the connection after success)
        ssh_command = f"ssh -i {key_path} -o StrictHostKeyChecking=no {username}@{ip_address} exit"
        result = subprocess.run(ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            messagebox.showinfo("Connection Test", "Connection successful!")
        else:
            messagebox.showerror("Connection Test", f"Connection failed: {result.stderr}")
    else:
        messagebox.showerror("Error", "Please fill in all fields")


def is_remote_directory(key_path, username, ip_address, remote_path):
    """
    Check if the remote path is a directory using SSH.

    Args:
        key_path (str): Path to the SSH key.
        username (str): SSH username.
        ip_address (str): IP address of the remote server.
        remote_path (str): Path on the remote server.

    Returns:
        bool: True if the remote path is a directory, False if it's a file.
    """
    # Prepare the SSH command to check if the path is a directory
    ssh_command = f"ssh -i {key_path} {username}@{ip_address} 'test -d {remote_path} && echo directory || echo file'"

    # Run the command and capture output
    result = subprocess.run(ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if "directory" in result.stdout:
        return True
    elif "file" in result.stdout:
        return False
    else:
        raise Exception(f"Unable to determine if {remote_path} is a directory or file. SSH Error: {result.stderr}")


# SSH connection and file transfer related functions
def connect_to_instance():
    """
    Establish an SSH connection to a remote server using the selected terminal emulator.

    This function retrieves the username, IP address, SSH key path, and the selected terminal
    emulator from the GUI inputs. It validates that all fields are filled, including the terminal
    selection, and then starts a new thread to open the selected terminal and initiate the SSH
    connection. If any field is missing, an error message is displayed.

    The terminal emulator is selected from a dropdown menu, with options depending on the
    operating system:
    - On macOS: "Standard" (default Terminal) and "Warp" (if installed).
    - On Linux: Only "Standard" (e.g., gnome-terminal).

    The function saves the configuration details (username, IP address, key path) to a JSON file
    before initiating the connection.

    Threading is used to prevent the GUI from freezing while the SSH connection is being established.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()
    terminal = terminal_var.get()  # Get the selected terminal from the dropdown

    if username and ip_address and key_path and terminal:
        # Save the configuration details to a JSON file
        save_config(username, ip_address, key_path)

        # Start a new thread to open the selected terminal and SSH into the instance
        thread = threading.Thread(target=open_new_terminal_and_ssh, args=(key_path, username, ip_address, terminal))
        thread.start()
    else:
        # Show an error if any field is missing or no terminal is selected
        messagebox.showerror("Error", "Please fill in all fields and select a terminal")


def open_new_terminal_and_ssh(key_path, username, ip_address, terminal_type):
    """
    Open a new terminal window and initiate an SSH session using the specified terminal emulator.

    This function constructs an SSH command with the provided key, username, and IP address,
    and opens a new terminal window using the selected terminal emulator to run the SSH command.

    The terminal emulator is specified by the `terminal_type` parameter:
    - On macOS:
      - "Standard": Uses the default Terminal application via AppleScript to execute the SSH command directly.
      - "Warp": Uses a custom shell script (`src/run_in_warp.sh`) to open Warp and simulate typing the SSH command.
    - On Linux:
      - "Standard": Uses `gnome-terminal` to run the SSH command in a new window.

    If the operating system or terminal type is unsupported, an error message is displayed.

    Args:
        key_path (str): The path to the SSH private key file used for authentication.
        username (str): The SSH username to connect as on the remote server.
        ip_address (str): The IP address of the remote server to connect to.
        terminal_type (str): The type of terminal emulator to use ("Standard" or "Warp" on macOS).

    SSH Command Options:
        -i {key_path}: Specifies the private SSH key file for authentication.
        -o StrictHostKeyChecking=no: Disables host key checking to avoid prompts.
        -o ServerAliveInterval=60: Sends keep-alive messages every 60 seconds to prevent timeouts.
        -o ServerAliveCountMax=2: Disconnects if no response after two keep-alive messages.

    Note:
        For "Warp" on macOS, this function relies on the `src/run_in_warp.sh` script, which must be
        executable and located in the `src/` directory relative to the Python script's working directory.
        Ensure Warp is installed at `/Applications/Warp.app` and the script has execute permissions (`chmod +x src/run_in_warp.sh`).
    """
    # Construct the SSH command with keep-alive options to prevent idle timeout
    ssh_command = f"ssh -i {key_path} -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=2 {username}@{ip_address}"

    # Determine the current operating system
    current_os = platform.system()

    if current_os == "Darwin":  # macOS
        if terminal_type == "Standard":
            # Use AppleScript to open the default Terminal and run the SSH command
            terminal_command = f'''
            tell application "Terminal"
                do script "{ssh_command}"
                activate
            end tell
            '''
            subprocess.Popen(["osascript", "-e", terminal_command])
        elif terminal_type == "Warp":
            # Use the custom shell script to open Warp and run the SSH command
            script_path = os.path.join(os.path.dirname(__file__), "src", "run_in_warp.sh")
            if os.path.exists(script_path):
                subprocess.Popen([script_path, ssh_command])
            else:
                messagebox.showerror(
                    "Error",
                    f"Warp script not found at {script_path}. Ensure src/run_in_warp.sh exists and is executable.",
                )
        else:
            messagebox.showerror("Error", f"Unsupported terminal type: {terminal_type}")
    elif current_os == "Linux":
        if terminal_type == "Standard":
            # Use gnome-terminal to open a new terminal window and run the SSH command
            terminal_command = f"gnome-terminal -- bash -c '{ssh_command}; exec bash'"
            subprocess.Popen(terminal_command, shell=True)
        else:
            messagebox.showerror("Error", f"Unsupported terminal type: {terminal_type}")
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
        # Show the progress bar and reset its value
        download_progress.grid()  # Make the progress bar visible
        download_progress["value"] = 0
        # Update status label to show the download has started
        download_status_label.config(text="Downloading...")
        # Start the rsync process in a separate thread
        thread = threading.Thread(
            target=run_rsync_command,
            args=(
                key_path,
                username,
                ip_address,
                remote_path,
                local_path,
                "download",
                download_status_label,
                download_progress,
            ),
        )
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
        # Show the progress bar and reset its value
        upload_progress.grid()  # Make the progress bar visible
        upload_progress["value"] = 0
        # Update status label to show the upload has started
        upload_status_label.config(text="Uploading...")
        # Start the rsync process in a separate thread
        thread = threading.Thread(
            target=run_rsync_command,
            args=(
                key_path,
                username,
                ip_address,
                local_path,
                remote_path,
                "upload",
                upload_status_label,
                upload_progress,
            ),
        )
        thread.start()
    else:
        messagebox.showerror("Error", "Please fill in all fields for uploading")


def run_rsync_command(key_path, username, ip_address, src_path, dest_path, direction, status_label, progress_bar):
    """
    Run an rsync command to transfer files between local and remote servers efficiently,
    update the status label, and reflect the progress in a progress bar.

    Args:
        key_path (str): The path to the SSH key file.
        username (str): The SSH username.
        ip_address (str): The IP address of the remote server.
        src_path (str): The source path of the file or folder.
        dest_path (str): The destination path for the file or folder.
        direction (str): "download" or "upload" to indicate the transfer direction.
        status_label (Label): The label to update with progress messages.
        progress_bar (ttk.Progressbar): The progress bar to update during the transfer.

    The function builds the rsync command with options:
        -a: Preserves symbolic links, permissions, timestamps, etc.
        -z: Enables compression during the transfer.
        -P: Shows progress and allows partial transfers.
        -e: Specifies the SSH command with the provided SSH key for authentication.

    The status_label is updated to reflect the completion of the operation.
    """
    progress_bar["value"] = 0  # Reset progress bar
    is_directory = False

    # Determine if the source is a directory by checking with SSH for downloads or local check for uploads
    if direction == "download":
        is_directory = is_remote_directory(key_path, username, ip_address, src_path)
    elif direction == "upload":
        is_directory = os.path.isdir(src_path)

    # Update the status label based on whether it's a directory or file
    if is_directory:
        status_label.config(text=f"{direction.capitalize()} in progress... (Folder)")
    else:
        status_label.config(text=f"{direction.capitalize()} in progress...")

    # Construct the rsync command based on the direction
    if direction == "download":
        command = f"rsync -azP -e 'ssh -i {key_path}' {username}@{ip_address}:{src_path} {dest_path}"
    elif direction == "upload":
        command = f"rsync -azP -e 'ssh -i {key_path}' {src_path} {username}@{ip_address}:{dest_path}"
    else:
        raise Exception("Unsupported direction")

    # Open the subprocess and capture real-time output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

    # Regex to capture progress percentage from rsync output (e.g., "50.2%")
    progress_regex = re.compile(r"(\d+)\%")

    # Loop through the output of rsync
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break

        # Update progress for files (based on percentage output)
        if not is_directory:
            match = progress_regex.search(output)
            if match:
                progress_percent = int(match.group(1))
                progress_bar["value"] = progress_percent  # Update the progress bar
                status_label.config(text=f"{direction.capitalize()} in progress... {progress_percent}%")

        # For directories: Just update the progress bar without showing percentages
        else:
            if "to-check" in output:
                # Parse "to-check" line to update progress for folder downloads
                # e.g., rsync output line: "12345 files to-check=100/200"
                match = re.search(r"to-check=(\d+)/(\d+)", output)
                if match:
                    checked = int(match.group(2)) - int(match.group(1))
                    total = int(match.group(2))
                    progress_percent = int((checked / total) * 100)
                    progress_bar["value"] = progress_percent  # Update the progress bar for directories
            progress_bar.update()  # Ensure progress bar is always updated

    # Ensure the process has completed
    process.wait()

    # Final update after the process finishes
    progress_bar["value"] = 100  # Ensure the bar reaches 100%
    status_label.config(text=f"{direction.capitalize()} Complete!")


# File dialog utility functions


def browse_key_file():
    """
    Open a file dialog to select the SSH key file, starting in ~/.ssh/ if it exists,
    otherwise starting in the home directory.
    """
    # Get the user's home directory
    home_dir = os.path.expanduser("~")

    # Check if ~/.ssh/ exists, otherwise default to the home directory
    ssh_dir = os.path.join(home_dir, ".ssh")
    initial_dir = ssh_dir if os.path.exists(ssh_dir) else home_dir

    # Open the file dialog starting from the determined initial directory
    key_path = filedialog.askopenfilename(
        initialdir=initial_dir,  # Start in ~/.ssh/ or ~
        title="Select SSH Key",
        filetypes=(("PEM files", "*.pem"), ("All files", "*.*")),
    )

    # If a file was selected, update the entry widget
    if key_path:
        key_file_entry.delete(0, tk.END)
        key_file_entry.insert(0, key_path)


def browse_local_path():
    """
    Open a directory dialog to select the local destination directory for downloading files.
    """
    local_path = filedialog.askdirectory(title="Select Local Destination")
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

test_connection_button = tk.Button(connect_frame, text="Test Connection", command=test_connection)
test_connection_button.grid(row=5, column=0, columnspan=3, pady=10)

# Determine terminal options based on the operating system
current_os = platform.system()
if current_os == "Darwin":  # macOS
    terminal_options = ["Standard", "Warp"]
elif current_os == "Linux":
    terminal_options = ["Standard"]
else:
    terminal_options = []

# Add terminal selection dropdown
tk.Label(connect_frame, text="Terminal:").grid(row=6, column=0, sticky="w")
terminal_var = tk.StringVar()
terminal_combobox = ttk.Combobox(connect_frame, textvariable=terminal_var, state="readonly")
terminal_combobox["values"] = terminal_options
if terminal_options:
    terminal_var.set(terminal_options[0])  # Set default to the first option
terminal_combobox.grid(row=6, column=1, columnspan=2, sticky="ew")

# ---- Column 2: Download ----
download_frame = tk.LabelFrame(root, text="Download from instance", padx=10, pady=10)
download_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

download_progress = ttk.Progressbar(download_frame, orient="horizontal", mode="determinate", length=300)
download_progress.grid(row=4, column=0, columnspan=3, pady=5)

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

download_status_label = tk.Label(download_frame, text="")  # Initialize with an empty string
download_status_label.grid(row=3, column=0, columnspan=3, pady=5)  # Place it under the download button

# ---- Column 3: Upload ----
upload_frame = tk.LabelFrame(root, text="Upload to instance", padx=10, pady=10)
upload_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

upload_progress = ttk.Progressbar(upload_frame, orient="horizontal", mode="determinate", length=300)
upload_progress.grid(row=4, column=0, columnspan=3, pady=5)

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

upload_status_label = tk.Label(upload_frame, text="")  # Upload status label
upload_status_label.grid(row=3, column=0, columnspan=3, pady=5)  # Place it under the upload button

# After creating the progress bars, hide them initially
download_progress.grid_remove()  # Hide the download progress bar
upload_progress.grid_remove()  # Hide the upload progress bar


# --- Load last used configuration and pre-fill fields ---
def load_last_used_config():
    config_files = glob.glob(os.path.join(CONFIG_DIR, "config_*.json"))
    if not config_files:
        return

    # Sort files by the number in their name
    def extract_number(f):
        m = re.search(r"config_(\d+)\.json$", f)
        return int(m.group(1)) if m else 0

    config_files.sort(key=extract_number)
    last_config = config_files[-1]
    config = load_config(last_config)
    if config:
        username_entry.delete(0, tk.END)
        username_entry.insert(0, config.get("username", ""))
        ip_entry.delete(0, tk.END)
        ip_entry.insert(0, config.get("ip_address", ""))
        key_file_entry.delete(0, tk.END)
        key_file_entry.insert(0, config.get("key_path", ""))


load_last_used_config()

# Run the application
root.mainloop()
