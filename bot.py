# -*- coding: utf-8 -*-
"""
Discord Protection Bot
- Slash commands
- Profanity/insult filter (Arabic + English + obfuscated variants)
- Ban/Kick protection
- Bot-add protection
- Role update/delete protection
Author: ChatGPT
"""

import re
import json
import asyncio
from datetime import timedelta
from typing import List, Set

import discord
from discord.ext import commands
from discord import app_commands

# ====================== CONFIG ======================
# 1) Rename config.example.json -> config.json and fill TOKEN & ALERT_CHANNEL_ID
# 2) Or set DISCORD_TOKEN environment variable.
import os
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
CONFIG = {}
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)

TOKEN = os.getenv("DISCORD_TOKEN") or CONFIG.get("TOKEN", "PUT_YOUR_TOKEN_HERE")
ALERT_CHANNEL_ID = int(CONFIG.get("ALERT_CHANNEL_ID", 123456789012345678))

# IDs allowed explicitly (optional)
ALLOWED_USERS: Set[int] = {
    1377796809170354336,  # allowed user 1
    1358059903310369000,  # allowed user 2
}

# POWER ROLES (role IDs with power to use slash commands)
POWER_ROLES: Set[int] = {
    1398790164414857236,  # Owner
    1398790109536452689,  # Co-Owner / سو اونر
    1398789842468470805,  # Manager
    1398789570824241262,  # Admin
    1398789410912469172,  # Jr Admin
}

# ====================== NORMALIZATION ======================
# Strong normalization map (requested set)
CHAR_MAP = {
    "0": "o", "1": "i", "2": "z", "3": "e", "4": "a", "5": "s",
    "6": "g", "7": "t", "8": "b", "9": "g",
    "@": "a", "$": "s", "!": "i", "*": "", "#": "h",
    "+": "t", "?": "", ".": "", "_": "", "-": "", "ـ": "",
    "¡": "i", "¿": "?", "€": "e", "¥": "y", "¢": "c", "£": "l",
    "ß": "ss", "æ": "ae", "œ": "oe",
}

# Also strip spaces and diacritics-like characters
STRIP_CHARS = "".join([
    "\u200b", "\u200c", "\u200d", "\u200e", "\u200f",  # zero-width and RLM/LRM
    " ", "\t", "\n", "\r",
])

ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06dc\u06df-\u06e8\u06ea-\u06ed]")

def normalize_text(text: str) -> str:
    t = text.lower()
    # replace char map
    for k, v in CHAR_MAP.items():
        t = t.replace(k, v)
    # remove diacritics
    t = ARABIC_DIACRITICS.sub("", t)
    # remove non [a-z + Arabic block] (keep Arabic letters \u0600-\u06FF)
    t = re.sub(r"[^a-z\u0600-\u06FF]+", "", t)
    return t

