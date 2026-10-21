#!/usr/bin/env python3
"""
ZYROX CODE ENCRYPTOR v1.0
Encrypt: .py | .js (Node) | .html
Stdlib ONLY - no pip install. Runs: Termux, Linux, Windows, GitHub Codespaces/Actions.

Encryption core:
  key  = PBKDF2-HMAC-SHA256(password OR auto-key, salt, 200_000)  [password mode]
         OR random 32-byte key split/masked in loader            [auto mode]
  stream = HMAC-SHA256(key, nonce || counter32BE) per 32-byte block (CTR-style)
  cipher = zlib.compress(plain) XOR stream
  tag    = HMAC-SHA256(key, nonce||cipher)  -> tamper check (galat password = fail)

HONEST LIMIT:
  - Password mode: bina password koi decrypt NAHI kar sakta (real encryption).
  - Auto mode (code khud chalna hai): key loader ke andar chhupti hai,
    isliye ye strong obfuscation + encryption hai, 100% impossible nahi.
    Jo code chalega, expert kabhi na kabhi runtime par nikaal sakta hai.
    Server-secret / license logic hamesha apne server par rakho.
"""
import argparse, base64, hashlib, hmac, os, struct, sys, zlib, secrets

VERSION = "1.0"
PBKDF_ITER = 200_000

def derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF_ITER, dklen=32)

def keystream(key: bytes, nonce: bytes, n: int) -> bytes:
    out = bytearray()
    ctr = 0
    while len(out) < n:
        out += hmac.new(key, nonce + struct.pack(">I", ctr), hashlib.sha256).digest()
        ctr += 1
    return bytes(out[:n])

def xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))

def encrypt_data(plain: bytes, key: bytes, compress=True):
    salt = b""  # salt stored separately when password mode
    nonce = secrets.token_bytes(16)
    data = zlib.compress(plain, 9) if compress else plain
    ks = keystream(key, nonce, len(data))
    cipher = xor_bytes(data, ks)
    tag = hmac.new(key, nonce + cipher, hashlib.sha256).digest()
    return nonce, cipher, tag

def b64_chunks(data: bytes, width=76):
    s = base64.b64encode(data).decode()
    return "\n".join(s[i:i+width] for i in range(0, len(s), width))

def split_key_mask(key: bytes):
    """Split auto key into 2 masked shares: shareA (random), shareB = key XOR shareA."""
    a = secrets.token_bytes(32)
    b = xor_bytes(key, a)
    return a, b

# ---------------------------------------------------------------- PYTHON
def build_python(plain: bytes, password):
    if password:
        salt = secrets.token_bytes(16)
        key = derive_key(password, salt)
        nonce, cipher, tag = encrypt_data(plain, key, compress=True)
        salt_b64 = base64.b64encode(salt).decode()
        key_block = f'''import getpass
_salt=__import__("base64").b64decode("{salt_b64}")
_pw=getpass.getpass("Password: ")
_k=__import__("hashlib").pbkdf2_hmac("sha256",_pw.encode(),_salt,{PBKDF_ITER},dklen=32)'''
    else:
        key = secrets.token_bytes(32)
        a, b = split_key_mask(key)
        nonce, cipher, tag = encrypt_data(plain, key, compress=True)
        key_block = f'''_s1=bytes.fromhex("{a.hex()}")
_s2=bytes.fromhex("{b.hex()}")
_k=bytes(x^y for x,y in zip(_s1,_s2))'''
    loader = f'''#!/usr/bin/env python3
# ZYROX ENCRYPTED - v{VERSION} - do not edit
import sys as _s, base64 as _b, hashlib as _h, hmac as _hm, struct as _st, zlib as _z
if _s.gettrace() is not None: _s.exit(1)
_P="""{b64_chunks(cipher)}"""
_N=bytes.fromhex("{nonce.hex()}")
_T=bytes.fromhex("{tag.hex()}")
{key_block}
if not _hm.compare_digest(_hm.new(_k,_N+_b.b64decode(_P),_h.sha256).digest(),_T):
    print("ZYROX: wrong password / file tampered"); _s.exit(1)
_c=_b.b64decode(_P); _ks=bytearray(); _ctr=0
while len(_ks)<len(_c):
    _ks+=_hm.new(_k,_N+_st.pack(">I",_ctr),_h.sha256).digest(); _ctr+=1
_raw=_z.decompress(bytes(x^y for x,y in zip(_c,bytes(_ks[:len(_c)]))))
exec(compile(_raw,"<zyrox>","exec"),{{"__name__":"__main__","__file__":"zyrox_encrypted.py"}})
'''
    return loader.encode()

