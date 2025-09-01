# OVH VPS Availability Checker

A Python script that automatically checks VPS availability on OVH configurator page and sends notifications via Telegram when servers become available.

## Features

- Checks VPS-2 availability in specific regions (North America, Europe)
- Handles cookie popups and other page interactions automatically
- Sends Telegram notifications when servers are available
- Can run in headless mode on servers
- Includes cron job configuration for automated checking

## Requirements

- Python 3.8+
- Playwright browser automation library
- Telegram Bot (for notifications)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ovh_checker
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install chromium
playwright install-deps chromium
```

## Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` file with your settings:
```bash
HEADLESS=true
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Getting Telegram Credentials

1. Create a Telegram bot:
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Copy the bot token

2. Get your chat ID:
   - Message your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

## Usage

### Manual Run
```bash
python ovh_daily_checker.py
```

### Automated Run (Cron)
1. Make the script executable:
```bash
chmod +x run_checker.sh
```

2. Add to crontab (example: run every 30 minutes):
```bash
crontab -e
```

Add this line:
```
*/30 * * * * /path/to/ovh_checker/run_checker.sh
```

Or use the provided crontab configuration:
```bash
crontab crontab_config.txt
```

## What the Script Checks

The script monitors availability for:
- **VPS Model**: VPS-2 (6 vCore, 12GB RAM, 100GB NVMe)
- **Commitment**: No commitment (monthly billing)
- **Regions**:
  - North America: Canada - East - Beauharnois (BHS)
  - Europe: France - Gravelines (GRA)

## How It Works

1. Opens OVH VPS configurator page
2. Handles cookie consent popup
3. Removes any interfering geo-location popups
4. Selects VPS-2 configuration
5. Selects "No commitment" billing
6. Checks availability in each target region
7. Sends Telegram notification if servers are available

## Output Examples

### When servers are available:
```
Server available in North America!

- Location: Canada - East - Beauharnois (BHS)
- [Book now](https://www.ovhcloud.com/en/vps/configurator/)
```

### When servers are not available:
```
Location BHS (North America) not available (container disabled).
Location GRA (Europe) not available (container disabled).
```

## Troubleshooting

### Script fails to find elements
- The script includes robust error handling for page structure changes
- It tries multiple selectors and fallback methods
- Check console output for specific error messages

### Telegram notifications not working
- Verify bot token and chat ID in `.env` file
- Make sure you've messaged the bot at least once
- Check that the bot token has necessary permissions

### Running on a VPS/Server
- Set `HEADLESS=true` in `.env` file
- Install Xvfb for virtual display if needed:
```bash
sudo apt install xvfb
```

- For viewing browser actions on VPS:
```bash
# Install VNC server
sudo apt install x11vnc

# Start virtual display
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Start VNC server
x11vnc -display :99 -bg -nopw -listen localhost

# Connect from local machine
ssh -L 5900:localhost:5900 user@your-vps
# Then connect VNC client to localhost:5900
```

## File Structure

```
ovh_checker/
├── ovh_daily_checker.py   # Main script
├── run_checker.sh         # Shell wrapper for cron
├── requirements.txt       # Python dependencies
├── crontab_config.txt     # Cron configuration
├── .env.example          # Environment template
├── .env                  # Your configuration (not in git)
└── README.md             # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This script is for educational and personal use only. Please respect OVH's terms of service and don't abuse their systems with excessive requests.