# ====================== BAD WORDS (BIG) ======================
# The following list merges Arabic + English + many obfuscated variants.
# You can add/remove using slash commands at runtime (in-memory).
BAD_WORDS: List[str] = [
    # --- English base and variants ---
    "fuck","f*ck","f u c k","fuk","fck","fuuck","fuuuuck","fucker","motherfucker","mf","fcking",
    "shit","sh*t","sh1t","s h i t","shiiiit","bullshit","crap","damn","bitch","b!tch","b1tch",
    "ass","a s s","a$$","asshole","a s s h o l e","a55hole","bastard","b@stard",
    "slut","slutt","s l u t","sluut","whore","wh0re","w h o r e",
    "nigger","n1gger","nigga","n1gga","nigg@","n1gg@",
    "cunt","dick","d1ck","diick","d!ck","d i c k",
    "cock","c0ck","c0k","c o c k","pussy","pussi","pusy","p u s s y",
    "cum","cumm","c u m","anal","a n a l","rape","r@pe","r4pe",
    "porn","p0rn","p o r n","pr0n","sex","s3x","s e x",
    "gay","g4y","g a y","lesbian","l3sbian","lezbian",
    "jerk","jerking","wank","wanking","orgasm","deepthroat","blowjob","handjob","spank","milf","teen porn","hardcore",
    "dumbass","idiot","moron","retard","loser","trash","scum","fuckface","shitface",
    "f@ck","sh1t","b1tch","a55","d1ck","p0rn","s3x","g4y","l3sbian","l0ser","n00b",
    "go to hell","eat shit","son of a bitch","son of a whore","your mother is a whore","damn you",
    # --- Extra English insults ---
    "douche","douchebag","twat","prick","wanker","git","bollocks","bugger","arsehole","tosser","muppet","plonker","knobhead",
    # --- Arabic base and variants ---
    "كس","ك س","كُس","كْس","كسخت","كسختك","كسختكم","كسخة","كسختها","كسها",
    "كسمك","كسمكم","كسمه","كسمها","كسموك","كسموني","كسامك","كس امك","كس امها","كس امكم",
    "زب","ز ب","زُب","زْب","زبالة","زباله","زباح","زبال","زبوني","زباني",
    "طيز","ط ي ز","طــيــز","طيزان","طيزتك","طيزكم","طيزي","طيزك",
    "يلعن","يلعن ابو","يلعن ام","يلعن حياتك","يلعن وجهك","يلعن جدك","يلعن جدودك","يلعن امك","يلعن امها","يلعن امكم",
    "قحبة","قحـبة","قحــبة","قحْبة","قحِبة","قحبة امك","قحبة امها","قحبة امكم",
    "شرموطة","شرمـوطة","شرمــوطة","شرموط","شرموطت","شرموطتك","شرموطكم",
    "متناك","متـناك","متنــاك","متناك امك","متناكك",
    "لوطي","ل و ط ي","لواطي","لوطيه","لوطية","لواط",
    "منيك","منيـك","منيــك","منيكة","منيكتك","منيكم",
    "لعنة","لعنـة","لعنــة","لعن الله","لعنة عليك","لعنة ربك",
    "تفوو","تف","تفو","تفو عليك","تفو عليكم",
    "حيوان","حيوانه","حيوانات","ياحيوان","يا حيوان",
    "كلب","كلبة","كلاب","ياكلب","كلبوس","كلبو","كلب ابن كلب","كلب ابن العاهرة",
    "خنزير","خنازير","ياخنزير","خنزيرة","خنزيرك",
    "ابن الكلب","ابن حيوان","ابن المتناك","ابن الشرموطة","ابن الشرموط",
    "عرص","عرصه","ع ر ص","عرصان","عرصتك","عرصكم",
    "زق","زقرت","زقرتك","زقرتكم","ازق",
    "قذر","قذرة","قذرين","قذارة",
    "شرموط","شرموطة","شرموت","شرموطه",
    "تناك","تنك","تناك امك",
    "حمار","حمير","حمارة","حمارك",
    "بغل","بغال","بغلتك",
    "حقير","حقيره","حقير جدا","سافل","سافلة","سافلين",
    "خرا","خراء","خرابيط",
    "خسيس","خسيسة",
    "وادحمار","وادحمارك",
    "أهبل","هبيل","هبيلة",
    "أبله","بلحة","بلح",
    "أعرص","لعين","لعينة","لعائن",
    "صعلوك","صعاليك","صعلوكه",
    "غباء","غباءه","غباءتك",
    "أخرق","أخرقه",
    "كذاب","منافق","حقود","حقد","جبان","خائن","مجرم","لص",
    "متسخ","وسخ","نتن","متعفن","مقرف",
    # Extra Arabic insult set
    "يا حيوان","يا كلب","يا قذر","يا نذل","يا حقير","يا نجس","يا زفت","يا عديم","يا تيس","يا حثالة","يا بليد",
    "يا تافه","يا مسكين","يا منحط","قليل الأدب","يا ساقط","يا رخيص","يا غبي","يا مجنون","يا مطي","يا معفن",
    "انقلع","وسخ وجهك","يا شرموط","يا شرموطة","يا ابن الكلب","يا ابن حمار","يا ابن عاهرة","يا مخنث","يا طرطور",
    "يا لقيط","يا وصخة","يا نكرة","يا قمامة","يا زبالة","يا مسعور","يا خنزير","يا خنزيرة","يا كلبة","يا كلبة الشارع",
]

