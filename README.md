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
- API статистики : `http://localhost:8000/docs`
- CV-сервис : `http://localhost:8002/docs`
- Фронтенд : `http://localhost:4173`
- Dozzle (логи) : `http://localhost:8080`

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

- `CONVEYOR_SPEED_MM_PER_SEC` : скорость конвейера (мм/с), пример 1000
- `PX_TO_MM_WIDTH_FACTOR` : перевод пикселей → мм по ширине, пример 0.5
- `REDIS_HOST` : хост Redis, пример redis
- `REDIS_PORT` : порт Redis, пример 6379
- `POSTGRES_HOST` : хост PostgreSQL, пример postgres
- `POSTGRES_PORT` : порт PostgreSQL, пример 5432
- `POSTGRES_USER` : пользователь БД, пример lining_user
- `POSTGRES_PASSWORD` : пароль БД, пример lining_pass
- `POSTGRES_DB` : имя базы данных, пример lining_board

## Таблица цен (price_list)
Раскрой возможен только при наличии записей в price_list.
Минимальный набор для демонстрации:

```
INSERT INTO price_list (length_m, grade, price) VALUES
(1.0, 0, 150), (1.0, 1, 120), (1.0, 2, 90), (1.0, 3, 60),
(2.0, 0, 300), (2.0, 1, 250), (2.0, 2, 200), (2.0, 3, 150),
(3.0, 0, 450), (3.0, 1, 380), (3.0, 2, 310), (3.0, 3, 240);
```

Выполнить SQL можно через psql внутри контейнера:

`docker exec -it postgres psql -U lining_user -d lining_board`

## Просмотр логов
Все контейнеры: docker-compose logs -f
Конкретный сервис: docker-compose logs -f defect_detector
Через Dozzle: http://localhost:8080

## Остановка
docker-compose down # данные (тома) сохраняются
docker-compose down -v # полная очистка томов (удаление БД)

## Пример работы

<img width="978" height="552" alt="image" src="https://github.com/user-attachments/assets/bf79d282-0b4e-46a2-b966-a39e9b54c1b2" />
<img width="978" height="552" alt="image" src="https://github.com/user-attachments/assets/0268807c-f6b4-4c84-b540-0ac3b30ca869" />
<img width="978" height="552" alt="image" src="https://github.com/user-attachments/assets/738f6df4-e312-4090-befb-4d3254b557a3" />
<img width="978" height="552" alt="image" src="https://github.com/user-attachments/assets/cd8d3445-a91f-4024-aeac-d6aa56aa46c8" />
<img width="978" height="869" alt="image" src="https://github.com/user-attachments/assets/49beb660-3f15-472d-9a89-8c7aab67f0b2" />
<img width="819" height="583" alt="image" src="https://github.com/user-attachments/assets/7e029a10-e280-45c5-8533-ce9c8080e202" />
<img width="978" height="707" alt="image" src="https://github.com/user-attachments/assets/b37f3461-551c-485a-a593-cc920cb19d82" />
<img width="978" height="657" alt="image" src="https://github.com/user-attachments/assets/85d14caa-1b40-4e6e-ac40-6774015f60df" />
<img width="978" height="522" alt="image" src="https://github.com/user-attachments/assets/70be0f38-8cc5-40a7-b6e6-e94cfd0e3064" />









