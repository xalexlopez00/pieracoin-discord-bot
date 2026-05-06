import os
import time
import asyncio
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def _default_account():
    return {"wallet": 0, "bank": 0, "last_daily": 0, "wallet_address": None}

class Economy:
    def __init__(self, db_url: str = None, start_balance: int = 500, daily_reward: int = 100):
        self.start_balance = start_balance
        self.daily_reward = daily_reward
        self.lock = asyncio.Lock()
        self.use_db = bool(db_url)
        
        if self.use_db:
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
                    last_daily INTEGER DEFAULT 0,
                    wallet_address TEXT DEFAULT NULL
                )
            """)
            self.conn.commit()

    def _load_data(self):
        if not os.path.exists(self.data_file): return
        try:
            with open(self.data_file, "r", encoding="utf-8") as h:
                self.data = json.load(h)
        except: self.data = {"users": {}}

    def _save_data(self):
        if not self.use_db:
            with open(self.data_file, "w", encoding="utf-8") as h:
                json.dump(self.data, h, indent=2, ensure_ascii=False)

    async def _ensure_user(self, user_id: int):
        if self.use_db:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                row = cur.fetchone()
                if not row:
                    cur.execute("INSERT INTO users (user_id, wallet, bank, last_daily) VALUES (%s, %s, %s, %s)",
                               (user_id, self.start_balance, 0, 0))
                    self.conn.commit()
                    return {"wallet": self.start_balance, "bank": 0, "last_daily": 0, "wallet_address": None}
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
            return await self._ensure_user(user_id)

    async def update_wallet_address(self, user_id: int, address: str):
        async with self.lock:
            await self._ensure_user(user_id)
            if self.use_db:
                with self.conn.cursor() as cur:
                    cur.execute("UPDATE users SET wallet_address = %s WHERE user_id = %s", (address, user_id))
                    self.conn.commit()
            else:
                self.data["users"][str(user_id)]["wallet_address"] = address
                self._save_data()
            return True

    async def change_wallet(self, user_id: int, amount: int):
        async with self.lock:
            acc = await self._ensure_user(user_id)
            new_val = acc["wallet"] + amount
            if self.use_db:
                with self.conn.cursor() as cur:
                    cur.execute("UPDATE users SET wallet = %s WHERE user_id = %s", (new_val, user_id))
                    self.conn.commit()
            else:
                self.data["users"][str(user_id)]["wallet"] = new_val
                self._save_data()
            return True

    # Los métodos deposit, withdraw, transfer y claim_daily se mantienen iguales 
    # pero asegurando que usen la lógica de self.use_db correctamente.