# Precompute normalized bad words for fast contains
BAD_WORDS_NORM = set()
for w in BAD_WORDS:
    BAD_WORDS_NORM.add(normalize_text(w))

def is_bad_word_detected(text: str) -> bool:
    cleaned = normalize_text(text)
    # Also collapse repeated characters like "coooool" -> "cool"
    cleaned = re.sub(r"(.)\1{2,}", r"\1\1", cleaned)
    for bad in BAD_WORDS_NORM:
        if bad and bad in cleaned:
            return True
    return False

# ====================== BOT SETUP ======================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
protected_channels: Set[int] = set()  # channels where profanity filter is active

def is_authorized(user: discord.abc.User | discord.Member) -> bool:
    if isinstance(user, discord.Member):
        if any(role.id in POWER_ROLES for role in user.roles):
            return True
    return user.id in ALLOWED_USERS

async def send_alert(guild: discord.Guild, message: str):
    ch = guild.get_channel(ALERT_CHANNEL_ID)
    if ch:
        await ch.send(message)

# ====================== EVENTS ======================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot ready as {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id in protected_channels:
        if is_bad_word_detected(message.content):
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            try:
                duration = timedelta(hours=2)
                await message.author.timeout(duration, reason="Profanity / سب")
            except Exception:
                pass
            embed = discord.Embed(
                title="⚠️ تم إعطاؤك تايم أوت",
                description=(
                    f"⛔ {message.author.mention} تم إعطاؤك **تايم أوت ساعتين** بسبب استخدام كلمات ممنوعة/سب.\n"
                    f"رجاءً التزم بقوانين السيرفر. النظام يلتقط حتى الكلمات المشفّرة مثل sh1t، f*ck، ك ل ب، إلخ."
                ),
                color=discord.Color.red(),
            )
            try:
                await message.channel.send(embed=embed)
            except Exception:
                pass
            await send_alert(message.guild, f"⚠️ {message.author.mention} حاول استخدام كلمات ممنوعة في {message.channel.mention}.")
    await bot.process_commands(message)

# --- Ban protection ---
@bot.event
async def on_member_ban(guild: discord.Guild, user: discord.User):
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.target.id == user.id and not is_authorized(entry.user):
            try:
                await guild.unban(user, reason="Protection: unauthorized ban")
            except Exception:
                pass
            await send_alert(guild, f"🚨 محاولة **Ban** غير مصرح بها من {entry.user.mention} ضد {user.mention}. تم إلغاء الحظر.")

# --- Kick protection ---
@bot.event
async def on_member_remove(member: discord.Member):
    guild = member.guild
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        if entry.target.id == member.id and not is_authorized(entry.user):
            await send_alert(guild, f"🚨 محاولة **Kick** غير مصرح بها من {entry.user.mention} ضد {member.mention}.")

# --- Role delete protection ---
@bot.event
async def on_guild_role_delete(role: discord.Role):
    guild = role.guild
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        if entry.target.id == role.id and not is_authorized(entry.user):
            try:
                await guild.create_role(name=role.name, permissions=role.permissions, color=role.color, hoist=role.hoist)
            except Exception:
                pass
            await send_alert(guild, f"🚨 تم حذف رتبة **{role.name}** بدون صلاحية من {entry.user.mention}. تمت الإعادة تلقائياً.")

# --- Role update protection ---
@bot.event
async def on_guild_role_update(before: discord.Role, after: discord.Role):
    guild = after.guild
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
        if entry.target.id == after.id and not is_authorized(entry.user):
            try:
                await after.edit(name=before.name, permissions=before.permissions, color=before.color, hoist=before.hoist)
            except Exception:
                pass
            await send_alert(guild, f"🚨 محاولة تعديل رتبة **{before.name}** بدون صلاحية من {entry.user.mention}. تم إرجاع الإعدادات.")

# --- Bot add protection ---
@bot.event
async def on_member_join(member: discord.Member):
    if member.bot:
        guild = member.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
            if entry.target.id == member.id and not is_authorized(entry.user):
                try:
                    await member.kick(reason="Protection: unauthorized bot add")
                except Exception:
                    pass
                await send_alert(guild, f"🤖🚫 بوت {member.mention} تمت إضافته بدون صلاحية بواسطة {entry.user.mention} وتم طرده.")

