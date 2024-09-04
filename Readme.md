# SSH GUI Tool

A graphical user interface (GUI) application written in **native Python** using Tkinter for managing SSH connections and file transfers. This tool allows users to connect to remote SSH instances, download files from, and upload files to those instances, all without needing external libraries beyond the standard Python installation.

## Features

- **Connect to Remote SSH Instances**: Input SSH credentials and open a new terminal window to start an SSH session.
- **Remote File Browser**: A built-in GUI browser to explore remote directories over SSH. Easily navigate directories, view files, and select files or directories for download/upload.
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
   git clone https://github.com/seba2390/ssh_gui.git
   ```
## Usage
1. **Running the application**

    move into the repo:
    ```bash
    cd ssh_gui
   ```
    run the python script:
    ```bash
    python ssh_gui.py
   ```
The application window will display three sections:

- **Connect to instance**: Enter the SSH username, IP address, and path to the SSH key file. Click "Connect" to initiate an SSH session.
- **Download from instance**:  Provide the remote file path and local destination path. Click "Download" to transfer the file from the remote server to your local machine.
- **Upload to instance**:  Provide the local file path and remote destination path. Click "Upload" to transfer the file from your local machine to the remote server.

**N.B** Use the "Browse" buttons next to the file path fields to select files and directories via file dialogs.

2. **Configuration management**
- **Loading Configuration**: Use the "Load Config" button in the "Connect to instance" section to open a file dialog and select a JSON configuration file from the configurations folder. The application will load the selected configuration and update the input fields with the saved values.
- **Saving Configuration**: When you connect to an SSH instance, the application saves the configuration to a new file in the configurations folder. If the new configuration differs from the existing default configuration (config.json), it will be saved in a file with an incremental number (e.g., config_1.json, config_2.json, etc.) to avoid overwriting.

3. **Remote File Browser**

- Use the Remote Browser to navigate the file structure of your SSH-connected remote instance.
In both the "Download from instance" and "Upload to instance" sections, you can click the "Browse" button next to the file path fields to open a remote file browser. This allows you to visually navigate directories on the remote server, and select the files or directories to transfer.
## Notes
The application saves the SSH connection settings in a file named config.json. This file is used to retain the last entered SSH credentials and key path.

The application currently supports macOS and Linux. If you're using a different operating system, you'll see an error message indicating unsupported OS.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

