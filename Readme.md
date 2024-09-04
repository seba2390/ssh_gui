# SSH GUI Tool

A graphical user interface (GUI) application for managing SSH connections and file transfers using Python and Tkinter. This tool allows users to connect to remote SSH instances, download files from, and upload files to those instances.

## Features

- **Connect to Remote SSH Instances**: Input SSH credentials and open a new terminal window to start an SSH session.
- **Download Files**: Retrieve files from a remote server to a local destination.
- **Upload Files**: Transfer files from a local system to a remote server.
- **Configuration Management**: Save and load SSH connection settings for convenience.

## Prerequisites

- Python 3.x
- Tkinter (comes pre-installed with Python)
- SSH client (such as OpenSSH)

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/ssh_gui.git
## Usage

1. **Running the application**
    ```bash
    python ssh_gui.py
The application window will display three sections:

- **Connect to instance**: Enter the SSH username, IP address, and path to the SSH key file. Click "Connect" to initiate an SSH session.
- **Download from instance**:  Provide the remote file path and local destination path. Click "Download" to transfer the file from the remote server to your local machine.
- **Upload to instance**:  Provide the local file path and remote destination path. Click "Upload" to transfer the file from your local machine to the remote server.

**N.B** Use the "Browse" buttons next to the file path fields to select files and directories via file dialogs.

## Notes
The application saves the SSH connection settings in a file named config.json. This file is used to retain the last entered SSH credentials and key path.

The application currently supports macOS and Linux. If you're using a different operating system, you'll see an error message indicating unsupported OS.