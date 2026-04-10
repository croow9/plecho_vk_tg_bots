import firebase_client as fc


async def notify_creator_on_join(bot, creator_uid, joiner_name, spot_name):
    """
    Уведомляет создателя сбора о новом участнике.
    """
    # Получаем данные создателя из Firestore
    creator_doc = fc.db.collection("users").document(creator_uid).get()
    if creator_doc.exists:
        creator_data = creator_doc.to_dict()
        chat_id = creator_data.get("telegramChatId")

        if chat_id:
            text = (
                f"👤 <b>{joiner_name}</b> записался на ваш сбор!\n"
                f"📍 Место: <b>{spot_name}</b>"
            )
            # Используем HTML для красоты [cite: 35]
            await bot.send_message(chat_id, text, parse_mode="HTML")


async def notify_participants_on_cancel(bot, gathering_id, user_name):
    """
    Уведомляет всех участников, если кто-то отменил свою запись.
    """
    # Получаем информацию о самом сборе для названия места
    gathering = fc.get_gathering(gathering_id)
    if not gathering:
        return

    # Получаем список всех участников подколлекции
    participants_ref = (
        fc.db.collection("gatherings").document(gathering_id).collection("participants")
    )
    participants = participants_ref.get()

    for p_doc in participants:
        p_data = p_doc.to_dict()
        user_id = p_data.get("userId")

        # Получаем профиль пользователя, чтобы найти его telegramChatId
        user_doc = fc.db.collection("users").document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            chat_id = user_data.get("telegramChatId")

            # Не отправляем уведомление тому, кто сам же и отменил запись
            if chat_id and p_data.get("userName") != user_name:
                text = (
                    f"ℹ️ <b>{user_name}</b> отменил участие в сборе.\n"
                    f"📍 Место: <b>{gathering['spotName']}</b>"
                )
                await bot.send_message(chat_id, text, parse_mode="HTML")
