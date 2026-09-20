# RPI Class Seat Finder Discord Bot 🪑

A Discord bot that monitors class availability at **Rensselaer Polytechnic Institute (RPI)** and notifies your Discord server when seats become available.

Instead of repeatedly checking SIS yourself, provide the bot with one or more **Course Registration Numbers (CRNs)** and it will periodically check their enrollment availability for you.

When a seat becomes available, the bot updates the class status in Discord and can notify the server so you can register as soon as possible.

## How It Works

The bot periodically requests the RPI SIS course detail page for each CRN being monitored.

`seat_scrapper.py` parses the returned HTML and extracts:

* Course name
* Total number of seats
* Number of seats remaining

`seat_finder_bot.py` manages the Discord bot, active seat hunts, commands, notifications, and the polling loop.

The basic flow is:

```text
Discord Command
      ↓
CRN(s) added to hunt
      ↓
RPI SIS queried
      ↓
Course HTML parsed
      ↓
Seat availability extracted
      ↓
Discord status updated
      ↓
Repeat every 60 seconds
```

---

## Commands

### `/begin_hunt`

Starts monitoring one or more CRNs.

```text
/begin_hunt 77330
```

Multiple CRNs can be separated by spaces:

```text
/begin_hunt 77330 78854
```

or commas:

```text
/begin_hunt 77330, 78854
```

Starting a new hunt replaces the currently active hunt for that server or user.

---

### `/add_class`

Adds another CRN to the currently active hunt.

```text
/add_class 77330
```

---

### `/remove_class`

Removes a CRN from the currently active hunt.

```text
/remove_class 77330
```

---

### `/hunt_status`

Checks whether a seat hunt is currently active.

```text
/hunt_status
```

---

### `/stop_hunt`

Stops the currently active seat hunt.

```text
/stop_hunt
```

---

### `/ping`

Checks whether the bot is running.

```text
/ping
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/HiddenDevelop/RPI-Class-Seat-Finder-Discord-Bot.git
cd RPI-Class-Seat-Finder-Discord-Bot
```

### 2. Create a virtual environment

Creating a virtual environment is recommended so the project's dependencies remain isolated.

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project uses packages including:

* `discord.py`
* `aiohttp`
* `beautifulsoup4`
* `python-dotenv`

---

## Discord Bot Setup

You will need to create your own Discord application and bot.

### 1. Create a Discord application

Go to the **Discord Developer Portal** and create a new application.

### 2. Create the bot

Open the **Bot** section of your application and create a bot user.

### 3. Copy your bot token

Generate or copy the bot token.

> [!WARNING]
> Never commit your Discord bot token to GitHub or share it publicly.

### 4. Enable the required intent

The bot enables Discord's **Message Content Intent**, so make sure it is enabled for your bot in the Discord Developer Portal if required by your configuration.

### 5. Invite the bot

Generate an invite URL for the bot with the appropriate scopes and permissions.

Recommended scopes:

```text
bot
applications.commands
```

The bot should have permissions necessary to:

* View the channel
* Send messages
* Embed links
* Read message history

If you want server-wide `@everyone` notifications to work, the bot may also need permission to mention everyone.

---

## Environment Variables

Create a file named `.env` in the root directory:

```env
DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
```

Replace `YOUR_DISCORD_BOT_TOKEN` with the token from the Discord Developer Portal.

Your directory should look similar to:

```text
RPI-Class-Seat-Finder-Discord-Bot/
├── .env
├── LICENSE
├── requirements.txt
├── seat_finder_bot.py
└── seat_scrapper.py
```

### Keep `.env` private

Your `.env` file contains credentials and should **not** be committed to Git.

If you do not already have a `.gitignore`, create one containing:

```gitignore
.env
.venv/
venv/
__pycache__/
*.pyc
```

---

## Running the Bot

Start the bot with:

```bash
python seat_finder_bot.py
```

Depending on your system, you may need:

```bash
python3 seat_finder_bot.py
```

Once connected successfully, the terminal will display information about the bot, connected Discord servers, and synchronized slash commands.

You can then use:

```text
/begin_hunt <CRN>
```

inside Discord.

---

## Example

Suppose you want to monitor two classes with CRNs `77330` and `78854`.

Run:

```text
/begin_hunt 77330 78854
```

The bot begins monitoring both CRNs and checks RPI SIS approximately once every minute.

When a course has available seats, the Discord embed displays something similar to:

```text
SEAT AVAILABLE

Course Name

🪑 Availability
1 / 30 seats available

👉 Register now!

⏱️ Last checked
...
```

When a class is full, its status is displayed as:

```text
CLASS FULL

Course Name

🪑 Availability
0 / 30 seats available
```

---

## Project Structure

```text
RPI-Class-Seat-Finder-Discord-Bot/
│
├── seat_finder_bot.py
│   ├── Discord bot setup
│   ├── Slash commands
│   ├── Seat-hunt management
│   ├── Polling loop
│   └── Discord notifications
│
├── seat_scrapper.py
│   ├── Requests RPI SIS course pages
│   └── Parses course and seat information
│
├── requirements.txt
│   └── Python dependencies
│
└── LICENSE
    └── MIT License
```

---

## Current Semester Configuration

The RPI SIS URL in `seat_scrapper.py` currently contains a hard-coded term:

```python
term_in=202609
```

Because RPI SIS uses term-specific identifiers, this value may need to be changed for a different semester.

The relevant URL is constructed in `seat_scrapper.py`:

```python
url = f"https://sis.rpi.edu/rss/bwckschd.p_disp_detail_sched?term_in=202609&crn_in={crn}"
```

If the bot stops finding valid course information after a semester change, verify that the correct SIS term identifier is being used.

---

## Important Notes

### Hunts are stored in memory

Active hunts are stored in the running Python process. They are not currently saved to a database or file.

This means restarting the bot will clear all active hunts.

### One active hunt per server/user

The bot tracks hunts by Discord server. In direct messages, hunts are associated with the individual Discord user.

Starting another `/begin_hunt` replaces the existing hunt for that server or user.

### RPI SIS HTML changes

The scraper relies on the HTML structure returned by RPI SIS. If RPI changes the layout of its SIS pages, `seat_scrapper.py` may need to be updated.

### Polling interval

The current polling interval is:

```python
sleep_time = 60
```

which means the bot checks approximately once every **60 seconds**.

Please use reasonable polling intervals to avoid placing unnecessary load on RPI's systems.

---

## Technologies Used

* **Python**
* **discord.py**
* **aiohttp**
* **Beautiful Soup**
* **python-dotenv**
* **RPI SIS**

---

## Potential Future Improvements

Possible improvements to the project include:

* Automatically determine the current RPI semester/term
* Persist hunts across bot restarts
* Add database support
* Allow custom notification roles
* Add configurable polling intervals
* Improve invalid-CRN detection
* Add course search by subject/course number
* Add Docker support
* Add logging instead of console-only output
* Add automated tests
* Add per-user hunts within a Discord server
* Add a direct link to registration/course details in notifications

---

## Disclaimer

This project is an independent tool and is **not affiliated with, endorsed by, or maintained by Rensselaer Polytechnic Institute**.

Course availability can change quickly, and information returned by this bot should not be considered a guarantee that a seat will still be available when you attempt to register.

Use the bot responsibly and avoid unnecessarily aggressive polling of RPI services.

---

## License

This project is licensed under the **MIT License**.

See [`LICENSE`](LICENSE) for details.

---

## Author

Created by [HiddenDevelop](https://github.com/HiddenDevelop).

If you find the project useful, consider giving the repository a ⭐.
