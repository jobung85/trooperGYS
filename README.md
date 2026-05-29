# Trooper WhatsApp Bot

A small Flask + Python service that bridges your **Notion "Trooper" project** with **WhatsApp** via Meta's Cloud API.

It does three things:

1. **Detects new Main Tasks** in Notion and (a) creates one *Task Tracker* row per Trooper and (b) sends each Trooper a WhatsApp ping.
2. **Answers `tasks`** — when a Trooper messages the bot, it replies with their pending tasks.
3. **Marks tasks done** — `done <Task ID>` flips the row's *Status* to *Done* in the Task Tracker.

```
WhatsApp (Meta)  ─►  /webhook  (Flask, web service)
                                    │
                                    ▼
                            command_handler  ─►  Notion API
                                    ▲
                                    │
              every 6h  ──►  poller.py  ──►  Notion (read+write) ──► WhatsApp send
```

---

## 1. Folder layout

```
trooper-whatsapp-bot/
├── app/
│   ├── config.py              # env + roster loader
│   ├── notion_client.py       # Main Task / Task Tracker helpers
│   ├── whatsapp_client.py     # send_text + parse_inbound
│   ├── poller.py              # run_once() — the cron payload
│   ├── command_handler.py     # tasks / done / redo / help
│   ├── state.py               # JSON cursor (last poll, seen IDs)
│   └── main.py                # Flask app + /webhook
├── scripts/
│   ├── poll_once.py           # Render Cron entry point
│   └── test_send.py           # CLI to verify WA creds
├── config/
│   └── troopers.json          # NAME → WhatsApp phone roster
├── render.yaml                # Render Blueprint (web + cron)
├── Procfile                   # Generic web start command
├── requirements.txt
├── .env.example
└── README.md
```

---

## 2. Local setup

```bash
cd trooper-whatsapp-bot
python -m venv .venv
.venv\Scripts\activate            # PowerShell:  .venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env             # fill it in (next section)
notepad config\troopers.json       # put real phone numbers
```

Smoke-test the WhatsApp credentials before doing anything else:

```bash
python -m scripts.test_send 628xxxxxxxxxx "hello from trooper-bot"
```

You should receive a WhatsApp message on `628xxxxxxxxxx`.

> **Heads-up:** Until your Meta app is *Approved for production*, Meta only delivers messages to **phone numbers explicitly added** as test recipients in *WhatsApp → API Setup → Test recipients*. Add each Trooper's number there first.

---

## 3. Notion setup (one-time)

1. Open the *Trooper* page in Notion.
2. Click **`•••` (top right) → Connections → "Connect to" → choose your integration.**
   - If you don't have one yet, create it at <https://www.notion.so/my-integrations> (Internal, "Read content" + "Update content" + "Insert content").
3. Verify it has access to *both* `Main Task` and `Task Tracker` databases. (Connections inherit on child databases automatically.)
4. The two database IDs are already filled in `.env.example`:

   | DB | ID |
   | --- | --- |
   | Main Task | `36fe9c57-814d-80c8-8ea0-cb45f5ee2eb2` |
   | Task Tracker | `36fe9c57-814d-80d9-8704-f26fec4bf51d` |

5. Make sure each Notion *Trooper* select option matches `notion_name` in `config/troopers.json`:

   | Notion option | Roster entry |
   | --- | --- |
   | `Sdri Cien-Cien` | Cien-Cien |
   | `Sdri Lisa` | Lisa |
   | `Sdri Nove` | Nove |
   | `Sdr Jonathan` | Jonathan |

---

## 4. WhatsApp Cloud API setup (one-time)

You already have:

- **Phone Number ID:** `1059304737269663`
- **Access token:** `EAA9MogQ0MMkB...` (long token)

Note: that token is a **24-hour user token** — for production use a **System User permanent token** so it doesn't expire:

1. Meta Business → Settings → Users → System Users → *Add* → name: `trooper-bot`, role: *Admin*.
2. *Add Assets* → your WhatsApp Business app + WhatsApp account.
3. *Generate new token* → permissions `whatsapp_business_messaging`, `whatsapp_business_management`. **Save it** — you can't view it again.
4. Put it in `.env` as `WHATSAPP_ACCESS_TOKEN`.

### Webhook subscription

In Meta App Dashboard → **WhatsApp → Configuration → Webhook**:

- **Callback URL:** your public HTTPS URL + `/webhook`  (ngrok in dev, Render in prod — see below)
- **Verify token:** the same string you set as `WHATSAPP_VERIFY_TOKEN` in `.env` (e.g. `trooper-bot-verify-2026`)
- **Subscribe to:** `messages` (just that one — that's what we need)

Meta will GET your `/webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...` once. Our Flask app handles it.

---

## 5. ngrok — local development

> ngrok gives your localhost a public HTTPS URL so Meta can reach it.

### 5.1 Install

- **Windows (PowerShell):** `winget install ngrok.ngrok`
- Or download <https://ngrok.com/download> and unzip.

### 5.2 Authenticate

1. Sign up at <https://dashboard.ngrok.com> (free).
2. Copy your **authtoken** from <https://dashboard.ngrok.com/get-started/your-authtoken>.
3. Run once:

```bash
ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>
```

### 5.3 (Recommended) Reserve a static domain

The free plan now includes **one** free static domain — so your URL doesn't change every restart (very useful, otherwise you'd re-paste it into Meta every time):

