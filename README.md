# Discord Bot

Bot Discord dùng slash command (discord.py 2.x).

## Tính năng
- **Chung:** `/ping` `/help` `/userinfo` `/serverinfo` `/avatar`
- **Giải trí:** `/roll` `/coinflip` `/8ball` `/poll`
- **Quản trị:** `/kick` `/ban` `/unban` `/timeout` `/clear`
- **Tự động:** chào mừng thành viên mới + tự cấp role

## Chạy local
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # rồi điền DISCORD_TOKEN
python bot.py
```

## Chạy bằng Docker
```bash
docker build -t discord-bot .
docker run -d --restart unless-stopped --env-file .env --name discord-bot discord-bot
```

## Biến môi trường
| Biến | Bắt buộc | Ý nghĩa |
|---|---|---|
| `DISCORD_TOKEN` | ✅ | Token bot |
| `GUILD_ID` | | ID server để lệnh cập nhật ngay |
| `WELCOME_CHANNEL_ID` | | Kênh chào mừng |
| `AUTO_ROLE_ID` | | Role tự cấp |
