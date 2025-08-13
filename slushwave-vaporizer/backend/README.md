# Slushwave Vaporizer - Backend

This is the backend for the Slushwave Vaporizer application.

## System Requirements

- Python 3.10+
- **SoX (Sound eXchange):** This application depends on the SoX command-line tool for all audio processing via the `pysndfx` library. You **must** have SoX installed on your system for this backend to function.
  - On Debian/Ubuntu, you can install it and the required MP3 format library with:
    ```bash
    sudo apt-get update
    sudo apt-get install sox libsox-fmt-mp3
    ```
- The Python dependencies listed in `requirements.txt`.

## Setup

1. Install the system requirements listed above.
2. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask application:
   ```bash
   python app.py
   ```
