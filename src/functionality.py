"""
SSH GUI - Functionality Module

This module contains all the business logic and SSH-related functions for the SSH GUI application.
Includes configuration management, SSH operations, file transfers, and remote operations.

Features:
    - Configuration file management (save/load SSH credentials)
    - SSH connection testing and terminal launching
    - Remote disk space monitoring
    - File transfer operations via rsync
    - Remote directory detection

Author: SSH GUI Team
Version: 2.0
License: MIT
"""

import glob
import json
import os
import platform
import re
import subprocess
import time
from typing import Optional
from tkinter import messagebox

# Constants for configuration directory and default configuration file
CONFIG_DIR = "configurations"
DEFAULT_CONFIG_FILE = "config.json"

# Ensure the configurations directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)


def truncate_filename(filename: str, max_length: int) -> str:
    """
    Truncate a filename to fit within max_length characters, inserting an ellipsis in the middle if needed.

    This function is useful for displaying long filenames in constrained UI spaces while maintaining
    readability by showing both the beginning and end of the filename.

    Args:
        filename: The complete filename to potentially truncate
        max_length: Maximum allowed length for the returned string

    Returns:
        str: The original filename if it fits within max_length, otherwise a truncated version
             with an ellipsis (…) in the middle

    Example:
        >>> truncate_filename("very_long_filename_example.txt", 20)
        "very_lon…mple.txt"
    """
    if len(filename) <= max_length:
        return filename
    # Calculate how many characters to keep from each end
    part = (max_length - 3) // 2
    return f"{filename[:part]}…{filename[-part:]}"


def load_config(file_path: str) -> Optional[dict[str, str]]:
    """
    Load SSH configuration data from a JSON file.

    Reads and parses a JSON configuration file containing SSH connection details
    such as username, IP address, SSH key path, and port number.

    Args:
        file_path: Absolute or relative path to the configuration JSON file

    Returns:
        Optional[dict[str, str]]: Dictionary containing configuration data with keys:
            - username: SSH username
            - ip_address: Remote server IP address
            - key_path: Path to SSH private key file
            - port: SSH port number
        Returns None if the file doesn't exist or cannot be read

    Raises:
        json.JSONDecodeError: If the file exists but contains invalid JSON

    Example:
        >>> config = load_config("configurations/config.json")
        >>> if config:
        >>>     print(config['username'])
    """
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    return None


