import os
import asyncio
import random
import re
import time
from datetime import datetime

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.types import ChannelParticipantsAdmins
from dotenv import load_dotenv

# ================== ENV ==================
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID"))

SESSION_NAME = "support_userbot"

# ================== COOLDOWN ==================
GROUP_COOLDOWN_SECONDS = 600  # 10 minutes
GROUP_LAST_ALERT = {}        # {group_id: timestamp}

# ================== KEYWORDS ==================
URGENT_KEYWORDS = [
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

MILD_KEYWORDS = [
    "help", "support", "question", "anyone", "how to",
    "need help", "assistance", "issue"
]

URGENT_RE = re.compile("|".join(re.escape(k) for k in URGENT_KEYWORDS), re.I)
MILD_RE = re.compile("|".join(re.escape(k) for k in MILD_KEYWORDS), re.I)

# ================== CLIENT ==================
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ================== HELPERS ==================


def generate_ticket():
    return random.randint(100000, 999999)


async def is_admin(chat, user_id):
    try:
        async for admin in client.iter_participants(chat, filter=ChannelParticipantsAdmins):
            if admin.id == user_id:
                return True
    except Exception:
        pass
    return False


def score_priority(text: str):
    if URGENT_RE.search(text):
        return "🔴 URGENT"
    if MILD_RE.search(text):
        return "🟡 MILD"
    return None


def group_on_cooldown(group_id: int) -> bool:
    now = time.time()
    last = GROUP_LAST_ALERT.get(group_id, 0)
    return (now - last) < GROUP_COOLDOWN_SECONDS

# ================== HANDLER ==================


@client.on(events.NewMessage)
async def handler(event):
    if not event.is_group:
        return

    sender = await event.get_sender()
    chat = await event.get_chat()

    if not sender or sender.bot:
        return

    if await is_admin(chat, sender.id):
        return

    text = event.raw_text or ""
    priority = score_priority(text)

    if not priority:
        return

    group_id = event.chat_id

    # ---- GROUP COOLDOWN CHECK ----
    if group_on_cooldown(group_id):
        return

    ticket = generate_ticket()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # ---- FORWARD ORIGINAL MESSAGE ----
    try:
        await event.forward_to(OWNER_ID)
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
        return
    except Exception:
        return

    # ---- METADATA MESSAGE ----
    meta = f"""📌 ISSUE SUMMARY

Priority: {priority}
Ticket: #{ticket}
Group: {getattr(chat, 'title', 'Unknown')}
User: @{sender.username or sender.first_name}
User ID: {sender.id}
Time: {now}
"""

    try:
        await client.send_message(OWNER_ID, meta)
        GROUP_LAST_ALERT[group_id] = time.time()  # set cooldown
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
    except Exception:
        pass

# ================== RUN ==================
if __name__ == "__main__":
    print("🚀 Support Monitor running (PRIORITY + FORWARD + GROUP COOLDOWN)")
    client.start()
    client.run_until_disconnected()
