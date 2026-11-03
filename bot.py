import logging
import os
import random
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # Tuỳ chọn: điền ID server để lệnh cập nhật ngay lập tức
WELCOME_CHANNEL_ID = os.getenv("WELCOME_CHANNEL_ID")  # Tuỳ chọn: kênh chào mừng thành viên mới
AUTO_ROLE_ID = os.getenv("AUTO_ROLE_ID")  # Tuỳ chọn: role tự cấp cho thành viên mới

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("bot")

intents = discord.Intents.default()
intents.members = True  # Cần bật "Server Members Intent" trong Developer Portal


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Đồng bộ slash commands
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info("Đã sync lệnh cho server %s", GUILD_ID)
        else:
            await self.tree.sync()
            log.info("Đã sync lệnh toàn cầu (có thể mất tới 1 giờ để hiện)")


bot = MyBot()


# ---------------------------------------------------------------- Sự kiện
@bot.event
async def on_ready():
    log.info("Đăng nhập thành công: %s (ID: %s)", bot.user, bot.user.id)
    await bot.change_presence(activity=discord.Game(name="/help để xem lệnh"))


@bot.event
async def on_member_join(member: discord.Member):
    # Tự cấp role
    if AUTO_ROLE_ID:
        role = member.guild.get_role(int(AUTO_ROLE_ID))
        if role:
            try:
                await member.add_roles(role, reason="Auto role")
            except discord.Forbidden:
                log.warning("Bot không đủ quyền để cấp role %s", role.name)

    # Tin nhắn chào mừng
    channel = None
    if WELCOME_CHANNEL_ID:
        channel = member.guild.get_channel(int(WELCOME_CHANNEL_ID))
    channel = channel or member.guild.system_channel
    if channel:
        embed = discord.Embed(
            title="Chào mừng thành viên mới! 🎉",
            description=f"Xin chào {member.mention}, chào mừng bạn đến với **{member.guild.name}**!",
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Bạn là thành viên thứ {member.guild.member_count}")
        await channel.send(embed=embed)


# ---------------------------------------------------------------- Lệnh chung
@bot.tree.command(name="ping", description="Kiểm tra độ trễ của bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")


@bot.tree.command(name="help", description="Xem danh sách lệnh")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 Danh sách lệnh", color=discord.Color.blurple())
    embed.add_field(
        name="Chung",
        value="`/ping` `/help` `/userinfo` `/serverinfo` `/avatar`",
        inline=False,
    )
    embed.add_field(name="Giải trí", value="`/roll` `/8ball` `/poll` `/coinflip`", inline=False)
    embed.add_field(
        name="Quản trị",
        value="`/kick` `/ban` `/unban` `/timeout` `/clear`",
        inline=False,
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="userinfo", description="Xem thông tin một thành viên")
@app_commands.describe(member="Thành viên cần xem (mặc định là bạn)")
@app_commands.guild_only()
async def userinfo(interaction: discord.Interaction, member: discord.Member | None = None):
    member = member or interaction.user
    embed = discord.Embed(title=str(member), color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Biệt danh", value=member.nick or "Không có")
    embed.add_field(name="Tạo tài khoản", value=discord.utils.format_dt(member.created_at, "D"))
    embed.add_field(name="Vào server", value=discord.utils.format_dt(member.joined_at, "D"))
    roles = [r.mention for r in reversed(member.roles) if r.name != "@everyone"]
    embed.add_field(name=f"Role ({len(roles)})", value=" ".join(roles[:15]) or "Không có", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverinfo", description="Xem thông tin server")
@app_commands.guild_only()
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=g.name, color=discord.Color.blurple())
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="Chủ server", value=g.owner.mention if g.owner else "Không rõ")
    embed.add_field(name="Thành viên", value=g.member_count)
    embed.add_field(name="Kênh chat", value=len(g.text_channels))
    embed.add_field(name="Kênh voice", value=len(g.voice_channels))
    embed.add_field(name="Số role", value=len(g.roles))
    embed.add_field(name="Ngày tạo", value=discord.utils.format_dt(g.created_at, "D"))
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="avatar", description="Xem avatar của một thành viên")
@app_commands.describe(member="Thành viên cần xem (mặc định là bạn)")
async def avatar(interaction: discord.Interaction, member: discord.User | None = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"Avatar của {member.display_name}", color=discord.Color.blurple())
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)


# ---------------------------------------------------------------- Giải trí
@bot.tree.command(name="roll", description="Tung xúc xắc")
@app_commands.describe(sides="Số mặt của xúc xắc (mặc định 6)")
async def roll(interaction: discord.Interaction, sides: app_commands.Range[int, 2, 1000] = 6):
    await interaction.response.send_message(f"🎲 Bạn tung được **{random.randint(1, sides)}** (d{sides})")


@bot.tree.command(name="coinflip", description="Tung đồng xu")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.send_message(f"🪙 Kết quả: **{random.choice(['Sấp', 'Ngửa'])}**")


@bot.tree.command(name="8ball", description="Hỏi quả cầu thần kỳ")
@app_commands.describe(question="Câu hỏi của bạn")
async def eight_ball(interaction: discord.Interaction, question: str):
    answers = [
        "Chắc chắn rồi!", "Hoàn toàn đúng.", "Có vẻ là có.", "Rất có thể.",
        "Hỏi lại sau nhé.", "Tôi không chắc lắm.", "Đừng trông chờ vào điều đó.",
        "Câu trả lời là không.", "Rất đáng ngờ.",
    ]
    await interaction.response.send_message(f"🎱 **{question}**\n{random.choice(answers)}")


