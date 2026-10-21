# ZYROX CODE ENCRYPTOR 😈🔥

**HTML / Python / Node.js code ko encrypt karo — Termux, GitHub, Linux, Windows sab me chalega.**
Ek hi file `zyrox_encrypt.py` — **koi pip install nahi**, sirf Python 3 (stdlib only).

## ⚡ Quick Start

```bash
# Termux
pkg update && pkg install python git -y
git clone <tumhara-repo-url> zyrox-code-encryptor
cd zyrox-code-encryptor

# Linux / GitHub Codespace / Windows me bhi same:
python3 zyrox_encrypt.py --help
```

## 🔥 Usage

```bash
# Python file — AUTO mode (encrypted file khud chalega)
python3 zyrox_encrypt.py app.py -o app_enc.py
python3 app_enc.py

# Python file — PASSWORD mode (STRONG — bina password decrypt impossible)
python3 zyrox_encrypt.py app.py -o app_enc.py -p 'TumharaStrongPassword'
python3 app_enc.py        # run par password puchega

# Node.js file
python3 zyrox_encrypt.py server.js -o server_enc.js
node server_enc.js
# password mode me run:  ZYROX_PASSWORD='xxx' node server_enc.js

# HTML file
python3 zyrox_encrypt.py index.html -o index_enc.html
# browser me kholo — password mode me prompt aayega, auto mode me khud khulega
```

## 🛡️ 2 Mode — Sach Samajh Lo

| Mode | Kaise | Suraksha |
|---|---|---|
| **PASSWORD** (`-p`) | PBKDF2 200,000 rounds + HMAC stream cipher + tamper tag | ✅ **Real encryption.** Bina password koi decrypt nahi kar sakta. Galat password = file band. |
| **AUTO** (bina `-p`) | Random key 2 hisso me baant ke loader me chhupti hai + wahi cipher | ⚠️ **Strong obfuscation + encryption.** Source seedha nahi dikhega, copy-paste wale ruk jayenge — lekin jo code khud *chalna* hai, uski key kahin na kahin loader me hogi hi, isliye expert runtime par nikaal sakta hai. Ye har "code protector" ki sachchai hai. |

**Rule:** Asli secret (API key, license check, paisa wala logic) kabhi client code me mat rakho — password mode ya apne server par rakho.

## ✅ Tested

- Python AUTO — run hua, output sahi, plain source leak = 0
- Python PASSWORD — sahi password chala, galat = `wrong password / file tampered`
- Node AUTO — run hua, plain source leak = 0
- Node PASSWORD — sahi chala, galat = exit 1 + tamper error
- HTML AUTO — WebCrypto decrypt verify, original HTML exact wapas mila
- HTML me original content plain me nahi dikhta

## 📁 Files

- `zyrox_encrypt.py` — pura tool (single file)
- `examples/` — test.py / test.js / test.html
- `termux-setup.sh` — Termux one-command setup

## GitHub par daalna

```bash
git init && git add . && git commit -m "ZYROX Code Encryptor v1.0"
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```
GitHub token chat me mat bhejo — push ke liye fresh token lagega to bata dena, secure tareeke se karenge.

Made by ZYROX 😈
