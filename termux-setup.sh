#!/data/data/com.termux/files/usr/bin/bash
# ZYROX Code Encryptor - Termux setup (one command)
set -e
pkg update -y && pkg install python nodejs git -y
echo "ZYROX ready 😈  Usage: python zyrox_encrypt.py file.py -o file_enc.py"
python3 --version; node --version || true