@bot.tree.command(name="poll", description="Tạo bình chọn nhanh (tối đa 5 lựa chọn)")
@app_commands.describe(question="Nội dung bình chọn", options="Các lựa chọn, ngăn cách bằng dấu |  (vd: A | B | C)")
@app_commands.guild_only()
async def poll(interaction: discord.Interaction, question: str, options: str):
    choices = [o.strip() for o in options.split("|") if o.strip()]
    if not 2 <= len(choices) <= 5:
        await interaction.response.send_message("Cần từ 2 đến 5 lựa chọn, ngăn cách bằng `|`.", ephemeral=True)
        return
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    desc = "\n".join(f"{emojis[i]} {c}" for i, c in enumerate(choices))
    embed = discord.Embed(title=f"📊 {question}", description=desc, color=discord.Color.gold())
    embed.set_footer(text=f"Tạo bởi {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()
    for i in range(len(choices)):
        await msg.add_reaction(emojis[i])


# ---------------------------------------------------------------- Quản trị
def can_act_on(interaction: discord.Interaction, target: discord.Member) -> str | None:
    """Trả về thông báo lỗi nếu không thể thao tác lên target, ngược lại trả None."""
    if target.id == interaction.user.id:
        return "Bạn không thể tự thao tác lên chính mình."
    if target.id == interaction.guild.owner_id:
        return "Không thể thao tác lên chủ server."
    if target.top_role >= interaction.guild.me.top_role:
        return "Role của bot phải cao hơn role của người này."
    if interaction.user.id != interaction.guild.owner_id and target.top_role >= interaction.user.top_role:
        return "Role của bạn phải cao hơn role của người này."
    return None


@bot.tree.command(name="kick", description="Đuổi một thành viên khỏi server")
@app_commands.describe(member="Thành viên cần kick", reason="Lý do")
@app_commands.guild_only()
@app_commands.checks.has_permissions(kick_members=True)
@app_commands.checks.bot_has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Không có lý do"):
    if err := can_act_on(interaction, member):
        await interaction.response.send_message(err, ephemeral=True)
        return
    await member.kick(reason=f"{interaction.user}: {reason}")
    await interaction.response.send_message(f"👢 Đã kick **{member}** — {reason}")


@bot.tree.command(name="ban", description="Cấm một thành viên")
@app_commands.describe(member="Thành viên cần ban", reason="Lý do")
@app_commands.guild_only()
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.checks.bot_has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Không có lý do"):
    if err := can_act_on(interaction, member):
        await interaction.response.send_message(err, ephemeral=True)
        return
    await member.ban(reason=f"{interaction.user}: {reason}", delete_message_days=0)
    await interaction.response.send_message(f"🔨 Đã ban **{member}** — {reason}")


@bot.tree.command(name="unban", description="Gỡ ban bằng ID người dùng")
@app_commands.describe(user_id="ID của người dùng cần gỡ ban")
@app_commands.guild_only()
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.checks.bot_has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
    except (ValueError, discord.NotFound):
        await interaction.response.send_message("Không tìm thấy người dùng hoặc họ chưa bị ban.", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ Đã gỡ ban **{user}**")


@bot.tree.command(name="timeout", description="Cấm chat tạm thời một thành viên")
@app_commands.describe(member="Thành viên", minutes="Số phút (1 - 40320)", reason="Lý do")
@app_commands.guild_only()
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.checks.bot_has_permissions(moderate_members=True)
async def timeout(
    interaction: discord.Interaction,
    member: discord.Member,
    minutes: app_commands.Range[int, 1, 40320],
    reason: str = "Không có lý do",
):
    if err := can_act_on(interaction, member):
        await interaction.response.send_message(err, ephemeral=True)
        return
    await member.timeout(timedelta(minutes=minutes), reason=f"{interaction.user}: {reason}")
    await interaction.response.send_message(f"🔇 Đã timeout **{member}** trong {minutes} phút — {reason}")


@bot.tree.command(name="clear", description="Xoá nhiều tin nhắn cùng lúc")
@app_commands.describe(amount="Số tin nhắn cần xoá (1 - 100)")
@app_commands.guild_only()
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.checks.bot_has_permissions(manage_messages=True, read_message_history=True)
async def clear(interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Đã xoá {len(deleted)} tin nhắn.", ephemeral=True)


# ---------------------------------------------------------------- Xử lý lỗi
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        msg = "❌ Bạn không có quyền dùng lệnh này."
    elif isinstance(error, app_commands.BotMissingPermissions):
        msg = "❌ Bot thiếu quyền: " + ", ".join(error.missing_permissions)
    elif isinstance(error, app_commands.NoPrivateMessage):
        msg = "❌ Lệnh này chỉ dùng được trong server."
    else:
        log.exception("Lỗi lệnh /%s", interaction.command.name if interaction.command else "?", exc_info=error)
        msg = "⚠️ Đã có lỗi xảy ra, vui lòng thử lại sau."

    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Thiếu DISCORD_TOKEN. Hãy tạo file .env (xem .env.example).")
    bot.run(TOKEN)