def save_config(username: str, ip_address: str, key_path: str, port: str) -> None:
    """
    Save SSH configuration details to a JSON file.

    Creates a new configuration file only if an identical configuration doesn't already exist.
    This prevents duplicate configurations and maintains a clean configurations directory.
    Configuration files are automatically numbered (config_1.json, config_2.json, etc.).

    Args:
        username: SSH username for remote server authentication
        ip_address: IP address or hostname of the remote server
        key_path: Absolute or relative path to the SSH private key file
        port: SSH port number (typically "22" for standard SSH)

    Returns:
        None

    Side Effects:
        - Creates the configurations directory if it doesn't exist
        - Creates a new JSON file in the configurations directory if no matching config exists
        - File naming pattern: config.json, config_1.json, config_2.json, etc.

    Example:
        >>> save_config("ubuntu", "192.168.1.100", "~/.ssh/id_rsa", "22")
        # Creates config_1.json if config differs from existing files
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

    # Ensure the new file name is unique by incrementing counter
    while os.path.exists(new_file_path):
        counter += 1
        new_file_name = f"{base_name}_{counter}{ext}"
        new_file_path = os.path.join(CONFIG_DIR, new_file_name)

    # Save the new configuration data to the new file
    with open(new_file_path, "w") as file:
        json.dump(config_data, file, indent=2)


def test_ssh_connection(username: str, ip_address: str, key_path: str, port: str) -> tuple[bool, str]:
    """
    Test SSH connection viability by executing a simple remote command.

    Attempts to establish an SSH connection and immediately exit, validating that
    credentials and network connectivity are correct without maintaining a session.

    Args:
        username: SSH username for authentication
        ip_address: Target server IP address or hostname
        key_path: Path to SSH private key file for authentication
        port: SSH port number (standard is "22")

    Returns:
        tuple[bool, str]: A tuple containing:
            - bool: True if connection successful, False otherwise
            - str: Success message or error description

    Note:
        Uses StrictHostKeyChecking=no to avoid interactive prompts.
        This should only be used in controlled environments.

    Example:
        >>> success, message = test_ssh_connection("user", "192.168.1.1", "~/.ssh/key", "22")
        >>> if success:
        >>>     print("Connected successfully!")
    """
    if not all([username, ip_address, key_path, port]):
        return False, "Please fill in all fields"

    # Construct SSH command that immediately exits after successful connection
    ssh_command = f"ssh -i {key_path} -p {port} -o StrictHostKeyChecking=no {username}@{ip_address} exit"
    result = subprocess.run(ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        return True, "Connection successful!"
    else:
        return False, f"Connection failed: {result.stderr}"


def check_remote_disk_space(username: str, ip_address: str, key_path: str, port: str) -> tuple[bool, str, str]:
    """
    Check and retrieve disk space information from remote server.

    Executes 'df -h /' on the remote server to gather filesystem usage statistics
    including total size, used space, available space, and usage percentage.

    Args:
        username: SSH username for authentication
        ip_address: Target server IP address or hostname
        key_path: Path to SSH private key file
        port: SSH port number

    Returns:
        tuple[bool, str, str]: A tuple containing:
            - bool: True if retrieval successful, False otherwise
            - str: Formatted disk space information or error message
            - str: Text color for UI display ("green" for success, "red" for error)

    The success message format:
        "Total: <size> | Used: <size> (<percent>) | Available: <size>"

    Example:
        >>> success, info, color = check_remote_disk_space("user", "192.168.1.1", "~/.ssh/key", "22")
        >>> if success:
        >>>     print(info)  # "Total: 50G | Used: 20G (40%) | Available: 30G"
    """
    if not all([username, ip_address, key_path, port]):
        return False, "Please fill in all connection fields", "red"

    ssh_command = f"ssh -i {key_path} -p {port} -o StrictHostKeyChecking=no {username}@{ip_address} 'df -h /'"
    result = subprocess.run(ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 5:
                size = parts[1]
                used = parts[2]
                available = parts[3]
                use_percent = parts[4]
                disk_info = f"Total: {size} | Used: {used} ({use_percent}) | Available: {available}"
                return True, disk_info, "green"
            else:
                return False, "Could not parse disk space info", "red"
        else:
            return False, "Could not retrieve disk space info", "red"
    else:
        return False, f"Error: {result.stderr}", "red"


def is_remote_directory(key_path: str, username: str, ip_address: str, remote_path: str, port: str) -> bool:
    """
    Determine whether a remote path is a directory or file using SSH test command.

    Executes a remote shell test to differentiate between directories and files.
    This is useful before file transfer operations to apply appropriate flags.

    Args:
        key_path: Path to SSH private key file for authentication
        username: SSH username for remote server
        ip_address: Target server IP address or hostname
        remote_path: Absolute path on remote server to check
        port: SSH port number (typically "22")

    Returns:
        bool: True if path is a directory, False if it's a regular file

    Raises:
        Exception: If unable to determine path type due to SSH errors or invalid path

    Example:
        >>> is_dir = is_remote_directory("~/.ssh/key", "user", "192.168.1.1", "/home/user/data", "22")
        >>> if is_dir:
        >>>     print("Path is a directory")
    """
    # Use shell test command to check if path is a directory
    ssh_command = f"ssh -i {key_path} -p {port} {username}@{ip_address} 'test -d {remote_path} && echo directory || echo file'"
    result = subprocess.run(ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if "directory" in result.stdout:
        return True
    elif "file" in result.stdout:
        return False
    else:
        raise Exception(f"Unable to determine if {remote_path} is a directory or file. SSH Error: {result.stderr}")


def open_ssh_terminal(key_path: str, username: str, ip_address: str, port: str, terminal_type: str) -> None:
    """
    Launch a new terminal window with an active SSH session to the remote server.

    Opens the specified terminal emulator and establishes an SSH connection with
    keep-alive settings to prevent disconnection. Supports different terminal types
    on different operating systems.

    Args:
        key_path: Absolute or relative path to SSH private key file
        username: SSH username for authentication
        ip_address: Target server IP address or hostname
        port: SSH port number (standard is "22")
        terminal_type: Terminal emulator to use. Options:
            - "Standard": Default Terminal app (macOS) or gnome-terminal (Linux)
            - "Warp": Warp terminal (macOS only, requires installation)

    Returns:
        None

    Side Effects:
        - Launches a new terminal window/tab
        - Initiates an SSH session in the terminal
        - Shows error dialog if terminal type unsupported or script missing

    SSH Connection Options:
        - StrictHostKeyChecking=no: Disables host key verification prompts
        - ServerAliveInterval=60: Sends keep-alive every 60 seconds
        - ServerAliveCountMax=2: Disconnects after 2 failed keep-alives

    Note:
        For Warp terminal on macOS, requires 'src/run_in_warp.sh' script with execute permissions.
        Use 'chmod +x src/run_in_warp.sh' if Warp terminal doesn't launch.

    Example:
        >>> open_ssh_terminal("~/.ssh/key", "ubuntu", "192.168.1.100", "22", "Standard")
    """
    ssh_command = f"ssh -i {key_path} -p {port} -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=2 {username}@{ip_address}"
    current_os = platform.system()

    if current_os == "Darwin":  # macOS
        if terminal_type == "Standard":
            terminal_command = f'''
            tell application "Terminal"
                do script "{ssh_command}"
                activate
            end tell
            '''
            subprocess.Popen(["osascript", "-e", terminal_command])
        elif terminal_type == "Warp":
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "run_in_warp.sh")
            if os.path.exists(script_path):
                subprocess.Popen([script_path, ssh_command])
            else:
                messagebox.showerror("Error", f"Warp script not found at {script_path}")
        else:
            messagebox.showerror("Error", f"Unsupported terminal type: {terminal_type}")
    elif current_os == "Linux":
        if terminal_type == "Standard":
            terminal_command = f"gnome-terminal -- bash -c '{ssh_command}; exec bash'"
            subprocess.Popen(terminal_command, shell=True)
        else:
            messagebox.showerror("Error", f"Unsupported terminal type: {terminal_type}")
    else:
        messagebox.showerror("Error", f"Unsupported operating system: {current_os}")


def run_rsync_command(
    key_path: str,
    username: str,
    ip_address: str,
    port: str,
    src_path: str,
    dest_path: str,
    direction: str,
    status_label: object,
    progress_bar: object,
    filename_label: Optional[object] = None,
    speed_label: Optional[object] = None,
    eta_label: Optional[object] = None,
) -> None:
    """
    Execute rsync file transfer between local and remote servers with real-time progress tracking.

    Uses rsync over SSH for efficient file synchronization with features like compression,
    progress monitoring, and partial file transfer support. Provides real-time updates
    to GUI widgets showing transfer progress, speed, ETA, and current filename.

    Args:
        key_path: Path to SSH private key file for authentication
        username: SSH username for remote server
        ip_address: Target server IP address or hostname
        port: SSH port number (typically "22")
        src_path: Source path for transfer (local or remote depending on direction)
        dest_path: Destination path for transfer (local or remote depending on direction)
        direction: Transfer direction - "download" (remote→local) or "upload" (local→remote)
        status_label: Tkinter Label widget for displaying status messages
        progress_bar: Tkinter Progressbar widget (ttk.Progressbar) for visual progress
        filename_label: Optional Tkinter Label for showing current transferring filename
        speed_label: Optional Tkinter Label for displaying transfer speed (e.g., "2.5MB/s")
        eta_label: Optional Tkinter Label for showing estimated time to completion

    Returns:
        None

    Side Effects:
        - Updates all provided GUI widgets in real-time during transfer
        - Creates destination directories if they don't exist
        - Modifies progress_bar value from 0 to 100
        - Updates status_label text throughout transfer

    Rsync Flags Used:
        -a: Archive mode (preserves permissions, timestamps, etc.)
        -z: Compress data during transfer
        -P: Show progress and keep partial files
        -e: Specify SSH command with custom options

    Example:
        >>> run_rsync_command(
        ...     "~/.ssh/key", "user", "192.168.1.1", "22",
        ...     "/remote/file.tar.gz", "/local/dest/", "download",
        ...     status_label, progress_bar,
        ...     filename_label=file_label,
        ...     speed_label=speed_label,
        ...     eta_label=eta_label
        ... )
    """
    # Initialize progress tracking
    progress_bar["value"] = 0
    is_directory = False

    # Variables for ETA calculation
    start_time = time.time()
    last_progress = 0
    last_time = start_time

    # Determine if source is a directory for appropriate handling
    if direction == "download":
        is_directory = is_remote_directory(key_path, username, ip_address, src_path, port)
    elif direction == "upload":
        is_directory = os.path.isdir(src_path)

    # Update status label based on source type
    if is_directory:
        status_label.config(text=f"{direction.capitalize()} in progress... (Folder)")
    else:
        status_label.config(text=f"{direction.capitalize()} in progress...")

    # Construct rsync command based on transfer direction
    if direction == "download":
        command = f"rsync -azP -e 'ssh -i {key_path} -p {port}' {username}@{ip_address}:{src_path} {dest_path}"
    else:  # upload
        command = f"rsync -azP -e 'ssh -i {key_path} -p {port}' {src_path} {username}@{ip_address}:{dest_path}"

    # Start rsync process and capture output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    progress_regex = re.compile(r"(\d+)\%")

    # Process rsync output line by line
    while True:
        if process.stdout is None:
            break
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break

        # Detect and display current filename being transferred
        if (
            filename_label
            and output.strip()
            and not progress_regex.search(output)
            and "to-check" not in output
            and "%" not in output
        ):
            current_file = output.strip()
            truncated = truncate_filename(current_file, int(filename_label.cget("width")))
            filename_label.config(text=truncated)
            filename_label.update()

        current_progress = 0

        # Update progress for single files based on percentage
        if not is_directory:
            match = progress_regex.search(output)
            if match:
                percent = int(match.group(1))
                current_progress = percent
                progress_bar["value"] = percent
                status_label.config(text=f"{direction.capitalize()} in progress... {percent}%")
        else:
            # For directories, calculate progress from file count
            if "to-check" in output:
                m = re.search(r"to-check=(\d+)/(\d+)", output)
                if m:
                    checked = int(m.group(2)) - int(m.group(1))
                    total = int(m.group(2))
                    percent = int((checked / total) * 100)
                    current_progress = percent
                    progress_bar["value"] = percent
            progress_bar.update()

        # Parse and display transfer speed from rsync output
        speed_match = re.search(r"([0-9.]+[KMG]?B/s)", output)
        if speed_match and speed_label:
            speed = speed_match.group(1)
            speed_label.config(text=f"{speed}")
            speed_label.update()

        # Calculate and display ETA based on overall progress
        if current_progress > last_progress and current_progress > 0:
            current_time = time.time()
            elapsed_time = current_time - start_time

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

    # Wait for process completion and update final status
    process.wait()
    progress_bar["value"] = 100
    status_label.config(text=f"{direction.capitalize()} Complete!")


def load_last_used_config() -> Optional[dict[str, str]]:
    """
    Load the most recently created configuration file from the configurations directory.

    Scans all numbered configuration files and returns the one with the highest number,
    representing the most recent connection settings saved by the user.

    Returns:
        Optional[dict[str, str]]: Configuration dictionary containing:
            - username: SSH username
            - ip_address: Remote server IP
            - key_path: SSH key file path
            - port: SSH port number
        Returns None if no configuration files exist

    Example:
        >>> config = load_last_used_config()
        >>> if config:
        >>>     print(f"Last connected to {config['ip_address']}")
    """
    # Find all config files matching the pattern
    config_files = glob.glob(os.path.join(CONFIG_DIR, "config_*.json"))
    if not config_files:
        return None

    # Extract numeric suffix from filename for sorting
    def extract_number(f: str) -> int:
        """Extract the configuration number from filename."""
        m = re.search(r"config_(\d+)\.json$", f)
        return int(m.group(1)) if m else 0

    # Sort files by number and get the most recent
    config_files.sort(key=extract_number)
    last_config = config_files[-1]
    return load_config(last_config)


def load_last_used_config() -> dict:
    """
    Load the most recently used configuration file.

    Returns:
        Configuration dictionary or None if no configs exist
    """
    config_files = glob.glob(os.path.join(CONFIG_DIR, "config_*.json"))
    if not config_files:
        return None

    def extract_number(f):
        m = re.search(r"config_(\d+)\.json$", f)
        return int(m.group(1)) if m else 0

    config_files.sort(key=extract_number)
    last_config = config_files[-1]
    return load_config(last_config)
