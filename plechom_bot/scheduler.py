from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import firebase_client as fc


async def gathering_reminder(bot):
    now = datetime.now()
    soon = now + timedelta(minutes=65)

    gs = (
        fc.db.collection("gatherings")
        .where("scheduledAt", ">", now)
        .where("scheduledAt", "<=", soon)
        .get()
    )
    for g_doc in gs:
        g = g_doc.to_dict()
        participants = g_doc.reference.collection("participants").get()
        for p in participants:
            p_data = p.to_dict()
            user = fc.db.collection("users").document(p_data["userId"]).get().to_dict()
            if user.get("telegramChatId"):
                await bot.send_message(
                    user["telegramChatId"],
                    f"⏰ Через час — сбор в {g['spotName']}!\nНе забудь! 💪",
                )


async def daily_reminder(bot):
    users = fc.db.collection("users").where("telegramChatId", "!=", None).get()
    for u_doc in users:
        u = u_doc.to_dict()
        # Простая проверка на наличие сборов сегодня
        gs = fc.get_user_gatherings(u_doc.id)
        if not gs:
            await bot.send_message(
                u["telegramChatId"],
                "🌅 Доброе утро! Ты ещё не записался на сегодня.\nИспользуй /gatherings чтобы найти сбор!",
            )


async def streak_reminder(bot):
    users = fc.db.collection("users").where("streakDays", ">", 0).get()
    for u_doc in users:
        u = u_doc.to_dict()
        if u.get("telegramChatId"):
            # Проверка чек-ина (упрощенно по lastStreakDate)
            if u["lastStreakDate"].date() < datetime.now().date():
                await bot.send_message(
                    u["telegramChatId"],
                    f"🔥 Не потеряй серию ({u['streakDays']} дн.)!\nЕщё можно записаться на вечерний сбор.",
                )


def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(gathering_reminder, "interval", minutes=10, args=[bot])
    scheduler.add_job(daily_reminder, "cron", hour=10, minute=0, args=[bot])
    scheduler.add_job(streak_reminder, "cron", hour=20, minute=0, args=[bot])
    return scheduler
