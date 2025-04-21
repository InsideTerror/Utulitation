# Template_Bot

A modular, fully asynchronous Discord bot built with `discord.py`, hosted on Railway. Designed for managing hearings, server setup, and reaction roles with in-Discord UI.

## ✅ Features

- **Modular Cog System**
- **Server Setup:** Run `!setup_server` to initialize channels and roles.
- **Court Hearings:** Create temporary hearing channels that auto-expire after 24 hours of inactivity.
- **Reaction Roles:** Assign roles based on reactions, configured entirely through Discord.

## 🛠 Setup

### 1. Clone This Repo
```bash
git clone https://github.com/InsideTerror/Template_Bot.git
cd Template_Bot
```

### 2. Add a `.env` file
Create a `.env` file with:
```env
DISCORD_TOKEN=your_discord_bot_token_here
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Bot
```bash
python bot.py
```

## ☁️ Hosting on Railway

1. Go to [Railway](https://railway.app)
2. Create a new project and link this GitHub repo
3. Set your `DISCORD_TOKEN` in **Project > Variables**
4. Railway will auto-detect and deploy your bot using Nixpacks

## 📁 Project Structure
```
Template_Bot/
├── bot.py                  # Main bot launcher
├── requirements.txt        # Python dependencies
├── cogs/
│   ├── setup.py            # Server setup cog
│   ├── hearing.py          # Hearing channel management
│   └── reaction_roles.py   # Reaction role management
├── reaction_roles.json     # Stores emoji/role config
└── README.md               # You're here
```

## 🔐 Intents
Ensure that the following **Privileged Intents** are enabled in your bot settings on the Discord Developer Portal:
- Server Members
- Message Content (if needed)

## 👥 Commands Overview

### Server Setup
```bash
!setup_server
```
Creates categories, channels, and roles for your Discord server.

### Hearings
```bash
!hearing_create [channel_name] [@user1 @user2 ...]
```
Creates a temporary private channel for hearings. Auto-deletes after 24 hours of inactivity.

### Reaction Roles
```bash
!reactionrole_setup
```
Guides you through assigning emojis to roles via reactions.

## 👤 Maintainer
Built by [InsideTerror](https://github.com/InsideTerror)

---

Feel free to fork and customize for your own use!

