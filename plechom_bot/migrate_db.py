import firebase_client as fc


def migrate_users():
    print("🔄 Начинаю обновление базы пользователей...")
    users_ref = fc.db.collection("users").get()

    for doc in users_ref:
        data = doc.to_dict()
        updates = {}

        # Если поля нет, готовим его к добавлению
        if "xp" not in data:
            updates["xp"] = 0
        if "level" not in data:
            updates["level"] = 1
        if "trainings_count" not in data:
            updates["trainings_count"] = 0

        if updates:
            fc.db.collection("users").document(doc.id).update(updates)
            print(f"✅ Обновлен юзер: {data.get('name', doc.id)}")

    print("🚀 Миграция завершена!")


if __name__ == "__main__":
    migrate_users()
