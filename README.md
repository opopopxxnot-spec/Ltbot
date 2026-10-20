# 🔥 LeetCode Daily Streak Bot

Automated bot that solves the LeetCode Daily Challenge every day using **Gemini AI** and maintains your streak with auto-commits.

## How It Works

1. **Fetches** today's Daily Challenge via LeetCode's GraphQL API  
2. **Generates** a solution using Gemini 2.5 Flash  
3. **Submits** the code and polls the judge for results  
4. **Self-heals** — if submission fails, feeds the judge error back to Gemini for up to 3 retries  
5. **Falls back** to solving Two Sum if all AI attempts fail (preserves streak)  
6. **Auto-commits** a streak log entry to keep your GitHub contribution graph green  
7. **Notifies** via Discord webhook (optional)

## Setup

### 1. Add GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `LC_USERNAME` | Your LeetCode username |
| `LEETCODE_SESSION` | `LEETCODE_SESSION` cookie from browser DevTools |
| `CSRF_TOKEN` | `csrftoken` cookie from browser DevTools |
| `GEMINI_API_KEY` | API key from [Google AI Studio](https://aistudio.google.com/apikey) |
| `DISCORD_WEBHOOK` | *(Optional)* Discord channel webhook URL |

### 2. Get Your LeetCode Cookies

1. Log in to [leetcode.com](https://leetcode.com)  
2. Open DevTools → **Application** → **Cookies** → `https://leetcode.com`  
3. Copy the values of `LEETCODE_SESSION` and `csrftoken`

> ⚠️ These cookies expire periodically — refresh them if the bot starts failing.

### 3. Run

The bot runs automatically every day at **00:30 UTC** (06:00 IST).  
You can also trigger it manually from the **Actions** tab → **Run workflow**.

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `TARGET_LANG` | `cpp` | Language to solve in (`cpp` or `java`) |

## Project Structure

```
├── bot.py                          # Main solver script
├── requirements.txt                # Python dependencies
├── logs/streak.log                 # Auto-committed streak log
├── .github/workflows/streak.yml   # GitHub Actions cron workflow
└── README.md
```
