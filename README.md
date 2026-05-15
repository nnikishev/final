# Timber Cutting Optimizer

Система автоматического обнаружения дефектов пиломатериалов и оптимизации раскроя.

## Сервисы

| Сервис               | Порт | Назначение |
|----------------------|------|-------------|
| defect_detector (CV) | 8002 | RTSP, детекция дефектов (YOLO), публикация в Redis |
| cutting_service      | 8001 | Подписка на Redis, расчёт раскроя, сохранение в БД |
| statistics_service   | 8000 | REST API для фронтенда |
| frontend (React)     | 4173 | Визуализация досок, дефектов, планов раскроя |
| Redis                | 6379 | Брокер сообщений (канал `cv_events`) |
| PostgreSQL           | 5432 | Хранение boards, defects, cut_plans, price_list |
| Dozzle               | 8080 | Веб-интерфейс логов контейнеров |

## Быстрый старт

```bash
git clone https://github.com/your-repo/timber-cutting-optimizer.git
cd timber-cutting-optimizer
cp .env.example .env
# при необходимости отредактируйте .env
docker-compose up -d
```

## Доступы после запуска
API статистики : `http://localhost:8000/docs`
CV-сервис : `http://localhost:8002/docs`
Фронтенд : `http://localhost:4173`
Dozzle (логи) : `http://localhost:8080`

## Управление камерой
На дашборде нажмите «Запустить камеру».
В модальном окне укажите:
- название камеры (произвольное, например front_camera)
- RTSP-адрес (например rtsp://mediamtx:8554/conveyor)

«Остановить камеру» — завершает обработку потока.

Калибровка длины доски
Длина доски вычисляется по формуле:
```
total_length_mm = (end_time_sec - start_time_sec) × CONVEYOR_SPEED_MM_PER_SEC
```

Если реальная длина известна (например, 6000 мм), а расчётная не совпадает, подберите `CONVEYOR_SPEED_MM_PER_SEC`:

новая_скорость = (реальная_длина / расчётная_длина) × старая_скорость

Пример: доска 6 м, расчётная длина 2.9 м, старая скорость 1000 мм/с →
новая_скорость = (6000 / 2900) × 1000 ≈ 2069 мм/с

Измените параметр в .env CV-сервиса и перезапустите:

`docker-compose restart defect_detector`

## Переменные окружения (.env)
Основные настройки (остальные см. в .env.example):

`CONVEYOR_SPEED_MM_PER_SEC` : скорость конвейера (мм/с), пример 1000
`PX_TO_MM_WIDTH_FACTOR` : перевод пикселей → мм по ширине, пример 0.5
`REDIS_HOST` : хост Redis, пример redis
`REDIS_PORT` : порт Redis, пример 6379
`POSTGRES_HOST` : хост PostgreSQL, пример postgres
`POSTGRES_PORT` : порт PostgreSQL, пример 5432
`POSTGRES_USER` : пользователь БД, пример lining_user
`POSTGRES_PASSWORD` : пароль БД, пример lining_pass
`POSTGRES_DB` : имя базы данных, пример lining_board

## Таблица цен (price_list)
Раскрой возможен только при наличии записей в price_list.
Минимальный набор для демонстрации:

INSERT INTO price_list (length_m, grade, price) VALUES
(1.0, 0, 150), (1.0, 1, 120), (1.0, 2, 90), (1.0, 3, 60),
(2.0, 0, 300), (2.0, 1, 250), (2.0, 2, 200), (2.0, 3, 150),
(3.0, 0, 450), (3.0, 1, 380), (3.0, 2, 310), (3.0, 3, 240);

Выполнить SQL можно через psql внутри контейнера:

docker exec -it postgres psql -U lining_user -d lining_board

## Просмотр логов
Все контейнеры: docker-compose logs -f
Конкретный сервис: docker-compose logs -f defect_detector
Через Dozzle: http://localhost:8080

## Остановка
docker-compose down # данные (тома) сохраняются
docker-compose down -v # полная очистка томов (удаление БД)

## Пример работы

![alt text](image.png)
![alt text](image-1.png)
![alt text](image-2.png)
![alt text](image-3.png)
![alt text](image-4.png)
![alt text](image-5.png)
![alt text](image-6.png)
![alt text](image-7.png)