# ====================== SLASH COMMANDS ======================
@bot.tree.command(name="حماية", description="تفعيل حماية القناة من السب (في هذه القناة)")
@app_commands.describe(channel="اختر القناة المراد حمايتها (اختياري، افتراضي القناة الحالية)")
async def protect(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not is_authorized(interaction.user):
        await interaction.response.send_message("❌ ما عندك صلاحية تستخدم هذا الأمر.", ephemeral=True)
        return
    ch = channel or interaction.channel
    protected_channels.add(ch.id)
    await interaction.response.send_message(f"✅ تم تفعيل الحماية في القناة {ch.mention}.", ephemeral=True)

@bot.tree.command(name="الغاء", description="إلغاء حماية القناة من السب")
@app_commands.describe(channel="اختر القناة المراد إلغاء حمايتها (اختياري)")
async def unprotect(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not is_authorized(interaction.user):
        await interaction.response.send_message("❌ ما عندك صلاحية تستخدم هذا الأمر.", ephemeral=True)
        return
    ch = channel or interaction.channel
    if ch.id in protected_channels:
        protected_channels.remove(ch.id)
        await interaction.response.send_message(f"✅ تم إلغاء الحماية في {ch.mention}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ القناة {ch.mention} ليست محمية أصلاً.", ephemeral=True)

@bot.tree.command(name="الحالة", description="عرض القنوات المحمية حالياً")
async def status(interaction: discord.Interaction):
    if not is_authorized(interaction.user):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    if not protected_channels:
        await interaction.response.send_message("⚠️ لا توجد قنوات محمية حالياً.", ephemeral=True)
    else:
        channels = [f"<#{cid}>" for cid in protected_channels]
        await interaction.response.send_message("🔒 القنوات المحمية حالياً: " + ", ".join(channels), ephemeral=True)

# Manage bad words at runtime (in-memory)
@bot.tree.command(name="كلمة_ممنوعة_إضافة", description="إضافة كلمة جديدة لقائمة المنع (يؤخذ التطبيع بالحسبان)")
async def add_word(interaction: discord.Interaction, word: str):
    if not is_authorized(interaction.user):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    w = normalize_text(word)
    if not w:
        await interaction.response.send_message("⚠️ الكلمة بعد التطبيع صارت فاضية.", ephemeral=True)
        return
    BAD_WORDS_NORM.add(w)
    await interaction.response.send_message(f"✅ تمت إضافة الكلمة (بعد التطبيع): **{w}**", ephemeral=True)

@bot.tree.command(name="كلمة_ممنوعة_إزالة", description="إزالة كلمة من قائمة المنع (اكتبها بشكلها الأصلي وسيتم تطبيعها)")
async def remove_word(interaction: discord.Interaction, word: str):
    if not is_authorized(interaction.user):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    w = normalize_text(word)
    if w in BAD_WORDS_NORM:
        BAD_WORDS_NORM.remove(w)
        await interaction.response.send_message(f"🗑️ تم إزالة: **{w}**", ephemeral=True)
    else:
        await interaction.response.send_message("❌ غير موجودة بالقائمة (بعد التطبيع).", ephemeral=True)

@bot.tree.command(name="كلمة_ممنوعة_قائمة", description="عرض الكلمات الممنوعة (نسخة مطبّعة)")
async def list_words(interaction: discord.Interaction):
    if not is_authorized(interaction.user):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    words_sorted = sorted(list(BAD_WORDS_NORM))
    # split into chunks to avoid exceeding length
    chunk = 1500
    output = ""
    for w in words_sorted:
        if len(output) + len(w) + 2 > chunk:
            await interaction.followup.send(f"📜 {output}", ephemeral=True)
            output = ""
        output += (w + ", ")
    if output:
        await interaction.response.send_message(f"📜 {output}", ephemeral=True)
    elif not words_sorted:
        await interaction.response.send_message("📜 القائمة فارغة.", ephemeral=True)

# ====================== RUN ======================
def main():
    if TOKEN == "PUT_YOUR_TOKEN_HERE" or not TOKEN:
        raise RuntimeError("ضع توكن البوت في config.json أو متغير البيئة DISCORD_TOKEN")
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
