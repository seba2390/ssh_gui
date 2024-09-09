import tkinter as tk
from tkinter import ttk
import os
import subprocess


def format_size(size_in_bytes):
    """
    Convert a size in bytes to a human-readable string with units (Bytes, KB, MB, GB, etc.)
    using base 10 (1 KB = 1000 bytes).

    Args:
        size_in_bytes (int): The size in bytes.

    Returns:
        str: The human-readable size with the appropriate unit.
    """
    # Define the units
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_in_bytes)
    unit_index = 0

    # Loop to find the appropriate unit
    while size >= 1000 and unit_index < len(units) - 1:
        size /= 1000
        unit_index += 1

    # Format the size with one decimal place, but avoid decimals for Bytes
    if unit_index == 0:  # Bytes
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


class RemoteFileBrowser:
    """
    A class to represent a remote file browser through an SSH connection.
    This class allows users to browse files and directories on a remote server
    using SSH and select a file or directory to return.

    Attributes:
        master (Tk): The parent tkinter window.
        ssh_command (str): The SSH command to connect to the remote server.
        on_select_callback (function): Callback function when a file or directory is selected.
        current_path (str): Current path on the remote server being browsed.
        forward_history (list): Stack to track forward navigation history.
        path_var (StringVar): Tkinter variable to hold and update the current path.
        tree (Treeview): Treeview widget to display files and directories.
    """

    def __init__(self, master, ssh_command, on_select_callback):
        """
        Initialize the RemoteFileBrowser class.

        Args:
            master (Tk): The parent tkinter window.
            ssh_command (str): The SSH command to connect to the remote server.
            on_select_callback (function): Callback function when a file or directory is selected.
        """
        self.master = master
        self.ssh_command = ssh_command
        self.on_select_callback = on_select_callback

        self.current_path = "/"
        self.forward_history = []

        self.path_var = tk.StringVar()
        self.path_var.set(self.current_path)

        self.create_widgets()

    def create_widgets(self):
        """
        Create and arrange the widgets for the remote file browser.
        Includes navigation buttons, path entry, file treeview, and select button.
        """
        nav_frame = ttk.Frame(self.master)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)

        back_button = ttk.Button(nav_frame, text="←", command=self.go_up, width=3)
        back_button.pack(side=tk.LEFT, padx=(0, 5))

        forward_button = ttk.Button(nav_frame, text="→", command=self.go_forward, width=3)
        forward_button.pack(side=tk.LEFT, padx=(0, 5))

        path_entry = ttk.Entry(nav_frame, textvariable=self.path_var, width=50)
        path_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        refresh_button = ttk.Button(nav_frame, text="Refresh", command=self.refresh)
        refresh_button.pack(side=tk.LEFT)

        # File/Directory Treeview
        self.tree = ttk.Treeview(self.master, columns=("Type", "Permissions", "Size"))
        self.tree.heading("#0", text="Name")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Permissions", text="Permissions")
        self.tree.heading("Size", text="Size")
        self.tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        self.tree.bind("<Double-1>", self.on_double_click)

        # Button to select a file or directory
        select_button = ttk.Button(self.master, text="Select", command=self.select_item)
        select_button.pack(pady=5)

        self.refresh()

    def select_item(self):
        """
        Trigger the selection callback when an item is selected.
        The selected path is passed to the callback, and the window is closed.
        """
        selected_path = self.get_selected_path()
        if selected_path:
            self.on_select_callback(selected_path)
            self.master.destroy()

    def execute_command(self, command):
        """
        Execute a shell command using SSH and return the output.

        Args:
            command (str): The command to execute on the remote server.

        Returns:
            str: The standard output of the executed command.
        """
        full_command = f"{self.ssh_command} '{command}'"
        result = subprocess.run(full_command, capture_output=True, text=True, shell=True)
        return result.stdout

    def refresh(self):
        """
        Refresh the file and directory listing in the treeview.
        Fetches the list of files and directories in the current remote path.
        """
        # Clear the current tree items
        self.tree.delete(*self.tree.get_children())

        # Execute 'ls -la' command on the remote server
        ls_output = self.execute_command(f'ls -la "{self.current_path}"')
        lines = ls_output.split('\n')[1:]  # Skip the first line (total)

        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 9:
                    permissions, _, _, _, size, *_, name = parts
                    name = ' '.join(parts[8:])  # Join the name parts in case of spaces

                    # Determine the type of the item (file, directory, or link)
                    if permissions.startswith('d'):
                        item_type = "Directory"
                        size = ""  # Leave the size column blank for directories
                    elif permissions.startswith('l'):
                        item_type = "Link"
                        size = ""  # Leave the size column blank for links
                    else:
                        item_type = "File"
                        # Convert the size to human-readable format
                        size = format_size(int(size))  # Display size only for files

                    self.tree.insert("", "end", text=name, values=(item_type, permissions, size))

    def on_double_click(self, event):
        """
        Event handler for double-clicking an item in the treeview.
        Navigates into the directory if a directory is double-clicked.

        Args:
            event (Event): The tkinter event triggered by the double-click.
        """
        item = self.tree.selection()[0]
        item_type = self.tree.item(item, "values")[0]
        name = self.tree.item(item, "text")

        if item_type == "Directory":
            new_path = os.path.join(self.current_path, name).replace("\\", "/")
            self.navigate_to(new_path)

    def navigate_to(self, path):
        """
        Navigate to a specified path and refresh the listing.

        Args:
            path (str): The path to navigate to.
        """
        self.forward_history.clear()  # Clear forward history when navigating to a new path
        self.current_path = path
        self.path_var.set(self.current_path)
        self.refresh()

    def go_up(self):
        """
        Navigate one directory up in the file system.
        Updates the current path and refreshes the listing.
        """
        parent_path = os.path.dirname(self.current_path)
        if parent_path != self.current_path:  # Check if not at root
            self.forward_history.append(self.current_path)
            self.current_path = parent_path
            self.path_var.set(self.current_path)
            self.refresh()

    def go_forward(self):
        """
        Navigate forward to the last visited directory, if any.
        """
        if self.forward_history:
            next_path = self.forward_history.pop()
            self.current_path = next_path
            self.path_var.set(self.current_path)
            self.refresh()

    def get_selected_path(self):
        """
        Get the full path of the currently selected file or directory in the treeview.

        Returns:
            str: The full path of the selected file or directory.
        """
        item = self.tree.selection()[0]
        name = self.tree.item(item, "text")
        return os.path.join(self.current_path, name).replace("\\", "/")