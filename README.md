# OVH VPS Availability Checker

A Python script that automatically checks for VPS server availability at OVH and notifies you via Telegram when servers become available.

## 🔍 What does it do?

- Checks availability of VPS-2 servers in locations:
  - **North America**: Canada - East - Beauharnois (BHS)
  - **Europe**: France - Gravelines (GRA)
- Sends Telegram notifications only when availability is detected
- Runs automatically using crontab
- Saves logs of each execution

## 🚀 Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd ovh_checker
```

### 2. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate     # On Windows
```

### 3. Install dependencies
```bash
pip install requests python-dotenv playwright
playwright install chromium
```

### 4. Configure Telegram
1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
2. Get your Chat ID with [@userinfobot](https://t.me/userinfobot)
3. Copy the configuration file:
```bash
cp .env.example .env
```
4. Edit `.env` with your credentials:
```bash
TELEGRAM_BOT_TOKEN="your_real_token_here"
TELEGRAM_CHAT_ID="your_real_chat_id_here"
```

## 🧪 Manual testing

```bash
# Run once to test
python ovh_daily_checker.py

# Or use the wrapper script
./run_checker.sh
```

## ⏰ Configure automatic execution

### Option 1: Every 6 hours
```bash
echo "0 0,6,12,18 * * * $(pwd)/run_checker.sh" | crontab -
```

### Option 2: Every 12 hours (11 AM and 11 PM)
```bash
echo "0 11,23 * * * $(pwd)/run_checker.sh" | crontab -
```

### Option 3: Once a day (9 AM)
```bash
echo "0 9 * * * $(pwd)/run_checker.sh" | crontab -
```

## 📁 Project structure

```
ovh_checker/
├── ovh_daily_checker.py    # Main script
├── run_checker.sh          # Wrapper script for cron
├── elements.txt            # HTML elements reference
├── .env.example           # Configuration template
├── .env                   # Your configuration (not uploaded to git)
├── logs/                  # Execution logs
└── README.md             # This file
```

## 🔧 Customization

To change the verified locations, edit `ovh_daily_checker.py` in the `main()` function.

## 📊 Logs

Logs are saved in `logs/` with timestamp. They are automatically deleted after 30 days.

## 🛑 Stop the script

```bash
# View current crontab
crontab -l

# Remove entire cron configuration
crontab -r

# Or edit to remove only this line
crontab -e
```

## 🤝 Contributions

Contributions are welcome. Please:
1. Fork the project
2. Create a branch for your feature
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file for details.