# ---------------------------------------------------------------- NODE.JS
def build_node(plain: bytes, password):
    if password:
        salt = secrets.token_bytes(16)
        key = derive_key(password, salt)
        nonce, cipher, tag = encrypt_data(plain, key, compress=True)
        key_block = f'''const _salt=Buffer.from("{salt.hex()}","hex");
const _pw=require("readline-sync")&&false; // no deps: stdin prompt below
'''
        # No-dep password prompt: read from env ZYROX_PASSWORD or argv/stdin sync
        key_block = f'''const _salt=Buffer.from("{salt.hex()}","hex");
let _pw=process.env.ZYROX_PASSWORD||"";
if(!_pw){{process.stdout.write("Password: ");const _b=Buffer.alloc(1024);const _n=require("fs").readSync(0,_b,0,1024,null);_pw=_b.toString("utf8",0,_n).trim();}}
const _k=require("crypto").pbkdf2Sync(_pw,_salt,{PBKDF_ITER},32,"sha256");'''
    else:
        key = secrets.token_bytes(32)
        a, b = split_key_mask(key)
        nonce, cipher, tag = encrypt_data(plain, key, compress=True)
        key_block = f'''const _a=Buffer.from("{a.hex()}","hex"),_b=Buffer.from("{b.hex()}","hex");
const _k=Buffer.alloc(32);for(let i=0;i<32;i++)_k[i]=_a[i]^_b[i];'''
    cipher_b64 = base64.b64encode(cipher).decode()
    loader = f'''// ZYROX ENCRYPTED - v{VERSION} - do not edit
"use strict";
const _cr=require("crypto"),_z=require("zlib");
const _P=Buffer.from("{cipher_b64}","base64");
const _N=Buffer.from("{nonce.hex()}","hex"),_T=Buffer.from("{tag.hex()}","hex");
{key_block}
const _tag=_cr.createHmac("sha256",_k).update(Buffer.concat([_N,_P])).digest();
if(!_cr.timingSafeEqual(_tag,_T)){{console.error("ZYROX: wrong password / file tampered");process.exit(1);}}
const _out=Buffer.alloc(_P.length);let _off=0,_ctr=0;
while(_off<_P.length){{const _cb=Buffer.alloc(4);_cb.writeUInt32BE(_ctr++);
const _ks=_cr.createHmac("sha256",_k).update(Buffer.concat([_N,_cb])).digest();
for(let i=0;i<_ks.length&&_off<_P.length;i++,_off++)_out[_off]=_P[_off]^_ks[i];}}
const _src=_z.inflateSync(_out).toString("utf8");
module.paths=(module.paths||[]);const _m=new (require("module"))();_m._compile(_src,__filename);
'''
    return loader.encode()

# ---------------------------------------------------------------- HTML
def build_html(plain: bytes, password):
    # HTML: no compression (browser DecompressionStream format mismatch risk) -> compress=False
    if password:
        salt = secrets.token_bytes(16)
        key = derive_key(password, salt)
        nonce, cipher, tag = encrypt_data(plain, key, compress=False)
        key_js = f'''const salt=Uint8Array.from(Buffer.from("{salt.hex()}","hex"));
async function getKey(){{const pw=prompt("ZYROX - Password daalo:");if(pw===null)throw new Error("cancelled");
const base=await crypto.subtle.importKey("raw",new TextEncoder().encode(pw),"PBKDF2",false,["deriveBits"]);
const bits=await crypto.subtle.deriveBits({{name:"PBKDF2",salt:salt,iterations:{PBKDF_ITER},hash:"SHA-256"}},base,256);
return new Uint8Array(bits);}}'''
    else:
        key = secrets.token_bytes(32)
        a, b = split_key_mask(key)
        nonce, cipher, tag = encrypt_data(plain, key, compress=False)
        key_js = f'''async function getKey(){{const a=Uint8Array.from(Buffer.from("{a.hex()}","hex"));const b=Uint8Array.from(Buffer.from("{b.hex()}","hex"));const k=new Uint8Array(32);for(let i=0;i<32;i++)k[i]=a[i]^b[i];return k;}}'''
    cipher_b64 = base64.b64encode(cipher).decode()
    # JS helpers: Buffer is Node-only; in browser define from hex/base64 without Buffer
    key_js = key_js.replace('Uint8Array.from(Buffer.from("', 'hexToBytes("').replace('","hex"))', '")')
    # Simpler: rewrite both branches cleanly
    if password:
        key_js = f'''async function getKey(){{const pw=prompt("ZYROX - Password daalo:");if(pw===null)throw new Error("cancelled");
const base=await crypto.subtle.importKey("raw",new TextEncoder().encode(pw),"PBKDF2",false,["deriveBits"]);
const bits=await crypto.subtle.deriveBits({{name:"PBKDF2",salt:hexToBytes("{salt.hex()}"),iterations:{PBKDF_ITER},hash:"SHA-256"}},base,256);
return new Uint8Array(bits);}}'''
    else:
        key_js = f'''async function getKey(){{const a=hexToBytes("{a.hex()}"),b=hexToBytes("{b.hex()}");const k=new Uint8Array(32);for(let i=0;i<32;i++)k[i]=a[i]^b[i];return k;}}'''
    loader = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>ZYROX Encrypted</title></head>
