import os
import time
import asyncio
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def _default_account():
    return {"wallet": 0, "bank": 0, "last_daily": 0}

class Economy:
    def __init__(self, db_url: str = None, start_balance: int = 500, daily_reward: int = 100):
        self.start_balance = start_balance
        self.daily_reward = daily_reward
        self.lock = asyncio.Lock()
        self.use_db = bool(db_url)
        
        if self.use_db:
            # Conexión persistente
            self.conn = psycopg2.connect(db_url)
            self._create_table()
        else:
            self.data = {"users": {}}
            self.data_file = "economy.json"
            self._load_data()

    def _create_table(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    wallet INTEGER DEFAULT 0,
                    bank INTEGER DEFAULT 0,
                    last_daily INTEGER DEFAULT 0
                )
            """)
            self.conn.commit()

    def _load_data(self):
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, "r", encoding="utf-8") as handle:
                self.data = json.load(handle)
        except (ValueError, json.JSONDecodeError):
            self.data = {"users": {}}

    def _save_data(self):
        if not self.use_db:
            with open(self.data_file, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False)

    async def _ensure_user(self, user_id: int):
        # Nota: El lock se maneja en los métodos públicos para evitar deadlocks
        if self.use_db:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                row = cur.fetchone()
                if not row:
                    cur.execute(
                        "INSERT INTO users (user_id, wallet, bank, last_daily) VALUES (%s, %s, %s, %s)",
                        (user_id, self.start_balance, 0, 0)
                    )
                    self.conn.commit()
                    return {"user_id": user_id, "wallet": self.start_balance, "bank": 0, "last_daily": 0}
                return dict(row)
        else:
            uid = str(user_id)
            if uid not in self.data["users"]:
                self.data["users"][uid] = _default_account()
                self.data["users"][uid]["wallet"] = self.start_balance
                self._save_data()
            return self.data["users"][uid]

    async def get_account(self, user_id: int):
        async with self.lock:
            account = await self._ensure_user(user_id)
            return account

    async def change_wallet(self, user_id: int, amount: int):
        async with self.lock:
            account = await self._ensure_user(user_id)
            new_wallet = account["wallet"] + amount
            
            if self.use_db:
                with self.conn.cursor() as cur:
                    cur.execute("UPDATE users SET wallet = %s WHERE user_id = %s", (new_wallet, user_id))
                    self.conn.commit()
            else:
                self.data["users"][str(user_id)]["wallet"] = new_wallet
                self._save_data()
            return True

    async def deposit(self, user_id: int, amount: int):
        async with self.lock:
            account = await self._ensure_user(user_id)
            if account["wallet"] < amount:
                return False, "No tienes suficientes monedas en wallet."
            
            new_wallet = account["wallet"] - amount
            new_bank = account["bank"] + amount
            
            if self.use_db:
                with self.conn.cursor() as cur:
                    cur.execute("UPDATE users SET wallet = %s, bank = %s WHERE user_id = %s",
                                (new_wallet, new_bank, user_id))
                    self.conn.commit()
            else:
                uid = str(user_id)
                self.data["users"][uid]["wallet"] = new_wallet
                self.data["users"][uid]["bank"] = new_bank
                self._save_data()
            return True, f"Has depositado {amount} PieraCoin."

    async def withdraw(self, user_id: int, amount: int):
        async with self.lock:
            account = await self._ensure_user(user_id)
            if account["bank"] < amount:
                return False, "No tienes suficiente en el banco."
            
            new_wallet = account["wallet"] + amount
            new_bank = account["bank"] - amount
            
            if self.use_db:
                with self.conn.cursor() as cur:
                    cur.execute("UPDATE users SET wallet = %s, bank = %s WHERE user_id = %s",
                                (new_wallet, new_bank, user_id))
                    self.conn.commit()
            else:
                uid = str(user_id)
                self.data["users"][uid]["wallet"] = new_wallet
                self.data["users"][uid]["bank"] = new_bank
                self._save_data()
            return True, f"Has retirado {amount} PieraCoin."

    async def transfer(self, sender_id: int, receiver_id: int, amount: int):
        async with self.lock:
            sender = await self._ensure_user(sender_id)
            receiver = await self._ensure_user(receiver_id)
            
            if sender["wallet"] < amount:
                return False, "No tienes suficiente dinero."
            
            new_sender_wallet = sender["wallet"] - amount
            new_receiver_wallet = receiver["wallet"] + amount
            
            if self.use_db:
                with self.conn.cursor() as cur:
                    cur.execute("UPDATE users SET wallet = %s WHERE user_id = %s", (new_sender_wallet, sender_id))
                    cur.execute("UPDATE users SET wallet = %s WHERE user_id = %s", (new_receiver_wallet, receiver_id))
                    self.conn.commit()
            else:
                self.data["users"][str(sender_id)]["wallet"] = new_sender_wallet
                self.data["users"][str(receiver_id)]["wallet"] = new_receiver_wallet
                self._save_data()
            return True, f"Has enviado {amount} PieraCoin a <@{receiver_id}>."

    async def claim_daily(self, user_id: int):
        async with self.lock:
            account = await self._ensure_user(user_id)
            now = int(time.time())
            
            if now - account["last_daily"] < 86400:
                remaining = 86400 - (now - account["last_daily"])
                return False, f"Vuelve en {remaining // 3600}h {(remaining % 3600) // 60}m."
            
            new_wallet = account["wallet"] + self.daily_reward
            if self.use_db:
                with self.conn.cursor() as cur:
                    cur.execute("UPDATE users SET wallet = %s, last_daily = %s WHERE user_id = %s",
                                (new_wallet, now, user_id))
                    self.conn.commit()
            else:
                uid = str(user_id)
                self.data["users"][uid]["wallet"] = new_wallet
                self.data["users"][uid]["last_daily"] = now
                self._save_data()
            return True, f"¡Reclamaste {self.daily_reward} PieraCoin!"

    async def get_leaderboard(self, size: int = 10):
        if self.use_db:
            with self.conn.cursor() as cur:
                cur.execute("SELECT user_id, (wallet + bank) as total FROM users ORDER BY total DESC LIMIT %s", (size,))
                rows = cur.fetchall()
                return [(str(row[0]), row[1]) for row in rows]
        else:
            entries = [(uid, acc["wallet"] + acc["bank"]) for uid, acc in self.data["users"].items()]
            entries.sort(key=lambda x: x[1], reverse=True)
            return entries[:size]
