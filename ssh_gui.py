"""
SSH GUI - Main Entry Point

A professional SSH connection manager with file transfer capabilities.
Provides a modern GUI for managing SSH connections, uploading/downloading files,
and monitoring remote server disk space.

Author: SSH GUI Team
Version: 2.0
"""

from sys import platform
import tkinter as tk
from src.visuals import SSHGuiApp


def main():
    """
    Main entry point for the SSH GUI application.
    Creates the root window and initializes the application.
    """
    root = tk.Tk()
    _app = SSHGuiApp(root)

    # Fix for macOS and Linux: Force window to front and give it focus
    if platform in ["darwin", "linux"]:
        root.lift()
        root.focus_force()
        # Update idle tasks to ensure proper window initialization
        root.update_idletasks()
    else:
        raise NotImplementedError(
            f"This application currently supports only macOS and Linux platforms. Detected: {platform}"
        )

    root.mainloop()

if __name__ == "__main__":
    main()
