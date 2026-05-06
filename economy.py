import json
import os
import time
import asyncio

DEFAULT_DATA = {"users": {}, "history": []}


def _default_account():
    return {"wallet": 0, "bank": 0, "last_daily": 0}


class Economy:
    def __init__(self, path: str, start_balance: int = 500, daily_reward: int = 100):
        self.path = path
        self.start_balance = start_balance
        self.daily_reward = daily_reward
        self.lock = asyncio.Lock()
        self.data = self._load_data()

    def _load_data(self):
        if not os.path.exists(self.path):
            return DEFAULT_DATA.copy()
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except ValueError:
            return DEFAULT_DATA.copy()

    async def _save_data(self):
        async with self.lock:
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False)

    async def _ensure_user(self, user_id: int):
        uid = str(user_id)
        if uid not in self.data["users"]:
            self.data["users"][uid] = _default_account()
            self.data["users"][uid]["wallet"] = self.start_balance
            await self._save_data()
        return self.data["users"][uid]

    async def get_account(self, user_id: int):
        async with self.lock:
            account = await self._ensure_user(user_id)
            return {"wallet": account["wallet"], "bank": account["bank"], "last_daily": account["last_daily"]}

    async def change_wallet(self, user_id: int, amount: int):
        async with self.lock:
            account = await self._ensure_user(user_id)
            account["wallet"] += amount
            await self._save_data()
            return account

    async def change_bank(self, user_id: int, amount: int):
        async with self.lock:
            account = await self._ensure_user(user_id)
            account["bank"] += amount
            await self._save_data()
            return account

    async def deposit(self, user_id: int, amount: int):
        async with self.lock:
            account = await self._ensure_user(user_id)
            if account["wallet"] < amount:
                return False, "No tienes suficientes monedas en wallet para depositar."
            account["wallet"] -= amount
            account["bank"] += amount
            await self._save_data()
            return True, f"Has depositado {amount} PieraCoin en tu banco."

    async def withdraw(self, user_id: int, amount: int):
        async with self.lock:
            account = await self._ensure_user(user_id)
            if account["bank"] < amount:
                return False, "No tienes suficientes monedas en el banco para retirar."
            account["bank"] -= amount
            account["wallet"] += amount
            await self._save_data()
            return True, f"Has retirado {amount} PieraCoin a tu wallet."

    async def transfer(self, sender_id: int, receiver_id: int, amount: int):
        async with self.lock:
            sender = await self._ensure_user(sender_id)
            receiver = await self._ensure_user(receiver_id)
            if sender["wallet"] < amount:
                return False, "No tienes suficientes monedas en wallet para enviar."
            sender["wallet"] -= amount
            receiver["wallet"] += amount
            await self._save_data()
            return True, f"Has enviado {amount} PieraCoin a <@{receiver_id}>."

    async def claim_daily(self, user_id: int):
        async with self.lock:
            account = await self._ensure_user(user_id)
            now = int(time.time())
            if now - account["last_daily"] < 24 * 60 * 60:
                remaining = 24 * 60 * 60 - (now - account["last_daily"])
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                return False, f"Ya reclamaste tu daily. Vuelve en {hours}h {minutes}m."
            account["wallet"] += self.daily_reward
            account["last_daily"] = now
            await self._save_data()
            return True, f"Reclamaste tu daily y obtuviste {self.daily_reward} PieraCoin."

    async def get_leaderboard(self, size: int = 10):
        async with self.lock:
            entries = []
            for uid, account in self.data["users"].items():
                total = account["wallet"] + account["bank"]
                entries.append((uid, total))
            entries.sort(key=lambda item: item[1], reverse=True)
            return entries[:size]
