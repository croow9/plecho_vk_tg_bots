import firebase_client as fc

# Список реальных площадок Орла (примерные координаты)
STREET_SPOTS = [
    {
        "name": "Спортплощадка в Парке Победы",
        "lat": 52.9705,
        "lng": 36.0638,
        "address": "ул. Зои Космодемьянской",
        "equip": ["Воркаут-зона", "Турники", "Низкие брусья"],
    },
    {
        "name": "Площадка на Набережной",
        "lat": 52.9620,
        "lng": 36.0710,
        "address": "Набережная Дубровинского",
        "equip": ["Турники", "Пресс", "Рукоход"],
    },
    {
        "name": "Турники у Городского парка",
        "lat": 52.9665,
        "lng": 36.0590,
        "address": "ул. Максима Горького",
        "equip": ["Брусья", "Шведская стенка"],
    },
]


def fill_database():
    for spot in STREET_SPOTS:
        fc.add_new_place(
            name=spot["name"],
            lat=spot["lat"],
            lng=spot["lng"],
            address=spot["address"],
            equipment=spot["equip"],
        )
    print("\n🚀 Все площадки Орла загружены!")


if __name__ == "__main__":
    fill_database()
