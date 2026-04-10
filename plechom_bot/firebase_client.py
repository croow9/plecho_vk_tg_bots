import os
import math
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from config import FIREBASE_CRED_PATH, OREL_LAT, OREL_LNG
from google.cloud.firestore_v1.base_query import FieldFilter

# Инициализация Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---


def calculate_distance(lat1, lon1, lat2, lon2):
    """Расчет расстояния между двумя точками в км"""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# --- ПОЛЬЗОВАТЕЛИ ---


def get_user_by_email(email):
    docs = (
        db.collection("users")
        .where(filter=FieldFilter("email", "==", email.lower()))
        .limit(1)
        .get()
    )
    for doc in docs:
        return {**doc.to_dict(), "uid": doc.id}
    return None


def get_user_by_chat_id(chat_id):
    docs = (
        db.collection("users")
        .where(filter=FieldFilter("telegramChatId", "==", str(chat_id)))
        .limit(1)
        .get()
    )
    for doc in docs:
        return {**doc.to_dict(), "uid": doc.id}
    return None


def get_user_by_vk_id(vk_id):
    docs = (
        db.collection("users")
        .where(filter=FieldFilter("vkId", "==", str(vk_id)))
        .limit(1)
        .get()
    )
    for doc in docs:
        return {**doc.to_dict(), "uid": doc.id}
    return None


def create_vk_user(vk_id, name):
    user_data = {
        "name": name,
        "vkId": str(vk_id),
        "email": None,
        "xp": 0,
        "level": 1,
        "trainings_count": 0,
        "points": 0,
        "streakDays": 0,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "role": "user",
    }
    doc_ref = db.collection("users").add(user_data)
    return {**user_data, "uid": doc_ref[1].id}


def add_xp(vk_id, amount):
    """Добавляет опыт и проверяет повышение уровня"""
    user = get_user_by_vk_id(vk_id)
    if not user:
        return False

    new_xp = user.get("xp", 0) + amount
    new_level = (new_xp // 100) + 1

    db.collection("users").document(user["uid"]).update(
        {"xp": new_xp, "level": new_level}
    )
    return new_level > user.get("level", 1)


def get_leaderboard(limit=10):
    """Топ атлетов по опыту"""
    docs = (
        db.collection("users")
        .order_by("xp", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .get()
    )
    return [doc.to_dict() for doc in docs]


# --- ПЛОЩАДКИ (SPOTS / PLACES) ---


def add_new_place(name, lat, lng, address="", equipment=None, description=""):
    """Автоматическое добавление площадки (для приложения и ботов)"""
    place_data = {
        "name": name,
        "latitude": lat,
        "longitude": lng,
        "address": address,
        "equipment": equipment or ["Турники", "Брусья"],
        "description": description,
        "rating": 5.0,
        "reviews_count": 0,
        "status": "approved",  # Поле status для совместимости с твоим методом
        "createdAt": firestore.SERVER_TIMESTAMP,
    }
    db.collection("spots").add(place_data)  # Используем 'spots', как в твоем коде


def get_nearest_places(user_lat, user_lon, limit=3):
    """Поиск ближайших площадок по координатам"""
    spots_ref = (
        db.collection("spots")
        .where(filter=FieldFilter("status", "==", "approved"))
        .get()
    )
    spots = []
    for doc in spots_ref:
        data = doc.to_dict()
        if "latitude" in data and "longitude" in data:
            dist = calculate_distance(
                user_lat, user_lon, data["latitude"], data["longitude"]
            )
            spots.append({**data, "id": doc.id, "distance": round(dist, 2)})

    return sorted(spots, key=lambda x: x["distance"])[:limit]


def get_approved_spots():
    docs = (
        db.collection("spots")
        .where(filter=FieldFilter("status", "==", "approved"))
        .get()
    )
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]


# --- СБОРЫ ---


def get_upcoming_gatherings(limit=5):
    now = datetime.now()
    docs = (
        db.collection("gatherings")
        .where(filter=FieldFilter("scheduledAt", ">", now))
        .order_by("scheduledAt")
        .limit(limit)
        .get()
    )
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]


def get_gathering(gathering_id):
    doc = db.collection("gatherings").document(gathering_id).get()
    return {**doc.to_dict(), "id": doc.id} if doc.exists else None


def get_participants(gathering_id):
    docs = (
        db.collection("gatherings")
        .document(gathering_id)
        .collection("participants")
        .get()
    )
    return [doc.to_dict().get("userName", "Аноним") for doc in docs]


def join_gathering(gathering_id, user_id, user_name):
    batch = db.batch()
    g_ref = db.collection("gatherings").document(gathering_id)
    p_ref = g_ref.collection("participants").document(user_id)
    batch.set(
        p_ref, {"userId": user_id, "userName": user_name, "joinedAt": datetime.now()}
    )
    batch.update(g_ref, {"currentCount": firestore.Increment(1)})
    batch.commit()


# --- ОТЗЫВЫ (REVIEWS) ---


def add_review(user_id, place_id, text, stars):
    """Добавляет отзыв к площадке и обновляет её средний рейтинг"""
    review_data = {
        "userId": user_id,
        "placeId": place_id,
        "text": text,
        "stars": stars,
        "date": firestore.SERVER_TIMESTAMP,
    }

    # Сохраняем отзыв в отдельную коллекцию
    db.collection("reviews").add(review_data)

    # Логика автоматического обновления рейтинга площадки (опционально)
    spot_ref = db.collection("spots").document(place_id)
    spot_ref.update(
        {
            "reviews_count": firestore.Increment(1),
            # Тут можно усложнить формулу пересчета среднего рейтинга
        }
    )

    print(f"⭐️ Отзыв от {user_id} добавлен для площадки {place_id}")


def get_user_gatherings(user_id):
    """Сборы, на которые записан юзер (возвращаем на место)"""
    try:
        now = datetime.now()
        # Получаем все будущие сборы
        all_g = (
            db.collection("gatherings")
            .where(filter=FieldFilter("scheduledAt", ">", now))
            .get()
        )
        user_g = []
        for g in all_g:
            # Проверяем наличие юзера в подколлекции участников
            p_doc = g.reference.collection("participants").document(user_id).get()
            if p_doc.exists:
                user_g.append({**g.to_dict(), "id": g.id})
        return user_g
    except Exception as e:
        print(f"Error in get_user_gatherings: {e}")
        return []


def update_user(uid, data: dict):
    """Обновление данных пользователя (тоже нужно для работы)"""
    try:
        db.collection("users").document(uid).update(data)
    except Exception as e:
        print(f"Error updating user: {e}")
