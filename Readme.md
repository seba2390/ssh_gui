# SSH GUI Tool

A professional graphical user interface (GUI) application for managing SSH connections and file transfers. Built with **native Python** using Tkinter, this tool provides an intuitive interface for SSH operations without requiring external dependencies beyond the standard Python installation.

## Features

- **🔐 SSH Connection Management**: Securely connect to remote servers with SSH key authentication
- **📁 Remote File Browser**: Built-in GUI browser to explore remote directories over SSH
- **⬇️ File Downloads**: Efficient file transfers from remote servers using rsync
- **⬆️ File Uploads**: Upload files and directories to remote servers with progress tracking
- **💾 Configuration Management**: Save and load SSH connection settings for quick access
- **📊 Disk Space Monitoring**: Check available disk space on remote servers
- **🖥️ Multi-Terminal Support**: Launch SSH sessions in your preferred terminal (Standard, Warp on macOS)
- **⚡ Real-time Progress**: Live transfer speed, ETA, and progress visualization

## Project Structure

```
ssh_gui/
├── ssh_gui.py              # Main entry point
├── src/
│   ├── __init__.py
│   ├── functionality.py    # Business logic and SSH operations
│   ├── visuals.py          # GUI components and styling
│   ├── remote_file_browser.py  # Remote filesystem browser
│   └── run_in_warp.sh      # Warp terminal launcher (macOS)
├── configurations/         # Saved SSH configurations
├── requirements.txt        # Python dependencies
├── Readme.md              # This file
└── LICENSE                # MIT License

```

## Prerequisites

- **Python 3.7+** with Tkinter (pre-installed with Python)
- **SSH client** (OpenSSH recommended)
- **rsync** for file transfers
- **(Optional)** [Warp Terminal](https://www.warp.dev/) for enhanced macOS terminal experience

### Installing Warp (macOS only)

```bash
# Via Homebrew
brew install --cask warp

# Or download from https://app.warp.dev/get_warp?package=dmg
```

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/seba2390/ssh_gui.git
   cd ssh_gui
   ```

2. **Make Warp Script Executable** (Optional, macOS only)

   ```bash
   chmod +x src/run_in_warp.sh
   ```

   Note: Allow system access on first run and restart the GUI if needed.

## Usage

### Running the Application

From the repository directory:

```bash
python ssh_gui.py
```

The application window displays two main sections:

#### 1. Connection Panel (Left)
- **Username**: SSH username for authentication
- **IP Address**: Target server IP or hostname
- **Port**: SSH port (default: 22)
- **SSH Key File**: Path to your private SSH key
- **Load Config**: Load saved connection settings
- **Terminal**: Choose terminal type (Standard/Warp)
- **Connect**: Launch SSH terminal session
- **Test Connection**: Verify SSH credentials
- **Check Disk Space**: Display remote server disk usage

#### 2. File Transfer Panel (Right)

**Upload Section:**
- **Local File Path**: Select local file or directory to upload
- **Remote Destination Path**: Target path on remote server
- **Start Upload**: Initiate upload with progress tracking

**Download Section:**
- **Remote File Path**: Path to file/directory on remote server
- **Local Destination Path**: Local save location
- **Start Download**: Begin download with real-time progress

### Configuration Management

**Saving Configurations:**
- Configurations are automatically saved when you connect to a server
- Saved to `configurations/` directory as `config_1.json`, `config_2.json`, etc.
- Duplicate configurations are automatically prevented

**Loading Configurations:**
1. Click "Load Config" button
2. Select a JSON file from the file dialog
3. Connection fields will be automatically populated
4. The most recent configuration is loaded on startup

### Remote File Browser

Navigate remote filesystems visually:

1. Click the "..." button next to any remote path field
2. Browse directories using the tree view
3. Use ← and → buttons for navigation
4. Double-click folders to enter them
5. Select files/folders and click "Select"

### File Transfer Progress

Real-time monitoring includes:
- **Progress bar**: Visual completion indicator
- **Speed**: Current transfer rate (KB/s, MB/s, GB/s)
- **ETA**: Estimated time to completion
- **Status**: Current operation and percentage
- **Filename**: Currently transferring file (for multi-file operations)

## Creating a macOS Application

On macOS, create a clickable app icon:

1. Open **Automator**
2. File → New → Application
3. Search for "Run Shell Script" in Actions
4. Add this script:
   ```bash
   /usr/bin/python3 /full/path/to/ssh_gui/ssh_gui.py
   ```
   Replace `/full/path/to/ssh_gui/` with your actual path (find with `pwd` in the repo directory)
5. File → Save (⌘S) and name it "SSH GUI"
6. Drag to Dock or Applications folder

**Tip**: Find your Python path with `which python3` in Terminal.

## Technical Details

### Architecture

- **ssh_gui.py**: Application entry point and initialization
- **functionality.py**: Core SSH operations, rsync, configuration management
- **visuals.py**: Tkinter GUI components, styling, event handlers
- **remote_file_browser.py**: SSH-based file system browser implementation

### SSH Security

- Uses key-based authentication (password auth not supported)
- StrictHostKeyChecking disabled for convenience (use in controlled environments)
- Keep-alive enabled (60s interval, 2 max retries)

### File Transfer Details

- Uses rsync for efficient incremental transfers
- Compression enabled (`-z` flag)
- Archive mode preserves permissions and timestamps (`-a` flag)
- Progress tracking (`-P` flag)
- Works with both files and directories

### Platform Support

- **macOS**: Full support including Warp terminal
- **Linux**: Standard terminal support
- **Windows**: Limited support (SSH client required)

## Troubleshooting

**Connection fails:**
- Verify SSH key permissions: `chmod 600 ~/.ssh/your_key`
- Test manual SSH: `ssh -i ~/.ssh/your_key user@host`
- Check firewall settings and network connectivity

**Warp terminal doesn't open (macOS):**
- Ensure script is executable: `chmod +x src/run_in_warp.sh`
- Grant Automator permissions in System Preferences → Security & Privacy
- Restart the application after first-time permission grant

**Transfer fails:**
- Ensure rsync is installed on both local and remote systems
- Check file path permissions
- Verify sufficient disk space on destination

**Window unresponsive on startup (macOS/Linux):**
- This should be fixed automatically with built-in window focus handling
- If issues persist, try moving the window slightly

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Python's native Tkinter for zero external dependencies
- Uses rsync for efficient file transfers
- Inspired by the need for a simple, portable SSH GUI tool

## Version History

- **v2.0** - Complete refactor with modular architecture, enhanced documentation
- **v1.0** - Initial release with basic SSH and file transfer capabilities

## Author

**SSH GUI Team**
Repository: [github.com/seba2390/ssh_gui](https://github.com/seba2390/ssh_gui)
