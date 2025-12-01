#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTO FORWARD BOT TELEGRAM V2.0 - FIXED VERSION
Created by: Private Team
Features: Multi-Account, Anti-Ban, License System
"""

import asyncio
import logging
import sys
import time
import os
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import Message
import sqlite3
import hashlib
import requests
import json

# ==================== CONFIGURATION ====================
class Config:
    # Bot API ID dan Hash (ganti dengan milik Anda)
    API_ID = 34185910  # Ganti dengan API ID Anda
    API_HASH = '08e1a02e6bbc8067b64b7b7150fa80ec'  # Ganti dengan API Hash Anda
    
    # License Key System
    LICENSE_KEYS = [
        "FWDBOT2024-X1A2B3C4D5E6F7G8H",
        "FWDBOT2024-Y9Z8W7X6V5U4T3S2",
        "FWDBOT2024-P1Q2R3S4T5U6V7W8",
        "FWDBOT2024-M9N8B7V6C5X4Z3L2"
    ]
    
    # Database setup
    DB_NAME = "forward_bot.db"
    
    # Admin user IDs (ganti dengan ID Telegram Anda)
    ADMIN_IDS = [7431149093]

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forward_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== DATABASE SETUP ====================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_NAME, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Tabel users untuk menyimpan data pengguna
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                license_key TEXT UNIQUE,
                expiry_date TEXT,
                max_accounts INTEGER DEFAULT 4,
                created_at TEXT
            )
        ''')
        
        # Tabel accounts untuk menyimpan akun Telegram
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                phone TEXT PRIMARY KEY,
                session_file TEXT,
                is_active INTEGER DEFAULT 1,
                user_id INTEGER,
                created_at TEXT
            )
        ''')
        
        # Tabel forwarding rules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forwarding_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                from_chat TEXT,
                to_chat TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id, license_key, days=30):
        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (user_id, license_key, expiry_date, created_at) VALUES (?, ?, ?, ?)',
                (user_id, license_key, expiry_date, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def validate_license(self, user_id, license_key):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT expiry_date FROM users WHERE user_id = ? AND license_key = ?',
            (user_id, license_key)
        )
        result = cursor.fetchone()
        if result:
            expiry_date = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
            return expiry_date > datetime.now()
        return False
    
    def add_account(self, user_id, phone, session_file):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO accounts (phone, session_file, user_id, created_at) VALUES (?, ?, ?, ?)',
            (phone, session_file, user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        self.conn.commit()
    
    def get_user_accounts(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT phone, session_file FROM accounts WHERE user_id = ? AND is_active = 1',
            (user_id,)
        )
        return cursor.fetchall()
    
    def add_forwarding_rule(self, user_id, from_chat, to_chat):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO forwarding_rules (user_id, from_chat, to_chat, created_at) VALUES (?, ?, ?, ?)',
            (user_id, from_chat, to_chat, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_forwarding_rules(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, from_chat, to_chat FROM forwarding_rules WHERE user_id = ? AND is_active = 1',
            (user_id,)
        )
        return cursor.fetchall()
    
    def get_all_users(self):
        """FIX: Added missing method"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT user_id FROM users')
        return [row[0] for row in cursor.fetchall()]
    
    def get_all_active_accounts(self):
        """Get all active accounts from database"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id, phone, session_file FROM accounts WHERE is_active = 1')
        return cursor.fetchall()

# ==================== TELEGRAM BOT CLASS ====================
class AutoForwardBot:
    def __init__(self):
        self.db = Database()
        self.clients = {}
        self.bot_token = "8310663236:AAH7IWCGZytOtpPnonNdECAcsgizpd9KLZk"
        self.bot = None
        self.setup_bot()
    
    def setup_bot(self):
        """Setup Telegram Bot"""
        try:
            self.bot = TelegramClient('forward_bot', Config.API_ID, Config.API_HASH)
            self.register_handlers()
        except Exception as e:
            logger.error(f"Error setting up bot: {e}")
    
    def register_handlers(self):
        """Register event handlers untuk bot"""
        
        @self.bot.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await self.handle_start(event)
        
        @self.bot.on(events.NewMessage(pattern='/license'))
        async def license_handler(event):
            await self.handle_license(event)
        
        @self.bot.on(events.NewMessage(pattern='/add_account'))
        async def add_account_handler(event):
            await self.handle_add_account(event)
        
        @self.bot.on(events.NewMessage(pattern='/add_rule'))
        async def add_rule_handler(event):
            await self.handle_add_rule(event)
        
        @self.bot.on(events.NewMessage(pattern='/my_rules'))
        async def my_rules_handler(event):
            await self.handle_my_rules(event)
        
        @self.bot.on(events.NewMessage(pattern='/status'))
        async def status_handler(event):
            await self.handle_status(event)
        
        @self.bot.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            await self.handle_help(event)
    
    async def handle_start(self, event):
        """Handle /start command"""
        user_id = event.sender_id
        welcome_msg = """
