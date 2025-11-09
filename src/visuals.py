"""
SSH GUI - Visuals Module

This module contains all the GUI components and visual elements for the SSH GUI application.
Handles window creation, widget layout, styling, and user interface components.
"""

import logging
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

# Get logger from functionality module
logger = logging.getLogger(__name__)


class SSHGuiApp:
    """Main SSH GUI Application class containing all visual elements and event handlers."""

    def __init__(self, root):
        """
        Initialize the SSH GUI application.

        Args:
            root: The Tkinter root window
        """
        logger.info("=" * 80)
        logger.info("SSH GUI Application window initializing")

        self.root = root
        self.root.title("SSH Connect Pro")

        # Window dimensions
        self.window_width = 700
        self.window_height = 480
        logger.debug(f"Window dimensions: {self.window_width}x{self.window_height}")

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

        # Store references to active transfer processes
        self.upload_process = None
        self.download_process = None

        # Create GUI components
        logger.info("Creating GUI components...")
        self.create_connection_frame()
        self.create_transfer_frame()
        logger.info("GUI components created successfully")

        # Load last used configuration
        self.load_last_config()

        logger.info("SSH GUI Application window fully initialized and ready")
        logger.info("=" * 80)

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

        # Cancel upload button (hidden by default)
        self.cancel_upload_button = tk.Button(transfer_frame, text="Cancel Upload", command=self.cancel_upload,
                                         bg=self.DANGER_COLOR, fg=self.BG_COLOR, activebackground="#cc0044",
                                         activeforeground=self.BG_COLOR, **self.button_style)
        self.cancel_upload_button.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 8), ipady=0)
        self.cancel_upload_button.grid_remove()  # Hidden by default

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

        # Cancel download button (hidden by default)
        self.cancel_download_button = tk.Button(transfer_frame, text="Cancel Download", command=self.cancel_download,
                                           bg=self.DANGER_COLOR, fg=self.BG_COLOR, activebackground="#cc0044",
                                           activeforeground=self.BG_COLOR, **self.button_style)
        self.cancel_download_button.grid(row=16, column=0, columnspan=3, sticky="ew", pady=(0, 5), ipady=0)
        self.cancel_download_button.grid_remove()  # Hidden by default

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
        logger.info("=" * 60)
        logger.info("TEST CONNECTION button pressed")
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()
        logger.info(f"Parameters: username={username}, ip={ip_address}, port={port}")
        logger.debug(f"Key path: {key_path}")

        success, message = test_ssh_connection(username, ip_address, key_path, port)

        if success:
            logger.info(f"Connection test successful: {message}")
            messagebox.showinfo("Connection Test", message)
        else:
            logger.error(f"Connection test failed: {message}")
            messagebox.showerror("Connection Test", message)
        logger.info("=" * 60)

    def check_disk_space(self):
        """Check remote disk space."""
        logger.info("=" * 60)
        logger.info("CHECK DISK SPACE button pressed")
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()
        logger.info(f"Parameters: username={username}, ip={ip_address}, port={port}")
        logger.debug(f"Key path: {key_path}")

        success, message, color = check_remote_disk_space(username, ip_address, key_path, port)

        self.disk_space_label.config(text=message, fg=color)
        if success:
            logger.info(f"Disk space check successful: {message}")
        else:
            logger.error(f"Disk space check failed: {message}")
            if "Please fill" not in message:
                messagebox.showerror("Error", message)
        logger.info("=" * 60)

    def connect_to_instance(self):
        """Connect to SSH instance via terminal."""
        logger.info("=" * 60)
        logger.info("CONNECT button pressed")
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()
        terminal = self.terminal_var.get()
        logger.info(f"Parameters: username={username}, ip={ip_address}, port={port}, terminal={terminal}")
        logger.debug(f"Key path: {key_path}")

        if username and ip_address and key_path and port and terminal:
            logger.info("All fields filled, saving config and opening terminal")
            save_config(username, ip_address, key_path, port)
            thread = threading.Thread(target=open_ssh_terminal, args=(key_path, username, ip_address, port, terminal))
            thread.start()
            logger.info("Terminal thread started")
        else:
            logger.warning("Missing required fields for connection")
            messagebox.showerror("Error", "Please fill in all fields and select a terminal")
        logger.info("=" * 60)

    def download_file(self):
        """Start file download from remote server."""
        logger.info("=" * 60)
        logger.info("START DOWNLOAD button pressed")
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()
        remote_path = self.remote_file_entry.get()
        local_path = self.local_path_entry.get()
        logger.info(f"Download parameters: username={username}, ip={ip_address}, port={port}")
        logger.info(f"Remote path: {remote_path}")
        logger.info(f"Local destination: {local_path}")
        logger.debug(f"Key path: {key_path}")

        if username and ip_address and key_path and port and remote_path and local_path:
            logger.info("All fields filled, starting download in background thread")
            self.download_progress.grid()
            self.download_progress["value"] = 0
            self.download_live_file_label.grid()
            self.download_speed_label.grid()
            self.download_eta_label.grid()
            self.download_status_label.config(text="Downloading...")

            # Show cancel button
            self.cancel_download_button.grid()

            def store_download_process(process):
                """Callback to store the download process reference."""
                self.download_process = process
                logger.debug(f"Download process stored: PID {process.pid}")

            def hide_download_cancel(return_code):
                """Callback to hide cancel button and reset UI when transfer completes."""
                self.cancel_download_button.grid_remove()
                self.download_process = None
                logger.debug(f"Download cancel button hidden (exit code: {return_code})")

                # If cancelled (exit code 20, 15, or negative), reset UI to initial state
                if return_code == 20 or return_code == 15 or return_code < 0:
                    logger.debug("Resetting download UI to initial state after cancellation")
                    self.download_progress.grid_remove()
                    self.download_progress["value"] = 0
                    self.download_live_file_label.grid_remove()
                    self.download_live_file_label.config(text="")
                    self.download_speed_label.grid_remove()
                    self.download_speed_label.config(text="")
                    self.download_eta_label.grid_remove()
                    self.download_eta_label.config(text="")
                    self.download_status_label.config(text="")

            thread = threading.Thread(
                target=run_rsync_command,
                args=(
                    key_path, username, ip_address, port, remote_path, local_path,
                    "download", self.download_status_label, self.download_progress,
                    self.download_live_file_label, self.download_speed_label, self.download_eta_label,
                ),
                kwargs={
                    "cancel_callback": store_download_process,
                    "completion_callback": hide_download_cancel
                }
            )
            thread.start()
            logger.info("Download thread started")
        else:
            logger.warning("Missing required fields for download")
            messagebox.showerror("Error", "Please fill in all fields for downloading")
        logger.info("=" * 60)

    def upload_file(self):
        """Start file upload to remote server."""
        logger.info("=" * 60)
        logger.info("START UPLOAD button pressed")
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()
        local_path = self.local_file_entry.get()
        remote_path = self.remote_path_upload_entry.get()
        logger.info(f"Upload parameters: username={username}, ip={ip_address}, port={port}")
        logger.info(f"Local source: {local_path}")
        logger.info(f"Remote destination: {remote_path}")
        logger.debug(f"Key path: {key_path}")

        if username and ip_address and key_path and port and local_path and remote_path:
            logger.info("All fields filled, starting upload in background thread")
            self.upload_progress.grid()
            self.upload_progress["value"] = 0
            self.upload_live_file_label.grid()
            self.upload_speed_label.grid()
            self.upload_eta_label.grid()
            self.upload_status_label.config(text="Uploading...")

            # Show cancel button
            self.cancel_upload_button.grid()

            def store_upload_process(process):
                """Callback to store the upload process reference."""
                self.upload_process = process
                logger.debug(f"Upload process stored: PID {process.pid}")

            def hide_upload_cancel(return_code):
                """Callback to hide cancel button and reset UI when transfer completes."""
                self.cancel_upload_button.grid_remove()
                self.upload_process = None
                logger.debug(f"Upload cancel button hidden (exit code: {return_code})")

                # If cancelled (exit code 20, 15, or negative), reset UI to initial state
                if return_code == 20 or return_code == 15 or return_code < 0:
                    logger.debug("Resetting upload UI to initial state after cancellation")
                    self.upload_progress.grid_remove()
                    self.upload_progress["value"] = 0
                    self.upload_live_file_label.grid_remove()
                    self.upload_live_file_label.config(text="")
                    self.upload_speed_label.grid_remove()
                    self.upload_speed_label.config(text="")
                    self.upload_eta_label.grid_remove()
                    self.upload_eta_label.config(text="")
                    self.upload_status_label.config(text="")

            thread = threading.Thread(
                target=run_rsync_command,
                args=(
                    key_path, username, ip_address, port, local_path, remote_path,
                    "upload", self.upload_status_label, self.upload_progress,
                    self.upload_live_file_label, self.upload_speed_label, self.upload_eta_label,
                ),
                kwargs={
                    "cancel_callback": store_upload_process,
                    "completion_callback": hide_upload_cancel
                }
            )
            thread.start()
            logger.info("Upload thread started")
        else:
            logger.warning("Missing required fields for upload")
            messagebox.showerror("Error", "Please fill in all fields for uploading")
        logger.info("=" * 60)

    def browse_key_file(self):
        """Open file dialog to select SSH key."""
        logger.debug("Browse key file button pressed")
        home_dir = os.path.expanduser("~")
        ssh_dir = os.path.join(home_dir, ".ssh")
        initial_dir = ssh_dir if os.path.exists(ssh_dir) else home_dir

        key_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select SSH Key",
            filetypes=(("PEM files", "*.pem"), ("All files", "*.*")),
        )
        if key_path:
            logger.info(f"Key file selected: {key_path}")
            self.key_file_entry.delete(0, tk.END)
            self.key_file_entry.insert(0, key_path)
        else:
            logger.debug("Key file selection cancelled")

    def browse_local_path(self):
        """Open directory dialog to select local destination."""
        logger.debug("Browse local path button pressed")
        local_path = filedialog.askdirectory(title="Select Local Destination")
        if local_path:
            logger.info(f"Local destination selected: {local_path}")
            self.local_path_entry.delete(0, tk.END)
            self.local_path_entry.insert(0, local_path)
        else:
            logger.debug("Local path selection cancelled")

    def browse_local_file(self):
        """Show dropdown menu to select file or directory for upload."""
        logger.debug("Browse local file button pressed - showing menu")
        # Create a styled popup menu that matches the GUI design
        menu = tk.Menu(self.root, tearoff=0,
                      bg=self.ENTRY_BG,
                      fg=self.TEXT_COLOR,
                      activebackground=self.PRIMARY_COLOR,
                      activeforeground=self.BG_COLOR,
                      font=self.BUTTON_FONT,
                      relief="flat",
                      bd=1)

        menu.add_command(label="Select File", command=self.select_file)
        menu.add_command(label="Select Directory", command=self.select_directory)

        # Get the button's position on screen to place the menu directly below it
        x = self.browse_local_file_button.winfo_rootx()
        y = self.browse_local_file_button.winfo_rooty() + self.browse_local_file_button.winfo_height()

        # Display the menu at the button's location
        menu.post(x, y)

    def select_file(self):
        """Open file dialog to select a single file."""
        logger.debug("Select file option chosen")
        local_path = filedialog.askopenfilename(title="Select File to Upload")
        if local_path:
            logger.info(f"File selected for upload: {local_path}")
            self.local_file_entry.delete(0, tk.END)
            self.local_file_entry.insert(0, local_path)
        else:
            logger.debug("File selection cancelled")

    def select_directory(self):
        """Open directory dialog to select a directory."""
        logger.debug("Select directory option chosen")
        local_directory = filedialog.askdirectory(title="Select Directory to Upload")
        if local_directory:
            logger.info(f"Directory selected for upload: {local_directory}")
            self.local_file_entry.delete(0, tk.END)
            self.local_file_entry.insert(0, local_directory)
        else:
            logger.debug("Directory selection cancelled")

    def browse_remote_file(self):
        """Open remote file browser to select remote file."""
        logger.debug("Browse remote file button pressed")
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()

        if username and ip_address and key_path and port:
            logger.info(f"Opening remote file browser for {username}@{ip_address}:{port}")
            ssh_command = f"ssh -i {key_path} -p {port} {username}@{ip_address}"
            remote_browser_window = tk.Toplevel(self.root)
            remote_browser_window.title("Select Remote File")

            def on_select(path):
                logger.info(f"Remote file selected: {path}")
                self.remote_file_entry.delete(0, tk.END)
                self.remote_file_entry.insert(0, path)

            RemoteFileBrowser(remote_browser_window, ssh_command, on_select)
        else:
            logger.warning("Cannot open remote browser - missing connection fields")
            messagebox.showerror("Error", "Please fill in all connection fields")

    def browse_remote_path(self):
        """Open remote file browser to select remote path."""
        logger.debug("Browse remote path button pressed")
        username = self.username_entry.get()
        ip_address = self.ip_entry.get()
        key_path = self.key_file_entry.get()
        port = self.port_entry.get()

        if username and ip_address and key_path and port:
            logger.info(f"Opening remote path browser for {username}@{ip_address}:{port}")
            ssh_command = f"ssh -i {key_path} -p {port} {username}@{ip_address}"
            remote_browser_window = tk.Toplevel(self.root)
            remote_browser_window.title("Select Remote Path")

            def on_select(path):
                logger.info(f"Remote path selected: {path}")
                self.remote_path_upload_entry.delete(0, tk.END)
                self.remote_path_upload_entry.insert(0, path)

            RemoteFileBrowser(remote_browser_window, ssh_command, on_select)
        else:
            logger.warning("Cannot open remote browser - missing connection fields")
            messagebox.showerror("Error", "Please fill in all connection fields")

    def load_config_file(self):
        """Open file dialog to load a saved configuration."""
        logger.debug("Load config button pressed")
        file_path = filedialog.askopenfilename(
            title="Select Configuration File",
            initialdir=CONFIG_DIR,
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        )
        if file_path:
            logger.info(f"Loading configuration from: {file_path}")
            config = load_config(file_path)
            if config:
                logger.info(f"Configuration loaded successfully: username={config.get('username')}, ip={config.get('ip_address')}, port={config.get('port')}")
                self.username_entry.delete(0, tk.END)
                self.username_entry.insert(0, config.get("username", ""))
                self.ip_entry.delete(0, tk.END)
                self.ip_entry.insert(0, config.get("ip_address", ""))
                self.key_file_entry.delete(0, tk.END)
                self.key_file_entry.insert(0, config.get("key_path", ""))
                self.port_entry.delete(0, tk.END)
                self.port_entry.insert(0, config.get("port", "22"))
            else:
                logger.error(f"Failed to load configuration from {file_path}")
        else:
            logger.debug("Config file selection cancelled")

    def load_last_config(self):
        """Load the most recently used configuration."""
        logger.debug("Loading last used configuration")
        config = load_last_used_config()
        if config:
            logger.info(f"Last config loaded: username={config.get('username')}, ip={config.get('ip_address')}, port={config.get('port')}")
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, config.get("username", ""))
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, config.get("ip_address", ""))
            self.key_file_entry.delete(0, tk.END)
            self.key_file_entry.insert(0, config.get("key_path", ""))
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, config.get("port", "22"))
        else:
            logger.debug("No previous configuration found")

    def cancel_download(self):
        """Cancel the ongoing download operation."""
        logger.info("=" * 60)
        logger.info("CANCEL DOWNLOAD button pressed")

        if self.download_process:
            logger.info(f"Terminating download process (PID: {self.download_process.pid})")
            try:
                self.download_process.terminate()
                logger.info("Download process terminated successfully")

                # Immediately reset UI to initial state
                self.download_status_label.config(text="Download Cancelled")
                self.cancel_download_button.grid_remove()

            except Exception as e:
                logger.error(f"Error terminating download process: {e}")
        else:
            logger.warning("No active download process to cancel")

        logger.info("=" * 60)

    def cancel_upload(self):
        """Cancel the ongoing upload operation."""
        logger.info("=" * 60)
        logger.info("CANCEL UPLOAD button pressed")

        if self.upload_process:
            logger.info(f"Terminating upload process (PID: {self.upload_process.pid})")
            try:
                self.upload_process.terminate()
                logger.info("Upload process terminated successfully")

                # Immediately reset UI to initial state
                self.upload_status_label.config(text="Upload Cancelled")
                self.cancel_upload_button.grid_remove()

            except Exception as e:
                logger.error(f"Error terminating upload process: {e}")
        else:
            logger.warning("No active upload process to cancel")

        logger.info("=" * 60)