1. Dashboard → **Cloud Edge → Domains → Create Domain** (e.g. `trooper-bot-jonathan.ngrok-free.app`).
2. Copy that hostname.

### 5.4 Run the app + tunnel

Terminal A (the Flask app):

```bash
cd trooper-whatsapp-bot
.venv\Scripts\activate
python -m app.main      # listens on :5000
```

Terminal B (the tunnel):

```bash
ngrok http --url=handcraft-procedure-unluckily.ngrok-free.dev 5000
```

Your Meta webhook callback URL is **`https://handcraft-procedure-unluckily.ngrok-free.dev/webhook`** — paste it into the Meta dashboard once and you never need to touch it again (the free static domain is permanently reserved on this account).

### 5.5 Manual cron trigger while developing

You don't need to wait 6h to test — fire the poller manually:

```bash
# Inside the project (with .venv active)
python -m scripts.poll_once
```

…or hit the secret HTTP trigger:

```bash
curl -X POST http://localhost:5000/internal/poll \
     -H "X-Trigger-Secret: trooper-bot-verify-2026"
```

---

## 6. Production deploy — Render (web) + GitHub Actions (cron)

Render's free tier covers the **Flask webhook**, and GitHub Actions runs the **6-hourly poller** (Render dropped the free Cron Job tier; GitHub Actions is free with generous quota for both public and private repos).

### 6.1 Push to GitHub

This project lives at <https://github.com/jobung85/trooperGYS>. To update:

```bash
git add .
git commit -m "describe change"
git push
```

### 6.2 Render Blueprint deploy

One-click deploy URL — opens Render with this repo pre-filled:

<https://render.com/deploy?repo=https://github.com/jobung85/trooperGYS>

1. Sign in (free, GitHub OAuth).
2. Render reads `render.yaml` and creates one Web Service: `trooper-bot`.
3. When prompted, paste the secret env vars (the Blueprint marks them `sync: false`):
   - `NOTION_TOKEN`
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_VERIFY_TOKEN`
4. Click **Apply**. Build takes ~2 minutes.

### 6.3 GitHub Actions cron secrets

Add the same 3 secrets at <https://github.com/jobung85/trooperGYS/settings/secrets/actions>:

| Name | Value |
| --- | --- |
| `NOTION_TOKEN` | `ntn_…` |
| `WHATSAPP_ACCESS_TOKEN` | `EAA9MogQ0MMkB…` (System User token) |
| `WHATSAPP_VERIFY_TOKEN` | `trooper-bot-verify-2026` |

Workflow file: `.github/workflows/trooper-poll.yml`. Run it manually any time from <https://github.com/jobung85/trooperGYS/actions/workflows/trooper-poll.yml>.

### 6.4 Update Meta webhook to Render URL

After the web service is live, copy its URL (e.g. `https://trooper-bot.onrender.com`) and paste **`https://trooper-bot.onrender.com/webhook`** into Meta Dashboard → WhatsApp → Configuration → Webhook (verify token `trooper-bot-verify-2026`).

### 6.5 Updating the roster (phone numbers)

`config/troopers.json` is checked into the repo — to update phone numbers, edit + commit + push, and Render auto-redeploys. (If you don't want phones in git, move them to env vars and adjust `app/config.py`.)

---

## 8. Bot commands cheat-sheet

| What you say (WhatsApp) | What the bot does |
| --- | --- |
| `tasks` | Lists your Not-started Task Tracker rows |
| `tasks all` | Lists pending + last 5 done |
| `done T-001` | Sets *T-001*'s Status → Done, stamps Comment Date today |
| `redo T-001` | Sets *T-001* back to Not started |
| `help` | Shows the menu |

Spelling alternatives accepted: `done` ⇆ `selesai` ⇆ `finished`, `redo` ⇆ `belum` ⇆ `undo`.

---

## 9. Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| Webhook verification fails (403) | `WHATSAPP_VERIFY_TOKEN` mismatch between `.env` and Meta dashboard |
| Outbound `send_text` 401 | Access token expired — generate a permanent System User token (§4) |
| "object_not_found" from Notion | Integration not yet connected to the *Trooper* page (§3 step 2) |
| Bot replies "this number isn't registered" | Phone in `config/troopers.json` doesn't match the inbound (Meta sends without `+`, your config also without `+`) |
| New Main Task created but no notification | (a) The page's *Create Date* is in the past beyond our 14-day lookback on first run, or (b) the integration can't read that DB |
| Render free web sleeps & misses a webhook | Meta retries 3× over 5 min — usually OK. If it bothers you, hit `/health` from a free uptime pinger like UptimeRobot every 14 min. |

---

## 10. License / contact

Internal — Jonathan Handoyo, 2026.
