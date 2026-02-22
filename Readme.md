# 🚀 How to Run — Recipe Explorer

**One command starts everything** — frontend + API on the same port.

---

## Commands (copy-paste ready)

```bash
# 1. Go into the project folder
cd Recipe_Explorer_API

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed the database  (put recipes.json in the same folder first)
python seed.py recipes.json

# 4. Start the server
uvicorn main:app --port 8000 --reload
```

---

## Open in browser

| What | URL |
|------|-----|
| **Frontend UI** | http://127.0.0.1:8000 |
| **API Swagger Docs** | http://127.0.0.1:8000/docs |
| **From phone / other device on same Wi-Fi** | http://YOUR_IP:8000 |

---

## Find your IP address

**Windows:**
```
ipconfig
```
Look for `IPv4 Address` — e.g. `192.168.1.105`

**Mac / Linux:**
```bash
hostname -I
```

Then open `http://192.168.1.105:8000` on any device on the same Wi-Fi.

---

## Troubleshooting

**"No module named aiofiles"**
```bash
pip install aiofiles
```

**Can't reach from another device**

Allow port 8000 through your firewall:
- Windows: Windows Defender Firewall → Allow port 8000
- Mac: System Settings → Network → Firewall
- Linux: `sudo ufw allow 8000`

**Port already in use**
```bash
uvicorn main:app --port 8001 --reload
# then open http://127.0.0.1:8001
```
