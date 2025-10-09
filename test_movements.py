#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API движений
"""

import requests
import json

# URL для тестирования
BASE_URL = "http://localhost:5000"  # Измените на ваш URL

def test_movements_api():
    """Тестируем API движений"""
    
    # Сначала нужно получить токен авторизации или использовать сессию
    # Для простоты тестирования, давайте проверим, что API отвечает
    
    try:
        # Тестируем GET запрос к API движений
        response = requests.get(f"{BASE_URL}/supply/api/supply/movements")
        
        print(f"Статус ответа: {response.status_code}")
        print(f"Заголовки: {response.headers}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Количество движений: {len(data)}")
            if data:
                print("Первое движение:")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
            else:
                print("Движения не найдены")
        else:
            print(f"Ошибка: {response.text}")
            
    except Exception as e:
        print(f"Ошибка при тестировании API: {e}")

if __name__ == "__main__":
    test_movements_api()