<body><div style="font-family:sans-serif;text-align:center;margin-top:40px">ZYROX - Decrypting...</div>
<script>
function hexToBytes(h){{const u=new Uint8Array(h.length/2);for(let i=0;i<u.length;i++)u[i]=parseInt(h.substr(i*2,2),16);return u;}}
function b64ToBytes(s){{const bin=atob(s);const u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);return u;}}
{key_js}
async function hmac(key,msg){{const k=await crypto.subtle.importKey("raw",key,{{name:"HMAC",hash:"SHA-256"}},false,["sign"]);return new Uint8Array(await crypto.subtle.sign("HMAC",k,msg));}}
(async()=>{{
 const P=b64ToBytes("{cipher_b64}"),N=hexToBytes("{nonce.hex()}"),T=hexToBytes("{tag.hex()}");
 const key=await getKey();
 const macMsg=new Uint8Array(N.length+P.length);macMsg.set(N);macMsg.set(P,N.length);
 const tag=await hmac(key,macMsg);
 if(tag.length!==T.length||!tag.every((v,i)=>v===T[i])){{document.body.textContent="ZYROX: wrong password / file tampered";return;}}
 const out=new Uint8Array(P.length);let off=0,ctr=0;
 while(off<P.length){{const cb=new Uint8Array(4);new DataView(cb.buffer).setUint32(0,ctr++);
  const msg=new Uint8Array(N.length+4);msg.set(N);msg.set(cb,N.length);
  const ks=await hmac(key,msg);
  for(let i=0;i<ks.length&&off<P.length;i++,off++)out[off]=P[off]^ks[i];}}
 const html=new TextDecoder().decode(out);
 document.open();document.write(html);document.close();
}})();
</script></body></html>
'''
    return loader.encode()

BUILDERS = {".py": build_python, ".js": build_node, ".html": build_html, ".htm": build_html}

def main():
    ap = argparse.ArgumentParser(prog="zyrox_encrypt", description="ZYROX Code Encryptor - py/js/html")
    ap.add_argument("input", help="input file (.py / .js / .html)")
    ap.add_argument("-o", "--output", help="output file (default: <name>.zyrox.<ext>)")
    ap.add_argument("-p", "--password", help="password mode (STRONG: bina password decrypt impossible). Na do to AUTO mode (code khud chalega, key chhupi hui).")
    args = ap.parse_args()
    ext = os.path.splitext(args.input)[1].lower()
    if ext not in BUILDERS:
        print(f"ZYROX: unsupported type {ext} - sirf .py .js .html"); sys.exit(2)
    with open(args.input, "rb") as f: plain = f.read()
    out_path = args.output or (os.path.splitext(args.input)[0] + ".zyrox" + ext)
    result = BUILDERS[ext](plain, args.password)
    with open(out_path, "wb") as f: f.write(result)
    mode = "PASSWORD (strong)" if args.password else "AUTO (obfuscated)"
    print(f"ZYROX OK: {args.input} -> {out_path} | {len(plain)}B -> {len(result)}B | mode={mode}")

if __name__ == "__main__":
    main()
