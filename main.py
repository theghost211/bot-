import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View
import json
import datetime
from flask import Flask
from threading import Thread

# ===== إعدادات أساسية =====
TOKEN = "MTM3NDEyNjA4MTQwOTU0ODQxOA.GY4l0P.60Vswa1i7z2qP8XpfDCzLYHxv6RHFp1dPiZsmw"    
OWNER_ID = 1358059903310369000

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

CREDIT_FILE = "credits.json"
RANK_FILE = "ranks.json"
DAILY_FILE = "daily.json"

RANKS = {
    "Normal": {"price": 0, "daily": 1000},
    "Bronze": {"price": 50000, "daily": 25000},
    "Silver": {"price": 900000, "daily": 500000},
    "Diamond X": {"price": 90000000, "daily": 50000000},
}

# ===== دوال التعامل مع الملفات =====
def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def format_number(n):
    if n >= 1_000_000_000_000_000:
        return f"{n / 1_000_000_000_000_000:.2f}Q"
    elif n >= 1_000_000_000_000:
        return f"{n / 1_000_000_000_000:.2f}T"
    elif n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.2f}K"
    else:
        return str(n)

# ===== أحداث البوت =====
@bot.event
async def on_ready():
    if not getattr(bot, "synced", False):
        await tree.sync()
        bot.synced = True
    print(f"✅ Logged in as {bot.user}")

# ===== أوامر البوت =====
@tree.command(name="balance", description="عرض رصيدك أو رصيد شخص")
@app_commands.describe(member="الشخص الذي تريد رؤية رصيده")
async def balance(interaction: discord.Interaction, member: discord.Member = None):
    user = member or interaction.user
    credits = load_json(CREDIT_FILE)
    balance = credits.get(str(user.id), 0)
    await interaction.response.send_message(f"💰 رصيد {user.mention}: `{format_number(balance)}` كريدت")

@tree.command(name="give", description="تحويل كريدت لشخص آخر")
@app_commands.describe(member="الشخص الذي تريد التحويل له", amount="المبلغ")
async def give(interaction: discord.Interaction, member: discord.Member, amount: int):
    sender_id = str(interaction.user.id)
    receiver_id = str(member.id)

    if amount <= 0 or member.id == interaction.user.id:
        await interaction.response.send_message("❌ العملية غير صالحة.")
        return

    credits = load_json(CREDIT_FILE)
    sender_balance = credits.get(sender_id, 0)

    if sender_balance < amount:
        await interaction.response.send_message("❌ لا تملك كريدت كافي.")
        return

    credits[sender_id] = sender_balance - amount
    credits[receiver_id] = credits.get(receiver_id, 0) + amount
    save_json(CREDIT_FILE, credits)

    await interaction.response.send_message(
        f"✅ تم تحويل `{format_number(amount)}` كريدت إلى {member.mention}.")

@tree.command(name="add_money", description="إضافة كريدت (خاص بالمالك)")
@app_commands.describe(member="الشخص", amount="المبلغ")
async def add_money(interaction: discord.Interaction, member: discord.Member, amount: int):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ هذا الأمر للمالك فقط.")
        return

    if amount <= 0:
        await interaction.response.send_message("❌ المبلغ غير صالح.")
        return

    credits = load_json(CREDIT_FILE)
    user_id = str(member.id)
    credits[user_id] = credits.get(user_id, 0) + amount
    save_json(CREDIT_FILE, credits)

    await interaction.response.send_message(
        f"✅ تمت إضافة `{format_number(amount)}` كريدت لـ {member.mention}.")

@tree.command(name="daily", description="احصل على مكافأتك اليومية حسب رتبتك")
async def daily(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    credits = load_json(CREDIT_FILE)
    ranks = load_json(RANK_FILE)
    daily_log = load_json(DAILY_FILE)

    now = datetime.datetime.utcnow()
    last_claim = daily_log.get(user_id)

    if last_claim:
        last_time = datetime.datetime.fromisoformat(last_claim)
        elapsed = now - last_time
        if elapsed.total_seconds() < 86400:
            remaining = datetime.timedelta(seconds=86400) - elapsed
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes = remainder // 60
            await interaction.response.send_message(
                f"⏳ لا يمكنك أخذ اليومية الآن. الرجاء الانتظار `{hours}` ساعة و `{minutes}` دقيقة.")
            return

    rank = ranks.get(user_id, "Normal")
    reward = RANKS.get(rank, RANKS["Normal"])['daily']
    credits[user_id] = credits.get(user_id, 0) + reward
    daily_log[user_id] = now.isoformat()

    save_json(CREDIT_FILE, credits)
    save_json(DAILY_FILE, daily_log)

    await interaction.response.send_message(
        f"🎁 أخذت `{format_number(reward)}` كريدت كمكافأة يومية لرتبة `{rank}`.")

@tree.command(name="shop", description="عرض المتجر والرتب المتاحة")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 المتجر - الرتب المتاحة", color=0x00ffcc)
    for rank, info in RANKS.items():
        embed.add_field(
            name=f"🏷️ {rank}",
            value=f"💵 السعر: `{format_number(info['price'])}`\n🎁 اليومية: `{format_number(info['daily'])}` كريدت",
            inline=False
        )
    await interaction.response.send_message(embed=embed)

@tree.command(name="buy", description="شراء رتبة من المتجر (باختيار)")
async def buy(interaction: discord.Interaction):
    ranks = load_json(RANK_FILE)
    credits = load_json(CREDIT_FILE)
    user_id = str(interaction.user.id)

    options = []
    for rank, data in RANKS.items():
        label = f"{rank} - {format_number(data['price'])} كريدت"
        description = f"مكافأة يومية: {format_number(data['daily'])}"
        options.append(discord.SelectOption(label=rank, description=description, value=rank))

    class RankSelectView(View):
        @discord.ui.select(placeholder="اختر رتبة للشراء", options=options)
        async def select_callback(self, interaction2: discord.Interaction, select: Select):
            selected_rank = select.values[0]
            price = RANKS[selected_rank]['price']
            balance = credits.get(user_id, 0)

            if balance < price:
                await interaction2.response.send_message(
                    f"❌ تحتاج `{format_number(price)}` كريدت لشراء `{selected_rank}`.")
                return

            credits[user_id] = balance - price
            ranks[user_id] = selected_rank
            save_json(CREDIT_FILE, credits)
            save_json(RANK_FILE, ranks)

            await interaction2.response.send_message(
                f"✅ تم شراء رتبة `{selected_rank}` وتم خصم `{format_number(price)}` كريدت من رصيدك.")

    await interaction.response.send_message("🎯 اختر الرتبة التي تريد شراءها:", view=RankSelectView())

@tree.command(name="top", description="عرض أغنى 10 أشخاص")
async def top(interaction: discord.Interaction):
    credits = load_json(CREDIT_FILE)
    sorted_users = sorted(credits.items(), key=lambda x: x[1], reverse=True)[:10]

    embed = discord.Embed(title="🏆 أغنى 10 أعضاء", color=0xf1c40f)
    for index, (user_id, amount) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            embed.add_field(name=f"#{index} {user.name}", value=f"💰 {format_number(amount)} كريدت", inline=False)
        except:
            continue

    await interaction.response.send_message(embed=embed)

# ===== تشغيل Flask للـ UptimeRobot أو Replit =====
app = Flask('')

@app.route('/')
def home():
    return "I'm Alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

keep_alive()
bot.run(TOKEN)