🤖 **AUTO FORWARD BOT V2.0 - FIXED**

✨ **Benefit:**
✅ Bot stay 24Jam setiap hari
✅ Bebas forward grup 1-100
✅ Bebas dari Flood Wait panjang  
✅ Tools aman anti banned
✅ Tools aman pakai license key
✅ Tanpa forward ke grup manual
✅ Cocok untuk yang males forward
✅ Bisa 4 Akun tele sekaligus

**Commands:**
/license - Aktivasi license key
/add_account - Tambah akun Telegram
/add_rule - Tambah rule forwarding
/my_rules - Lihat rules aktif
/status - Cek status bot
/help - Bantuan

🔑 **Demo License:** `FWDBOT2024-DEMO123`
        """
        await event.reply(welcome_msg)
    
    async def handle_license(self, event):
        """Handle license activation"""
        user_id = event.sender_id
        message = event.message.text.split()
        
        if len(message) < 2:
            await event.reply("❌ Format: `/license YOUR_LICENSE_KEY`")
            return
        
        license_key = message[1].strip()
        
        if license_key in Config.LICENSE_KEYS:
            if self.db.add_user(user_id, license_key):
                await event.reply(f"✅ **License Activated!**\n\nLicense Key: `{license_key}`\nExpiry: 30 Days\nMax Accounts: 4\n\nSekarang gunakan /add_account untuk menambah akun Telegram.")
            else:
                await event.reply("❌ License key sudah digunakan atau user sudah terdaftar.")
        else:
            await event.reply("❌ License key tidak valid!")
    
    async def handle_add_account(self, event):
        """Handle adding Telegram account"""
        user_id = event.sender_id
        
        # Cek license
        if not self.db.validate_license(user_id, "temp"):
            # Cek apakah user ada di database
            user_accounts = self.db.get_user_accounts(user_id)
            if not user_accounts:
                await event.reply("❌ Anda perlu aktivasi license terlebih dahulu. Gunakan `/license YOUR_KEY`")
                return
        
        user_accounts = self.db.get_user_accounts(user_id)
        if len(user_accounts) >= 4:
            await event.reply("❌ Anda sudah mencapai batas maksimal 4 akun.")
            return
        
        await event.reply("📱 **Tambah Akun Telegram**\n\nSilakan kirim nomor telepon (format internasional):\nContoh: +6281234567890\n\n**Cancel:** ketik /cancel")
        
        @self.bot.on(events.NewMessage(from_users=user_id))
        async def wait_for_phone(phone_event):
            if phone_event.message.text.startswith('/cancel'):
                await phone_event.reply("❌ Proses dibatalkan.")
                self.bot.remove_event_handler(wait_for_phone)
                return
                
            if phone_event.message.text.startswith('/'):
                return
            
            phone = phone_event.message.text.strip()
            
            # Validasi nomor telepon
            if not phone.startswith('+'):
                await phone_event.reply("❌ Format nomor tidak valid. Gunakan format internasional: +6281234567890")
                self.bot.remove_event_handler(wait_for_phone)
                return
            
            # Buat session file
            session_file = f"sessions/{phone.replace('+', '')}.session"
            
            try:
                await phone_event.reply("🔄 **Menyiapkan koneksi...**")
                
                # Setup client baru
                client = TelegramClient(session_file, Config.API_ID, Config.API_HASH)
                await client.connect()
                
                if not await client.is_user_authorized():
                    await phone_event.reply("📲 **Kode Verifikasi**\n\nSilakan check Telegram untuk kode verifikasi, lalu kirim kode tersebut.")
                    
                    # Request code
                    sent_code = await client.send_code_request(phone)
                    
                    @self.bot.on(events.NewMessage(from_users=user_id))
                    async def wait_for_code(code_event):
                        if code_event.message.text.startswith('/cancel'):
                            await code_event.reply("❌ Proses dibatalkan.")
                            self.bot.remove_event_handler(wait_for_code)
                            return
                            
                        code = code_event.message.text.strip()
                        
                        try:
                            await client.sign_in(phone, code, phone_code_hash=sent_code.phone_code_hash)
                            await code_event.reply("✅ **Login Berhasil!**")
                            
                            # Simpan ke database
                            self.db.add_account(user_id, phone, session_file)
                            
                            await code_event.reply(f"✅ **Akun Berhasil Ditambahkan!**\n\nNomor: `{phone}`\nSession: `{session_file}`\n\nSekarang gunakan /add_rule untuk setup forwarding.")
                            
                            # Start forwarding untuk akun ini
                            asyncio.create_task(self.start_forwarding_for_account(client, user_id))
                            
                        except Exception as e:
                            await code_event.reply(f"❌ Error login: {str(e)}")
                        
                        self.bot.remove_event_handler(wait_for_code)
                    
                else:
                    # Already authorized
                    self.db.add_account(user_id, phone, session_file)
                    await phone_event.reply(f"✅ **Akun Berhasil Ditambahkan!**\n\nNomor: `{phone}`\nSession: `{session_file}`\n\nAkun sudah terauthorized sebelumnya.\n\nSekarang gunakan /add_rule untuk setup forwarding.")
                    
                    # Start forwarding untuk akun ini
                    asyncio.create_task(self.start_forwarding_for_account(client, user_id))
                
            except Exception as e:
                await phone_event.reply(f"❌ Error: {str(e)}")
            
            # Hapus handler setelah selesai
            self.bot.remove_event_handler(wait_for_phone)
    
    async def handle_add_rule(self, event):
        """Handle adding forwarding rule"""
        user_id = event.sender_id
        
        # Cek apakah user punya akun
        user_accounts = self.db.get_user_accounts(user_id)
        if not user_accounts:
            await event.reply("❌ Anda belum menambah akun Telegram. Gunakan /add_account terlebih dahulu.")
            return
        
        await event.reply("🔗 **Tambah Forwarding Rule**\n\nFormat: `FROM_CHAT_ID TO_CHAT_ID`\n\nContoh: `-1001234567890 -1009876543210`\n\n**Cara dapat Chat ID:**\n1. Forward pesan dari grup/channel ke @userinfobot\n2. Copy ID yang diberikan\n\n**Cancel:** ketik /cancel")
        
        @self.bot.on(events.NewMessage(from_users=user_id))
        async def wait_for_rule(rule_event):
            if rule_event.message.text.startswith('/cancel'):
                await rule_event.reply("❌ Proses dibatalkan.")
                self.bot.remove_event_handler(wait_for_rule)
                return
                
            if rule_event.message.text.startswith('/'):
                return
            
            try:
                parts = rule_event.message.text.strip().split()
                if len(parts) != 2:
                    await rule_event.reply("❌ Format tidak valid. Gunakan: FROM_CHAT_ID TO_CHAT_ID")
                    self.bot.remove_event_handler(wait_for_rule)
                    return
                    
                from_chat, to_chat = parts
                rule_id = self.db.add_forwarding_rule(user_id, from_chat, to_chat)
                
                await rule_event.reply(f"✅ **Rule Berhasil Ditambahkan!**\n\nID Rule: `{rule_id}`\nFrom: `{from_chat}`\nTo: `{to_chat}`\n\nForwarding akan aktif dalam 1-2 menit.")
                
            except Exception as e:
                await rule_event.reply(f"❌ Error: {str(e)}")
            
            self.bot.remove_event_handler(wait_for_rule)
    
    async def handle_my_rules(self, event):
        """Show user's forwarding rules"""
        user_id = event.sender_id
        rules = self.db.get_forwarding_rules(user_id)
        
        if not rules:
            await event.reply("❌ Anda belum memiliki forwarding rules. Gunakan /add_rule untuk menambah.")
            return
        
        rules_text = "📋 **Your Forwarding Rules:**\n\n"
        for rule_id, from_chat, to_chat in rules:
            rules_text += f"🆔 Rule {rule_id}\nFrom: `{from_chat}`\nTo: `{to_chat}`\n\n"
        
        await event.reply(rules_text)
    
    async def handle_status(self, event):
        """Show bot status"""
        user_id = event.sender_id
        user_accounts = self.db.get_user_accounts(user_id)
        rules = self.db.get_forwarding_rules(user_id)
        
        status_msg = f"""
🤖 **Bot Status**

👤 User ID: `{user_id}`
📱 Akun Terhubung: {len(user_accounts)}/4
🔗 Rules Aktif: {len(rules)}
🕒 Server Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔄 Bot Status: **ONLINE** ✅
        """
        
        await event.reply(status_msg)
    
    async def handle_help(self, event):
        """Show help message"""
        help_msg = """
🆘 **Bantuan Auto Forward Bot**

**Cara Setup:**
1. `/license KEY` - Aktivasi license
2. `/add_account` - Tambah akun Telegram  
3. `/add_rule` - Tambah rule forwarding
4. Bot otomatis mulai forwarding

**Format Chat ID:**
- Grup: `-1001234567890`
- Channel: `-1001234567890`
- User: `123456789`

**Tips:**
- Gunakan akun nomor yang aktif
- Pastikan bot/admin di grup sumber & tujuan
- Jangan terlalu banyak rule sekaligus

**Support:** Contact admin jika ada masalah
        """
        await event.reply(help_msg)
    
    async def start_forwarding_for_account(self, client, user_id):
        """Start forwarding messages for a specific account"""
        try:
            # Tunggu sampai client connected
            if not client.is_connected():
                await client.connect()
            
            rules = self.db.get_forwarding_rules(user_id)
            
            @client.on(events.NewMessage)
            async def forward_handler(event):
                try:
                    if not event.message:  # Skip jika tidak ada message
                        return
                        
                    chat_id = str(event.chat_id)
                    
                    # Cek apakah chat ini ada di rules
                    for rule_id, from_chat, to_chat in rules:
                        if from_chat == chat_id:
                            # Delay anti-flood (random 1-5 detik)
                            await asyncio.sleep(1 + (4 * random.random()))
                            
                            try:
                                # Forward message
                                await client.forward_messages(int(to_chat), event.message)
                                logger.info(f"✅ Forwarded message from {from_chat} to {to_chat}")
                                
                            except Exception as e:
                                logger.error(f"❌ Forward error for {from_chat}->{to_chat}: {e}")
                                # Skip jika error
                            
                except Exception as e:
                    logger.error(f"❌ Handler error: {e}")
            
            logger.info(f"✅ Started forwarding for user {user_id}")
            
            # Keep the client running
            await client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Error in forwarding for account: {e}")
    
    async def start_all_accounts(self):
        """Start all accounts from database - FIXED VERSION"""
        try:
            accounts = self.db.get_all_active_accounts()
            logger.info(f"🔄 Starting {len(accounts)} accounts...")
            
            for user_id, phone, session_file in accounts:
                try:
                    if os.path.exists(session_file):
                        client = TelegramClient(session_file, Config.API_ID, Config.API_HASH)
                        asyncio.create_task(self.start_forwarding_for_account(client, user_id))
                        logger.info(f"✅ Started account: {phone}")
                    else:
                        logger.warning(f"⚠️ Session file not found: {session_file}")
                except Exception as e:
                    logger.error(f"❌ Failed to start account {phone}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error starting accounts: {e}")
    
    async def run(self):
        """Start the bot"""
        try:
            # Buat folder sessions
            os.makedirs('sessions', exist_ok=True)
            
            logger.info("🔄 Starting bot...")
            
            # Start bot
            await self.bot.start(bot_token=self.bot_token)
            logger.info("✅ Bot started successfully!")
            
            # Start all accounts
            await self.start_all_accounts()
            
            logger.info("🤖 Bot is now running! Press Ctrl+C to stop.")
            
            # Keep running
            await self.bot.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")

# ==================== MAIN EXECUTION ====================
async def main():
    bot = AutoForwardBot()
    await bot.run()

if __name__ == "__main__":
    print("""
🤖 AUTO FORWARD BOT V2.0 - FIXED
✨ Benefit:
✅ Bot stay 24Jam setiap hari
✅ Bebas forward grup 1-100  
✅ Bebas dari Flood Wait panjang
✅ Tools aman anti banned
✅ Tools aman pakai license key
✅ Tanpa forward ke grup manual
✅ Cocok untuk yang males forward
✅ Bisa 4 Akun tele sekaligus

🔧 Starting bot...
    """)
    
    # Import random untuk delay
    import random
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")