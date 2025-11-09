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


def truncate_filename(filename: str, max_length: int) -> str:
    """
    Truncate a filename to fit within max_length characters, inserting '...' in the middle if needed.
    """
    if len(filename) <= max_length:
        return filename
    part = (max_length - 3) // 2
    return f"{filename[:part]}…{filename[-part:]}"


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


def save_config(username, ip_address, key_path, port):
    """
    Save configuration details to a JSON file.
    If an identical configuration already exists in any of the existing files, no new file is created.

    Args:
        username (str): The SSH username.
        ip_address (str): The IP address of the remote server.
        key_path (str): The path to the SSH key file.
        port (str): The SSH port number.
    """
    config_data = {"username": username, "ip_address": ip_address, "key_path": key_path, "port": port}

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
    port = port_entry.get()

    if username and ip_address and key_path and port:
        # SSH command to test connection (we use 'exit' to immediately close the connection after success)
        ssh_command = f"ssh -i {key_path} -p {port} -o StrictHostKeyChecking=no {username}@{ip_address} exit"
        result = subprocess.run(ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            messagebox.showinfo("Connection Test", "Connection successful!")
        else:
            messagebox.showerror("Connection Test", f"Connection failed: {result.stderr}")
    else:
        messagebox.showerror("Error", "Please fill in all fields")


def check_disk_space():
    """
    Check the available disk space on the remote server and display it in the GUI.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()
    port = port_entry.get()

    if username and ip_address and key_path and port:
        # SSH command to get disk space information (using df -h for human-readable format)
        ssh_command = f"ssh -i {key_path} -p {port} -o StrictHostKeyChecking=no {username}@{ip_address} 'df -h /'"
        result = subprocess.run(ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            # Parse the output to extract disk space information
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                # The second line contains the disk space info
                parts = lines[1].split()
                if len(parts) >= 5:
                    size = parts[1]
                    used = parts[2]
                    available = parts[3]
                    use_percent = parts[4]

                    disk_info = f"Total: {size} | Used: {used} ({use_percent}) | Available: {available}"
                    disk_space_label.config(text=disk_info, fg="green")
                else:
                    disk_space_label.config(text="Could not parse disk space info", fg="red")
            else:
                disk_space_label.config(text="Could not retrieve disk space info", fg="red")
        else:
            disk_space_label.config(text=f"Error: {result.stderr}", fg="red")
    else:
        messagebox.showerror("Error", "Please fill in all connection fields")


def is_remote_directory(key_path, username, ip_address, remote_path, port):
    """
    Check if the remote path is a directory using SSH.

    Args:
        key_path (str): Path to the SSH key.
        username (str): SSH username.
        ip_address (str): IP address of the remote server.
        remote_path (str): Path on the remote server.
        port (str): SSH port number.

    Returns:
        bool: True if the remote path is a directory, False if it's a file.
    """
    # Prepare the SSH command to check if the path is a directory
    ssh_command = f"ssh -i {key_path} -p {port} {username}@{ip_address} 'test -d {remote_path} && echo directory || echo file'"

    # Run the command and capture output
    result = subprocess.run(ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if "directory" in result.stdout:
        return True
    elif "file" in result.stdout:
        return False
    else:
        raise Exception(f"Unable to determine if {remote_path} is a directory or file. SSH Error: {result.stderr}")


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
    port = port_entry.get()
    terminal = terminal_var.get()  # Get the selected terminal from the dropdown

    if username and ip_address and key_path and port and terminal:
        # Save the configuration details to a JSON file
        save_config(username, ip_address, key_path, port)

        # Start a new thread to open the selected terminal and SSH into the instance
        thread = threading.Thread(target=open_new_terminal_and_ssh, args=(key_path, username, ip_address, port, terminal))
        thread.start()
    else:
        # Show an error if any field is missing or no terminal is selected
        messagebox.showerror("Error", "Please fill in all fields and select a terminal")


def open_new_terminal_and_ssh(key_path, username, ip_address, port, terminal_type):
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
        port (str): The SSH port number.
        terminal_type (str): The type of terminal emulator to use ("Standard" or "Warp" on macOS).

    SSH Command Options:
        -i {key_path}: Specifies the private SSH key file for authentication.
        -p {port}: Specifies the SSH port number.
        -o StrictHostKeyChecking=no: Disables host key checking to avoid prompts.
        -o ServerAliveInterval=60: Sends keep-alive messages every 60 seconds to prevent timeouts.
        -o ServerAliveCountMax=2: Disconnects if no response after two keep-alive messages.

    Note:
        For "Warp" on macOS, this function relies on the `src/run_in_warp.sh` script, which must be
        executable and located in the `src/` directory relative to the Python script's working directory.
        Ensure Warp is installed at `/Applications/Warp.app` and the script has execute permissions (`chmod +x src/run_in_warp.sh`).
    """
    # Construct the SSH command with keep-alive options to prevent idle timeout
    ssh_command = f"ssh -i {key_path} -p {port} -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=2 {username}@{ip_address}"

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
    port = port_entry.get()
    remote_path = remote_file_entry.get()
    local_path = local_path_entry.get()

    if username and ip_address and key_path and port and remote_path and local_path:
        # Show the progress bar and reset its value
        download_progress.grid()
        download_progress["value"] = 0
        # Show live labels
        download_live_file_label.grid()
        download_speed_label.grid()
        download_eta_label.grid()
        # Update status label to show the download has started
        download_status_label.config(text="Downloading...")
        # Start the rsync process in a separate thread
        thread = threading.Thread(
            target=run_rsync_command,
            args=(
                key_path,
                username,
                ip_address,
                port,
                remote_path,
                local_path,
                "download",
                download_status_label,
                download_progress,
                download_live_file_label,
                download_speed_label,
                download_eta_label,
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
    port = port_entry.get()
    local_path = local_file_entry.get()
    remote_path = remote_path_upload_entry.get()

    if username and ip_address and key_path and port and local_path and remote_path:
        # Show the progress bar and reset its value
        upload_progress.grid()
        upload_progress["value"] = 0
        # Show live labels
        upload_live_file_label.grid()
        upload_speed_label.grid()
        upload_eta_label.grid()
        # Update status label to show the upload has started
        upload_status_label.config(text="Uploading...")
        # Start the rsync process in a separate thread
        thread = threading.Thread(
            target=run_rsync_command,
            args=(
                key_path,
                username,
                ip_address,
                port,
                local_path,
                remote_path,
                "upload",
                upload_status_label,
                upload_progress,
                upload_live_file_label,
                upload_speed_label,
                upload_eta_label,
            ),
        )
        thread.start()
    else:
        messagebox.showerror("Error", "Please fill in all fields for uploading")


import time


def run_rsync_command(
    key_path,
    username,
    ip_address,
    port,
    src_path,
    dest_path,
    direction,
    status_label,
    progress_bar,
    filename_label=None,
    speed_label=None,
    eta_label=None,
):
    """
    Run an rsync command to transfer files between local and remote servers efficiently,
    update the status label, reflect the progress in a progress bar, and show live filename,
    speed, and ETA.
    """
    progress_bar["value"] = 0  # Reset progress bar
    is_directory = False

    # Variables for ETA calculation
    start_time = time.time()
    last_progress = 0
    last_time = start_time

    # Determine if the source is a directory by checking with SSH for downloads or local check for uploads
    if direction == "download":
        is_directory = is_remote_directory(key_path, username, ip_address, src_path, port)
    elif direction == "upload":
        is_directory = os.path.isdir(src_path)

    # Update the status label based on whether it's a directory or file
    if is_directory:
        status_label.config(text=f"{direction.capitalize()} in progress... (Folder)")
    else:
        status_label.config(text=f"{direction.capitalize()} in progress...")

    # Construct the rsync command based on the direction
    if direction == "download":
        command = f"rsync -azP -e 'ssh -i {key_path} -p {port}' {username}@{ip_address}:{src_path} {dest_path}"
    else:  # upload
        command = f"rsync -azP -e 'ssh -i {key_path} -p {port}' {src_path} {username}@{ip_address}:{dest_path}"

    # Open the subprocess and capture real-time output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

    # Regex to capture progress percentage from rsync output (e.g., "50%")
    progress_regex = re.compile(r"(\d+)\%")

    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break

        # Detect file name lines (they appear before progress stats)
        if (
            filename_label
            and output.strip()
            and not progress_regex.search(output)
            and "to-check" not in output
            and "%" not in output
        ):
            current_file = output.strip()
            truncated = truncate_filename(current_file, filename_label.cget("width"))
            filename_label.config(text=truncated)
            filename_label.update()

        current_progress = 0

        # Update progress for single files based on percentage output
        if not is_directory:
            match = progress_regex.search(output)
            if match:
                percent = int(match.group(1))
                current_progress = percent
                progress_bar["value"] = percent
                status_label.config(text=f"{direction.capitalize()} in progress... {percent}%")
        else:
            # For directories
            if "to-check" in output:
                m = re.search(r"to-check=(\d+)/(\d+)", output)
                if m:
                    checked = int(m.group(2)) - int(m.group(1))
                    total = int(m.group(2))
                    percent = int((checked / total) * 100)
                    current_progress = percent
                    progress_bar["value"] = percent
            progress_bar.update()

        # Parse speed from rsync stats lines
        speed_match = re.search(r"([0-9.]+[KMG]?B/s)", output)
        if speed_match and speed_label:
            speed = speed_match.group(1)
            speed_label.config(text=f"{speed}")
            speed_label.update()

        # Calculate overall ETA based on progress
        if current_progress > last_progress and current_progress > 0:
            current_time = time.time()
            elapsed_time = current_time - start_time

            # Calculate ETA based on overall progress
            if current_progress > 0:
                estimated_total_time = (elapsed_time / current_progress) * 100
                remaining_time = estimated_total_time - elapsed_time

                if remaining_time > 0:
                    hours = int(remaining_time // 3600)
                    minutes = int((remaining_time % 3600) // 60)
                    seconds = int(remaining_time % 60)

                    eta_str = f"{hours:01d}:{minutes:02d}:{seconds:02d}"

                    if eta_label:
                        eta_label.config(text=f"ETA: {eta_str}")
                        eta_label.update()

            last_progress = current_progress
            last_time = current_time

    process.wait()
    progress_bar["value"] = 100
    status_label.config(text=f"{direction.capitalize()} Complete!")


# File dialog utility functions
def browse_key_file():
    """
    Open a file dialog to select the SSH key file, starting in ~/.ssh/ if it exists,
    otherwise starting in the home directory.
    """
    home_dir = os.path.expanduser("~")
    ssh_dir = os.path.join(home_dir, ".ssh")
    initial_dir = ssh_dir if os.path.exists(ssh_dir) else home_dir

    key_path = filedialog.askopenfilename(
        initialdir=initial_dir,
        title="Select SSH Key",
        filetypes=(("PEM files", "*.pem"), ("All files", "*.*")),
    )
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
    browse_local_file_button.grid_remove()
    options = ["Select File", "Select Directory"]
    selected_option = tk.StringVar(root)
    selected_option.set("Select")
    dropdown = tk.OptionMenu(upload_frame, selected_option, *options, command=handle_local_selection)
    dropdown.grid(row=0, column=2, padx=5)


def handle_local_selection(selection):
    """
    Handle the user's selection from the dropdown.
    """
    if selection == "Select File":
        select_file()
    elif selection == "Select Directory":
        select_directory()
    restore_browse_button()


def restore_browse_button():
    """
    Restore the original 'Browse' button after a file/directory has been selected.
    """
    browse_local_file_button.grid()


def select_file():
    """
    Open a file dialog to select a single file and display the path in the entry.
    """
    local_path = filedialog.askopenfilename(title="Select File to Upload")
    if local_path:
        local_file_entry.delete(0, tk.END)
        local_file_entry.insert(0, local_path)


def select_directory():
    """
    Open a directory dialog to select a directory and display the path in the entry.
    """
    local_directory = filedialog.askdirectory(title="Select Directory to Upload")
    if local_directory:
        local_file_entry.delete(0, tk.END)
        local_file_entry.insert(0, local_directory)


def browse_remote_file():
    """
    Open a remote file browser dialog to select a file from the remote server.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()
    port = port_entry.get()
    if username and ip_address and key_path and port:
        ssh_command = f"ssh -i {key_path} -p {port} {username}@{ip_address}"
        remote_browser_window = tk.Toplevel(root)
        remote_browser_window.title("Select Remote File")

        def on_select(path):
            remote_file_entry.delete(0, tk.END)
            remote_file_entry.insert(0, path)

        RemoteFileBrowser(remote_browser_window, ssh_command, on_select)
    else:
        messagebox.showerror("Error", "Please fill in all connection fields")


def browse_remote_path():
    """
    Open a remote file browser dialog to select a path from the remote server.
    """
    username = username_entry.get()
    ip_address = ip_entry.get()
    key_path = key_file_entry.get()
    port = port_entry.get()
    if username and ip_address and key_path and port:
        ssh_command = f"ssh -i {key_path} -p {port} {username}@{ip_address}"
        remote_browser_window = tk.Toplevel(root)
        remote_browser_window.title("Select Remote Path")

        def on_select(path):
            remote_path_upload_entry.delete(0, tk.END)
            remote_path_upload_entry.insert(0, path)

        RemoteFileBrowser(remote_browser_window, ssh_command, on_select)
    else:
        messagebox.showerror("Error", "Please fill in all connection fields")


def load_config_file():
    """
    Open a file dialog to load a previously saved configuration from a JSON file.
    Populates the fields (username, IP address, key path, port) with the loaded data.
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
            port_entry.delete(0, tk.END)
            port_entry.insert(0, config.get("port", "22"))


# GUI setup

root = tk.Tk()
root.title("SSH Connect")

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

tk.Label(connect_frame, text="Port:").grid(row=2, column=0, sticky="w")
port_entry = tk.Entry(connect_frame)
port_entry.insert(0, "22")  # Default SSH port
port_entry.grid(row=2, column=1)

tk.Label(connect_frame, text="SSH Key File:").grid(row=3, column=0, sticky="w")
key_file_entry = tk.Entry(connect_frame)
key_file_entry.grid(row=3, column=1)
browse_button = tk.Button(connect_frame, text="Browse", command=browse_key_file)
browse_button.grid(row=3, column=2, padx=5)

connect_button = tk.Button(connect_frame, text="Connect", command=connect_to_instance)
connect_button.grid(row=4, column=0, columnspan=3, pady=10)
load_config_button = tk.Button(connect_frame, text="Load Config", command=load_config_file)
load_config_button.grid(row=5, column=0, columnspan=3, pady=10)
test_connection_button = tk.Button(connect_frame, text="Test Connection", command=test_connection)
test_connection_button.grid(row=6, column=0, columnspan=3, pady=10)

# Disk space check button and label
check_disk_button = tk.Button(connect_frame, text="Check Disk Space", command=check_disk_space)
check_disk_button.grid(row=8, column=0, columnspan=3, pady=10)

disk_space_label = tk.Label(connect_frame, text="", font=("TkDefaultFont", 9), wraplength=250)
disk_space_label.grid(row=9, column=0, columnspan=3, pady=5)

current_os = platform.system()
if current_os == "Darwin":
    terminal_options = ["Standard", "Warp"]
elif current_os == "Linux":
    terminal_options = ["Standard"]
else:
    terminal_options = []
tk.Label(connect_frame, text="Terminal:").grid(row=7, column=0, sticky="w")
terminal_var = tk.StringVar()
terminal_combobox = ttk.Combobox(connect_frame, textvariable=terminal_var, state="readonly")
terminal_combobox["values"] = terminal_options
if terminal_options:
    terminal_var.set(terminal_options[0])
terminal_combobox.grid(row=7, column=1, columnspan=2, sticky="ew")

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

download_status_label = tk.Label(download_frame, text="")
download_status_label.grid(row=3, column=0, columnspan=3, pady=5)

download_progress = ttk.Progressbar(download_frame, orient="horizontal", mode="determinate", length=300)
download_progress.grid(row=4, column=0, columnspan=3, pady=5)

download_live_file_label = tk.Label(download_frame, text="", width=30)
download_live_file_label.grid(row=5, column=0, columnspan=3)
download_speed_label = tk.Label(download_frame, text="", width=15)
download_speed_label.grid(row=6, column=0, columnspan=2, sticky="w")
download_eta_label = tk.Label(download_frame, text="", width=15)
download_eta_label.grid(row=6, column=2, sticky="w")

# Hide download widgets initially
download_progress.grid_remove()
download_live_file_label.grid_remove()
download_speed_label.grid_remove()
download_eta_label.grid_remove()

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

upload_status_label = tk.Label(upload_frame, text="")
upload_status_label.grid(row=3, column=0, columnspan=3, pady=5)

upload_progress = ttk.Progressbar(upload_frame, orient="horizontal", mode="determinate", length=300)
upload_progress.grid(row=4, column=0, columnspan=3, pady=5)

upload_live_file_label = tk.Label(upload_frame, text="", width=30)
upload_live_file_label.grid(row=5, column=0, columnspan=3)
upload_speed_label = tk.Label(upload_frame, text="", width=15)
upload_speed_label.grid(row=6, column=0, columnspan=2, sticky="w")
upload_eta_label = tk.Label(upload_frame, text="", width=15)
upload_eta_label.grid(row=6, column=2, sticky="w")

# Hide upload widgets initially
upload_progress.grid_remove()
upload_live_file_label.grid_remove()
upload_speed_label.grid_remove()
upload_eta_label.grid_remove()


def load_last_used_config():
    config_files = glob.glob(os.path.join(CONFIG_DIR, "config_*.json"))
    if not config_files:
        return

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
        port_entry.delete(0, tk.END)
        port_entry.insert(0, config.get("port", "22"))


load_last_used_config()

# Run the application
root.mainloop()
