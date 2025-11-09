"""
SSH GUI - Visuals Module

This module contains all the GUI components and visual elements for the SSH GUI application.
Handles window creation, widget layout, styling, and user interface components.
"""

import os
import platform
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.functionality import (
    save_config,
    test_ssh_connection,
    check_remote_disk_space,
    open_ssh_terminal,
    run_rsync_command,
    load_config,
    load_last_used_config,
    CONFIG_DIR,
)
from src.remote_file_browser import RemoteFileBrowser


class SSHGuiApp:
    """Main SSH GUI Application class containing all visual elements and event handlers."""

    def __init__(self, root):
        """
        Initialize the SSH GUI application.

        Args:
            root: The Tkinter root window
        """
        self.root = root
        self.root.title("SSH Connect Pro")

        # Window dimensions
        self.window_width = 700
        self.window_height = 480

        # Define color scheme
        self.BG_COLOR = "#1a1d29"
        self.FRAME_BG = "#252936"
        self.PRIMARY_COLOR = "#00d4ff"
        self.PRIMARY_HOVER = "#00b8e6"
        self.SUCCESS_COLOR = "#00ff88"
        self.DANGER_COLOR = "#ff0055"
        self.TEXT_COLOR = "#e4e6eb"
        self.LABEL_COLOR = "#8b92a8"
        self.ENTRY_BG = "#2f3241"
        self.BORDER_COLOR = "#3d4152"
        self.ACCENT_COLOR = "#7b61ff"

        # Define fonts
        self.TITLE_FONT = ("SF Pro Display", 12, "bold") if platform.system() == "Darwin" else ("Segoe UI", 12, "bold")
        self.SUBTITLE_FONT = ("SF Pro Display", 10, "bold") if platform.system() == "Darwin" else ("Segoe UI", 10, "bold")
        self.LABEL_FONT = ("SF Pro Text", 9) if platform.system() == "Darwin" else ("Segoe UI", 9)
        self.BUTTON_FONT = ("SF Pro Text", 10) if platform.system() == "Darwin" else ("Segoe UI", 10)
        self.ENTRY_FONT = ("SF Mono", 9) if platform.system() == "Darwin" else ("Consolas", 9)

        # Button style dictionary with consistent height
        self.button_style = {
            "font": self.BUTTON_FONT,
            "relief": "flat",
            "bd": 0,
            "cursor": "hand2",
            "pady": 6
        }

        # Configure root window
        self.root.configure(bg=self.BG_COLOR)
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.minsize(self.window_width, self.window_height - 20)

        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Create GUI components
        self.create_connection_frame()
        self.create_transfer_frame()

        # Load last used configuration
        self.load_last_config()

        # Apply platform-specific window focus fix
        self.apply_window_focus_fix()

    def create_connection_frame(self):
        """Create the connection settings frame with all input fields and buttons."""
        connect_frame = tk.LabelFrame(
            self.root,
            text="  CONNECTION  ",
            padx=16,
            pady=16,
            bg=self.FRAME_BG,
            fg=self.PRIMARY_COLOR,
            font=self.TITLE_FONT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.BORDER_COLOR
        )
        connect_frame.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        # Username
        tk.Label(connect_frame, text="Username", bg=self.FRAME_BG, fg=self.LABEL_COLOR, font=self.LABEL_FONT, anchor="w").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.username_entry = tk.Entry(connect_frame, font=self.ENTRY_FONT, bg=self.ENTRY_BG, fg=self.TEXT_COLOR, relief="flat", bd=0,
                              highlightthickness=1, highlightbackground=self.BORDER_COLOR, highlightcolor=self.PRIMARY_COLOR,
                              insertbackground=self.PRIMARY_COLOR)
        self.username_entry.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10), ipady=6)

        # IP Address
        tk.Label(connect_frame, text="IP Address", bg=self.FRAME_BG, fg=self.LABEL_COLOR, font=self.LABEL_FONT, anchor="w").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self.ip_entry = tk.Entry(connect_frame, font=self.ENTRY_FONT, bg=self.ENTRY_BG, fg=self.TEXT_COLOR, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=self.BORDER_COLOR, highlightcolor=self.PRIMARY_COLOR,
                        insertbackground=self.PRIMARY_COLOR)
        self.ip_entry.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 10), ipady=6)

        # Port
        tk.Label(connect_frame, text="Port", bg=self.FRAME_BG, fg=self.LABEL_COLOR, font=self.LABEL_FONT, anchor="w").grid(
            row=4, column=0, sticky="w", pady=(0, 4)
        )
        self.port_entry = tk.Entry(connect_frame, font=self.ENTRY_FONT, bg=self.ENTRY_BG, fg=self.TEXT_COLOR, relief="flat", bd=0,
                          highlightthickness=1, highlightbackground=self.BORDER_COLOR, highlightcolor=self.PRIMARY_COLOR,
                          insertbackground=self.PRIMARY_COLOR)
        self.port_entry.insert(0, "22")
        self.port_entry.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 10), ipady=6)

        # SSH Key File
        tk.Label(connect_frame, text="SSH Key File", bg=self.FRAME_BG, fg=self.LABEL_COLOR, font=self.LABEL_FONT, anchor="w").grid(
            row=6, column=0, sticky="w", pady=(0, 4)
        )
        self.key_file_entry = tk.Entry(connect_frame, font=self.ENTRY_FONT, bg=self.ENTRY_BG, fg=self.TEXT_COLOR, relief="flat", bd=0,
                              highlightthickness=1, highlightbackground=self.BORDER_COLOR, highlightcolor=self.PRIMARY_COLOR,
                              insertbackground=self.PRIMARY_COLOR)
        self.key_file_entry.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 10), ipady=6)
        browse_button = tk.Button(connect_frame, text="...", command=self.browse_key_file, bg=self.ENTRY_BG, fg=self.LABEL_COLOR,
                             font=self.BUTTON_FONT, relief="flat", bd=0, cursor="hand2",
                             activebackground=self.BORDER_COLOR, activeforeground=self.TEXT_COLOR, padx=12)
        browse_button.grid(row=7, column=2, padx=(6, 0), pady=(0, 10))

        # Load Config Button
        load_config_button = tk.Button(connect_frame, text="Load Config", command=self.load_config_file,
                                  bg=self.BORDER_COLOR, fg=self.BG_COLOR, activebackground="#4a4d5e",
                                  activeforeground=self.BG_COLOR, **self.button_style)
        load_config_button.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(0, 10), ipady=0)

        # Terminal
        tk.Label(connect_frame, text="Terminal", bg=self.FRAME_BG, fg=self.LABEL_COLOR, font=self.LABEL_FONT, anchor="w").grid(
            row=9, column=0, sticky="w", pady=(0, 4)
        )
        current_os = platform.system()
        if current_os == "Darwin":
            terminal_options = ["Standard", "Warp"]
        elif current_os == "Linux":
            terminal_options = ["Standard"]
        else:
            terminal_options = []
        self.terminal_var = tk.StringVar()
        terminal_combobox = ttk.Combobox(connect_frame, textvariable=self.terminal_var, state="readonly", font=self.ENTRY_FONT)
        terminal_combobox["values"] = terminal_options
        if terminal_options:
            self.terminal_var.set(terminal_options[0])
        terminal_combobox.grid(row=10, column=0, columnspan=3, sticky="ew", pady=(0, 10), ipady=4)

        # Connect and Test buttons
        connect_button = tk.Button(connect_frame, text="Connect", command=self.connect_to_instance,
                              bg=self.PRIMARY_COLOR, fg=self.BG_COLOR, activebackground=self.PRIMARY_HOVER,
                              activeforeground=self.BG_COLOR, **self.button_style)
        connect_button.grid(row=11, column=0, sticky="ew", pady=(0, 5), padx=(0, 3), ipady=0)

        test_connection_button = tk.Button(connect_frame, text="Test Connection", command=self.test_connection,
                                      bg=self.SUCCESS_COLOR, fg=self.BG_COLOR, activebackground="#00e67a",
                                      activeforeground=self.BG_COLOR, **self.button_style)
        test_connection_button.grid(row=11, column=1, columnspan=2, sticky="ew", pady=(0, 5), padx=(3, 0), ipady=0)

        # Check Disk Space button
        check_disk_button = tk.Button(connect_frame, text="Check Disk Space", command=self.check_disk_space,
                                 bg=self.ACCENT_COLOR, fg=self.BG_COLOR, activebackground="#6950e6",
                                 activeforeground=self.BG_COLOR, **self.button_style)
        check_disk_button.grid(row=12, column=0, columnspan=3, sticky="ew", pady=(0, 5), ipady=0)

        # Disk space label
        self.disk_space_label = tk.Label(connect_frame, text="", font=("SF Mono", 8) if platform.system() == "Darwin" else ("Consolas", 8),
                               bg=self.FRAME_BG, fg=self.LABEL_COLOR, wraplength=280, justify="center")
        self.disk_space_label.grid(row=13, column=0, columnspan=3, pady=(6, 0))

        connect_frame.grid_columnconfigure(0, weight=1)

    def create_transfer_frame(self):
        """Create the file transfer frame with upload and download sections."""
        transfer_frame = tk.LabelFrame(
            self.root,
            text="  FILE TRANSFER  ",
            padx=16,
            pady=16,
            bg=self.FRAME_BG,
            fg=self.PRIMARY_COLOR,
            font=self.TITLE_FONT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.BORDER_COLOR
        )
        transfer_frame.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        # === UPLOAD SECTION ===
        tk.Label(transfer_frame, text="UPLOAD", bg=self.FRAME_BG, fg=self.TEXT_COLOR, font=self.SUBTITLE_FONT, anchor="w").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 6)
        )

        # Local File Path
        tk.Label(transfer_frame, text="Local File Path", bg=self.FRAME_BG, fg=self.LABEL_COLOR, font=self.LABEL_FONT, anchor="w").grid(
            row=1, column=0, sticky="w", pady=(0, 4)
        )
        self.local_file_entry = tk.Entry(transfer_frame, font=self.ENTRY_FONT, bg=self.ENTRY_BG, fg=self.TEXT_COLOR, relief="flat", bd=0,
                               highlightthickness=1, highlightbackground=self.BORDER_COLOR, highlightcolor=self.PRIMARY_COLOR,
                               insertbackground=self.PRIMARY_COLOR)
        self.local_file_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10), ipady=6)
        self.browse_local_file_button = tk.Button(transfer_frame, text="...", command=self.browse_local_file, bg=self.ENTRY_BG, fg=self.LABEL_COLOR,
                                        font=self.BUTTON_FONT, relief="flat", bd=0, cursor="hand2",
                                        activebackground=self.BORDER_COLOR, activeforeground=self.TEXT_COLOR, padx=12)
        self.browse_local_file_button.grid(row=2, column=2, padx=(6, 0), pady=(0, 10))

        # Remote Destination Path
        tk.Label(transfer_frame, text="Remote Destination Path", bg=self.FRAME_BG, fg=self.LABEL_COLOR, font=self.LABEL_FONT, anchor="w").grid(
            row=3, column=0, sticky="w", pady=(0, 4)
        )
        self.remote_path_upload_entry = tk.Entry(transfer_frame, font=self.ENTRY_FONT, bg=self.ENTRY_BG, fg=self.TEXT_COLOR, relief="flat", bd=0,
                                        highlightthickness=1, highlightbackground=self.BORDER_COLOR, highlightcolor=self.PRIMARY_COLOR,
                                        insertbackground=self.PRIMARY_COLOR)
        self.remote_path_upload_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10), ipady=6)
        browse_remote_path_button = tk.Button(transfer_frame, text="...", command=self.browse_remote_path, bg=self.ENTRY_BG, fg=self.LABEL_COLOR,
                                         font=self.BUTTON_FONT, relief="flat", bd=0, cursor="hand2",
                                         activebackground=self.BORDER_COLOR, activeforeground=self.TEXT_COLOR, padx=12)
        browse_remote_path_button.grid(row=4, column=2, padx=(6, 0), pady=(0, 10))

        upload_button = tk.Button(transfer_frame, text="Start Upload", command=self.upload_file,
                             bg=self.PRIMARY_COLOR, fg=self.BG_COLOR, activebackground=self.PRIMARY_HOVER,
                             activeforeground=self.BG_COLOR, **self.button_style)
        upload_button.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 8), ipady=0)

        self.upload_status_label = tk.Label(transfer_frame, text="", bg=self.FRAME_BG, fg=self.LABEL_COLOR, font=self.LABEL_FONT)
        self.upload_status_label.grid(row=6, column=0, columnspan=3, pady=(0, 6))

        self.upload_progress = ttk.Progressbar(transfer_frame, orient="horizontal", mode="determinate", length=300)
        self.upload_progress.grid(row=7, column=0, columnspan=3, pady=(0, 6), sticky="ew")

        self.upload_live_file_label = tk.Label(transfer_frame, text="", bg=self.FRAME_BG, fg=self.TEXT_COLOR,
                                     font=("SF Mono", 8) if platform.system() == "Darwin" else ("Consolas", 8),
                                     wraplength=280)
        self.upload_live_file_label.grid(row=8, column=0, columnspan=3, pady=(0, 4))

        stats_frame_upload = tk.Frame(transfer_frame, bg=self.FRAME_BG)
        stats_frame_upload.grid(row=9, column=0, columnspan=3, sticky="ew")
        stats_frame_upload.grid_columnconfigure(0, weight=1)
        stats_frame_upload.grid_columnconfigure(1, weight=1)

        self.upload_speed_label = tk.Label(stats_frame_upload, text="", bg=self.FRAME_BG, fg=self.LABEL_COLOR,
                                 font=("SF Mono", 8) if platform.system() == "Darwin" else ("Consolas", 8))
        self.upload_speed_label.grid(row=0, column=0, sticky="w")
        self.upload_eta_label = tk.Label(stats_frame_upload, text="", bg=self.FRAME_BG, fg=self.LABEL_COLOR,
                               font=("SF Mono", 8) if platform.system() == "Darwin" else ("Consolas", 8))
        self.upload_eta_label.grid(row=0, column=1, sticky="e")

        # Hide upload widgets initially
        self.upload_progress.grid_remove()
        self.upload_live_file_label.grid_remove()
        stats_frame_upload.grid_remove()

        # Separator
        tk.Frame(transfer_frame, bg=self.BORDER_COLOR, height=1).grid(row=10, column=0, columnspan=3, sticky="ew", pady=(8, 8))

        # === DOWNLOAD SECTION ===
        tk.Label(transfer_frame, text="DOWNLOAD", bg=self.FRAME_BG, fg=self.TEXT_COLOR, font=self.SUBTITLE_FONT, anchor="w").grid(
            row=11, column=0, columnspan=3, sticky="w", pady=(0, 6)
        )

        # Remote File Path
        tk.Label(transfer_frame, text="Remote File Path", bg=self.FRAME_BG, fg=self.LABEL_COLOR, font=self.LABEL_FONT, anchor="w").grid(
            row=12, column=0, sticky="w", pady=(0, 4)
        )
        self.remote_file_entry = tk.Entry(transfer_frame, font=self.ENTRY_FONT, bg=self.ENTRY_BG, fg=self.TEXT_COLOR, relief="flat", bd=0,
                                 highlightthickness=1, highlightbackground=self.BORDER_COLOR, highlightcolor=self.PRIMARY_COLOR,
                                 insertbackground=self.PRIMARY_COLOR)
        self.remote_file_entry.grid(row=13, column=0, columnspan=2, sticky="ew", pady=(0, 10), ipady=6)
        browse_remote_file_button = tk.Button(transfer_frame, text="...", command=self.browse_remote_file, bg=self.ENTRY_BG, fg=self.LABEL_COLOR,
                                         font=self.BUTTON_FONT, relief="flat", bd=0, cursor="hand2",
                                         activebackground=self.BORDER_COLOR, activeforeground=self.TEXT_COLOR, padx=12)
        browse_remote_file_button.grid(row=13, column=2, padx=(6, 0), pady=(0, 10))

        # Local Destination Path
        tk.Label(transfer_frame, text="Local Destination Path", bg=self.FRAME_BG, fg=self.LABEL_COLOR, font=self.LABEL_FONT, anchor="w").grid(
            row=14, column=0, sticky="w", pady=(0, 4)
        )
        self.local_path_entry = tk.Entry(transfer_frame, font=self.ENTRY_FONT, bg=self.ENTRY_BG, fg=self.TEXT_COLOR, relief="flat", bd=0,
                               highlightthickness=1, highlightbackground=self.BORDER_COLOR, highlightcolor=self.PRIMARY_COLOR,
                               insertbackground=self.PRIMARY_COLOR)
        self.local_path_entry.grid(row=15, column=0, columnspan=2, sticky="ew", pady=(0, 8), ipady=6)
        browse_local_button = tk.Button(transfer_frame, text="...", command=self.browse_local_path, bg=self.ENTRY_BG, fg=self.LABEL_COLOR,
                                   font=self.BUTTON_FONT, relief="flat", bd=0, cursor="hand2",
                                   activebackground=self.BORDER_COLOR, activeforeground=self.TEXT_COLOR, padx=12)
        browse_local_button.grid(row=15, column=2, padx=(6, 0), pady=(0, 8))

        download_button = tk.Button(transfer_frame, text="Start Download", command=self.download_file,
                               bg=self.SUCCESS_COLOR, fg=self.BG_COLOR, activebackground="#00e67a",
                               activeforeground=self.BG_COLOR, **self.button_style)
        download_button.grid(row=16, column=0, columnspan=3, sticky="ew", pady=(0, 5), ipady=0)

        self.download_status_label = tk.Label(transfer_frame, text="", bg=self.FRAME_BG, fg=self.LABEL_COLOR, font=self.LABEL_FONT)
        self.download_status_label.grid(row=17, column=0, columnspan=3, pady=(0, 6))

        self.download_progress = ttk.Progressbar(transfer_frame, orient="horizontal", mode="determinate", length=300)
        self.download_progress.grid(row=18, column=0, columnspan=3, pady=(0, 6), sticky="ew")

        self.download_live_file_label = tk.Label(transfer_frame, text="", bg=self.FRAME_BG, fg=self.TEXT_COLOR,
                                       font=("SF Mono", 8) if platform.system() == "Darwin" else ("Consolas", 8),
                                       wraplength=280)
        self.download_live_file_label.grid(row=19, column=0, columnspan=3, pady=(0, 4))

        stats_frame_download = tk.Frame(transfer_frame, bg=self.FRAME_BG)
        stats_frame_download.grid(row=20, column=0, columnspan=3, sticky="ew")
        stats_frame_download.grid_columnconfigure(0, weight=1)
        stats_frame_download.grid_columnconfigure(1, weight=1)

        self.download_speed_label = tk.Label(stats_frame_download, text="", bg=self.FRAME_BG, fg=self.LABEL_COLOR,
                                   font=("SF Mono", 8) if platform.system() == "Darwin" else ("Consolas", 8))
        self.download_speed_label.grid(row=0, column=0, sticky="w")
        self.download_eta_label = tk.Label(stats_frame_download, text="", bg=self.FRAME_BG, fg=self.LABEL_COLOR,
                                 font=("SF Mono", 8) if platform.system() == "Darwin" else ("Consolas", 8))
        self.download_eta_label.grid(row=0, column=1, sticky="e")

        # Hide download widgets initially
        self.download_progress.grid_remove()
        self.download_live_file_label.grid_remove()
        stats_frame_download.grid_remove()

        transfer_frame.grid_columnconfigure(0, weight=1)

    # Event handlers
    def test_connection(self):
        """Test SSH connection."""
        success, message = test_ssh_connection(
            self.username_entry.get(),
            self.ip_entry.get(),
            self.key_file_entry.get(),
            self.port_entry.get()
        )
        if success:
            messagebox.showinfo("Connection Test", message)
        else:
            messagebox.showerror("Connection Test", message)

    def check_disk_space(self):
        """Check remote disk space."""
        success, message, color = check_remote_disk_space(
            self.username_entry.get(),
            self.ip_entry.get(),
            self.key_file_entry.get(),
            self.port_entry.get()
        )
        self.disk_space_label.config(text=message, fg=color)
        if not success and "Please fill" not in message:
            messagebox.showerror("Error", message)

    def connect_to_instance(self):
        """Connect to SSH instance via terminal."""
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()
        terminal = self.terminal_var.get()

        if username and ip_address and key_path and port and terminal:
            save_config(username, ip_address, key_path, port)
            thread = threading.Thread(target=open_ssh_terminal, args=(key_path, username, ip_address, port, terminal))
            thread.start()
        else:
            messagebox.showerror("Error", "Please fill in all fields and select a terminal")

    def download_file(self):
        """Start file download from remote server."""
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()
        remote_path = self.remote_file_entry.get()
        local_path = self.local_path_entry.get()

        if username and ip_address and key_path and port and remote_path and local_path:
            self.download_progress.grid()
            self.download_progress["value"] = 0
            self.download_live_file_label.grid()
            self.download_speed_label.grid()
            self.download_eta_label.grid()
            self.download_status_label.config(text="Downloading...")

            thread = threading.Thread(
                target=run_rsync_command,
                args=(
                    key_path, username, ip_address, port, remote_path, local_path,
                    "download", self.download_status_label, self.download_progress,
                    self.download_live_file_label, self.download_speed_label, self.download_eta_label,
                ),
            )
            thread.start()
        else:
            messagebox.showerror("Error", "Please fill in all fields for downloading")

    def upload_file(self):
        """Start file upload to remote server."""
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()
        local_path = self.local_file_entry.get()
        remote_path = self.remote_path_upload_entry.get()

        if username and ip_address and key_path and port and local_path and remote_path:
            self.upload_progress.grid()
            self.upload_progress["value"] = 0
            self.upload_live_file_label.grid()
            self.upload_speed_label.grid()
            self.upload_eta_label.grid()
            self.upload_status_label.config(text="Uploading...")

            thread = threading.Thread(
                target=run_rsync_command,
                args=(
                    key_path, username, ip_address, port, local_path, remote_path,
                    "upload", self.upload_status_label, self.upload_progress,
                    self.upload_live_file_label, self.upload_speed_label, self.upload_eta_label,
                ),
            )
            thread.start()
        else:
            messagebox.showerror("Error", "Please fill in all fields for uploading")

    def browse_key_file(self):
        """Open file dialog to select SSH key."""
        home_dir = os.path.expanduser("~")
        ssh_dir = os.path.join(home_dir, ".ssh")
        initial_dir = ssh_dir if os.path.exists(ssh_dir) else home_dir

        key_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select SSH Key",
            filetypes=(("PEM files", "*.pem"), ("All files", "*.*")),
        )
        if key_path:
            self.key_file_entry.delete(0, tk.END)
            self.key_file_entry.insert(0, key_path)

    def browse_local_path(self):
        """Open directory dialog to select local destination."""
        local_path = filedialog.askdirectory(title="Select Local Destination")
        if local_path:
            self.local_path_entry.delete(0, tk.END)
            self.local_path_entry.insert(0, local_path)

    def browse_local_file(self):
        """Show dropdown to select file or directory for upload."""
        self.browse_local_file_button.grid_remove()
        options = ["Select File", "Select Directory"]
        selected_option = tk.StringVar(self.root)
        selected_option.set("Select")
        dropdown = tk.OptionMenu(self.root, selected_option, *options, command=self.handle_local_selection)
        dropdown.grid(row=2, column=2, padx=(6, 0), pady=(0, 10))

    def handle_local_selection(self, selection):
        """Handle file/directory selection from dropdown."""
        if selection == "Select File":
            self.select_file()
        elif selection == "Select Directory":
            self.select_directory()
        self.restore_browse_button()

    def restore_browse_button(self):
        """Restore the browse button after selection."""
        self.browse_local_file_button.grid()

    def select_file(self):
        """Open file dialog to select a single file."""
        local_path = filedialog.askopenfilename(title="Select File to Upload")
        if local_path:
            self.local_file_entry.delete(0, tk.END)
            self.local_file_entry.insert(0, local_path)

    def select_directory(self):
        """Open directory dialog to select a directory."""
        local_directory = filedialog.askdirectory(title="Select Directory to Upload")
        if local_directory:
            self.local_file_entry.delete(0, tk.END)
            self.local_file_entry.insert(0, local_directory)

    def browse_remote_file(self):
        """Open remote file browser to select remote file."""
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()

        if username and ip_address and key_path and port:
            ssh_command = f"ssh -i {key_path} -p {port} {username}@{ip_address}"
            remote_browser_window = tk.Toplevel(self.root)
            remote_browser_window.title("Select Remote File")

            def on_select(path):
                self.remote_file_entry.delete(0, tk.END)
                self.remote_file_entry.insert(0, path)

            RemoteFileBrowser(remote_browser_window, ssh_command, on_select)
        else:
            messagebox.showerror("Error", "Please fill in all connection fields")

    def browse_remote_path(self):
        """Open remote file browser to select remote path."""
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()

        if username and ip_address and key_path and port:
            ssh_command = f"ssh -i {key_path} -p {port} {username}@{ip_address}"
            remote_browser_window = tk.Toplevel(self.root)
            remote_browser_window.title("Select Remote Path")

            def on_select(path):
                self.remote_path_upload_entry.delete(0, tk.END)
                self.remote_path_upload_entry.insert(0, path)

            RemoteFileBrowser(remote_browser_window, ssh_command, on_select)
        else:
            messagebox.showerror("Error", "Please fill in all connection fields")

    def load_config_file(self):
        """Open file dialog to load a saved configuration."""
        file_path = filedialog.askopenfilename(
            title="Select Configuration File",
            initialdir=CONFIG_DIR,
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        )
        if file_path:
            config = load_config(file_path)
            if config:
                self.username_entry.delete(0, tk.END)
                self.username_entry.insert(0, config.get("username", ""))
                self.ip_entry.delete(0, tk.END)
                self.ip_entry.insert(0, config.get("ip_address", ""))
                self.key_file_entry.delete(0, tk.END)
                self.key_file_entry.insert(0, config.get("key_path", ""))
                self.port_entry.delete(0, tk.END)
                self.port_entry.insert(0, config.get("port", "22"))

    def load_last_config(self):
        """Load the most recently used configuration."""
        config = load_last_used_config()
        if config:
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, config.get("username", ""))
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, config.get("ip_address", ""))
            self.key_file_entry.delete(0, tk.END)
            self.key_file_entry.insert(0, config.get("key_path", ""))
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, config.get("port", "22"))

    def apply_window_focus_fix(self):
        """Apply platform-specific window focus fix for macOS and Linux."""
        if platform.system() in ["Darwin", "Linux"]:
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after(100, lambda: self.root.attributes('-topmost', False))
            self.root.focus_force()
