# Quiz bots

![telegram bot image](https://i.ibb.co/hB1CwSS/image.png)

Telegram and Vkontakte quiz bots in Russian. Quiz is generated randomly from a
large number of text files representing played quiz games in the past and is
written then in Redis db.

Link to telegram bot: [Bot](https://t.me/balancy_quiz_bot)

Link to VK bot: [Messages](https://vk.com/im?sel=-208745906)

## Install

At least Python 3.8 and Git should be already installed.

1. Clone the repository by command:
```console
git clone git@github.com:balancy/quiz_bot
```

2. Go inside cloned repository, create and activate virtal environment:
```console
python -m venv env
source env/bin/activate (env\scripts\activate for Windows)
```

3. Install dependecies:
```console
pip install -r requirements.txt
```

4. Rename `.env.example` to `.env` and define your proper environment variables:

- `TG_BOT_TOKEN` - your telegram bot token
- `VK_BOT_TOKEN` - your vkontakte bot token
- `REDIS_ENDPOINT` - endpoint of your redis db
- `REDIS_PORT` - port of your redis db
- `REDIS_PASSWORDT` - password of your redis db

## Flush DB

In case you need to flush the database, use

```code
python flush_db.py
```

## Populate DB

To populate the database, use

```code
python populate_db.py --number <number>
```
where `number` is number of quizzes to populate the DB. By default it's 10.

## Launch bots

1. Run telegram bot
```console
python tg_bot.py
```

2. Run vkontakte bot
```console
python vk_bot.py
```