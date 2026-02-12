import os
import re
import asyncio
import random
import time
from datetime import datetime

from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.errors import FloodWaitError
from dotenv import load_dotenv

# ================== ENV ==================
load_dotenv()

OWNER_ID = int(os.getenv("OWNER_ID"))

WATCHERS = [
    {
        "api_id": int(os.getenv("API_ID_1")),
        "api_hash": os.getenv("API_HASH_1"),
        "phone": os.getenv("PHONE_1"),
        "session": os.getenv("SESSION_1"),
    },
    {
        "api_id": int(os.getenv("API_ID_2")),
        "api_hash": os.getenv("API_HASH_2"),
        "phone": os.getenv("PHONE_2"),
        "session": os.getenv("SESSION_2"),
    },
    {
        "api_id": int(os.getenv("API_ID_3")),
        "api_hash": os.getenv("API_HASH_3"),
        "phone": os.getenv("PHONE_3"),
        "session": os.getenv("SESSION_3"),
    },
]

# ================== KEYWORDS ==================
KEYWORDS = [
    "swap",
    "transfer",
    "transaction",
    "deposit",
    "withdraw",
    "mint",
    "stake",
    "unstake",
    "claim",
    "failed",
    "stuck",
    "pending",
    "reverted",
    "not received",
    "error",
    "timeout",
    "disappeared",
    "metamask",
    "trust wallet",
    "coinbase",
    "binance",
    "kraken",
    "kucoin",
    "cex",
    "dex",
    "nft",
    "bridge",
    "help",
    "support",
    "urgent",
    "anyone",
    "how to fix",
    "assistance",
    "issue",
    "problem",
    "feedback",

    # Transactions
    "transaction failed",
    "tx failed",
    "transfer failed",
    "transaction error",
    "transaction stuck",
    "tx stuck",
    "pending transaction",
    "not confirmed",
    "tx not found",
    "transaction reverted",
    "failed to send tx",

    # Swaps & DEX
    "swap failed",
    "swap error",
    "swap stuck",
    "cannot swap",
    "swap pending",
    "dex error",
    "liquidity issue",
    "slippage too high",
    "swap rejected",
    "insufficient funds for swap",
    "pair not found",

    # Deposits & Withdrawals
    "deposit not received",
    "withdrawal failed",
    "withdraw stuck",
    "withdraw pending",
    "funds not received",
    "deposit failed",
    "cannot deposit",
    "cannot withdraw",
    "withdraw rejected",

    # Missing funds/balance
    "tokens not received",
    "coins missing",
    "balance not updated",
    "missing funds",
    "lost funds",
    "wallet empty",
    "funds disappeared",

    # Gas/network issues
    "gas fee too high",
    "out of gas",
    "network congested",
    "rpc error",
    "nonce too low",
    "replacement transaction underpriced",
    "insufficient gas",
    "network timeout",
    "transaction pending too long",

    # Wallet issues
    "wallet not connecting",
    "wallet error",
    "cannot connect wallet",
    "wallet issue",
    "metamask error",
    "trust wallet error",
    "wallet disconnected",
    "wrong network",
    "unsupported chain",

    # Bridges / cross-chain
    "bridge stuck",
    "bridge failed",
    "cross chain issue",
    "tokens stuck on bridge",
    "bridge pending",
    "bridge error",

    # CEX / centralized exchange issues
    "exchange issue",
    "binance issue",
    "coinbase issue",
    "kucoin issue",
    "bybit issue",
    "kraken issue",
    "cex deposit failed",
    "cex withdrawal failed",
    "cex transfer error",

    # NFT / smart contract issues
    "nft transfer failed",
    "mint failed",
    "contract error",
    "smart contract reverted",
    "cannot claim nft",
    "nft stuck",

    # DeFi / staking/farming
    "stake failed",
    "unstake failed",
    "yield farming issue",
    "rewards not received",
    "pool error",
    "cannot withdraw stake",

    # Urgency/help indicators
    "please help",
    "any solution",
    "need help",
    "urgent",
    "anyone help",
    "support needed",
    "issue with transaction",
    "how to fix",
    "help me",
    "error occurred",
    "cannot resolve",

    # Status / Errors
    "failed",
    "stuck",
    "pending",
    "reverted",
    "not received",
    "error",
    "timeout",
    "disappeared",

    # Platforms / Wallets
    "metamask",
    "trust wallet",
    "coinbase",
    "binance",
    "kraken",
    "kucoin",
    "cex",
    "dex",
    "nft",
    "bridge"
]

KEYWORD_RE = re.compile("|".join(re.escape(k) for k in KEYWORDS), re.I)

# ================== COOLDOWN ==================
CONTACTED = set()

# ================== LOGGING ==================


def log(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

# ================== ADMIN CHECK ==================


async def is_admin(client, chat, user_id):
    try:
        async for p in client.iter_participants(chat, filter=ChannelParticipantsAdmins):
            if p.id == user_id:
                return True
    except Exception:
        pass
    return False

# ================== HANDLER FACTORY ==================


def register_handler(client, watcher_name):

    @client.on(events.NewMessage)
    async def handler(event):
        if not event.is_group:
            return

        chat = await event.get_chat()
        sender = await event.get_sender()
        text = event.raw_text or ""

        if not sender or sender.bot:
            return

        if sender.id in CONTACTED:
            log(f"🟡 SKIP cooldown | {chat.title}")
            return

        if not KEYWORD_RE.search(text):
            log(f"🟡 SKIP no keyword | {chat.title}")
            return

        if await is_admin(client, chat, sender.id):
            log(f"🟡 SKIP admin | {chat.title}")
            return

        ticket = random.randint(100000, 999999)

        try:
            await client.forward_messages(
                OWNER_ID,
                event.message
            )
            await client.send_message(
                OWNER_ID,
                f"📍 Group: {chat.title}\n🎟 Ticket #{ticket}"
            )

            CONTACTED.add(sender.id)

            log(f"📩 FORWARDED from {chat.title} | {watcher_name} | #{ticket}")

        except FloodWaitError as e:
            log(f"⏳ FloodWait {e.seconds}s")
            await asyncio.sleep(e.seconds)

        except Exception as e:
            log(f"❌ Forward failed: {e}")

# ================== START WATCHERS ==================


async def main():
    clients = []

    for i, w in enumerate(WATCHERS, start=1):
        client = TelegramClient(
            w["session"],
            w["api_id"],
            w["api_hash"],
            device_model="Support Watcher",
            system_version="Railway",
            app_version="1.0",
        )

        await client.start(phone=w["phone"])
        register_handler(client, f"session_{i}")
        clients.append(client)

        log(f"✅ Active: session_{i}")

    log("🚀 All watchers running")
    await asyncio.gather(*(c.run_until_disconnected() for c in clients))

# ================== ENTRY ==================
if __name__ == "__main__":
    asyncio.run(main())
