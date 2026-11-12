# AGENTS.md

FastAPI + SQLAlchemy 2.1 + PostgreSQL API для задач (TODO). Слоистая архитектура, Pydantic v2, Python 3.12.

Человекочитаемый обзор проекта, быстрый старт и описание API — в [README.md](README.md). Здесь только то, что нужно для правки кода. Необходимо поддерживать в актуальном состоянии, при каждом изменении кода.

## Установка зависимостей

```bash
python3.12 -m venv venv
./venv/bin/pip install -r requirements.txt
```

- Единственный источник зависимостей — `requirements.txt` с точными версиями. `pyproject.toml`, `poetry`, `pipenv` нет.
- `venv/` уже создан (Python 3.12) и лежит в `.gitignore`. Интерпретатор проекта — `./venv/bin/python`, не системный `python`.
- Добавляешь пакет — ставь его в venv и фиксируй версию в `requirements.txt`. `pip freeze` в файл целиком не перезаписывать (там только прод-зависимости).
- В Docker те же зависимости ставятся из `requirements.txt` при `docker compose up --build` — отдельный `pip install` на хосте для контейнера не нужен.

## Запуск и команды

Весь код лежит в `app/`, импорты абсолютные **от корня `app/`** (`from models.base import Base`, `from core.config import get_settings`). Из корня репозитория `import app.main` падает с `ModuleNotFoundError` — это ожидаемо.

```bash
# локально (cwd = app/)
cd app && ../venv/bin/uvicorn main:app --reload

# весь стек (api + postgres + redis)
docker compose up --build
```

- API: `http://localhost:8000`, Postgres: `localhost:5432` (`user` / `pass` / `mydb`).
- Контейнер `api` публикует `8000`: если запущен `docker compose`, локальный `uvicorn` упадёт с `[Errno 98] Address already in use`. Освободить порт — `docker compose stop api`, либо запускать локально с `--port 8001`.
- `DATABASE_URL` читается из env, дефолт в `app/core/config.py`. Драйвер — psycopg 3 (`postgresql://` уже мапится на него в SQLAlchemy 2.1).
- В проекте **нет** тестов, линтеров, `pyproject.toml` и Alembic. Не выдумывать команды `pytest`/`ruff` — их пока нет.

## Слои (порядок вызовов строго такой)

| Слой           | Каталог                       | Правила                                                                         |
| -------------- | ----------------------------- | ------------------------------------------------------------------------------- |
| Роутеры        | `app/api/routers/`            | только HTTP: валидация, `HTTPException`, коды статусов. Без SQL и бизнес-логики |
| DI             | `app/api/dependencies.py`     | сборка зависимостей (`get_task_service`)                                        |
| Сервисы        | `app/services/`               | бизнес-логика, транзакции (`db.commit()`), доменные исключения (`TaskNotFound`) |
| Репозитории    | `app/repositories/`           | **все** запросы к SQLAlchemy. Без `commit()`                                    |
| Модели / схемы | `app/models/`, `app/schemas/` | ORM и Pydantic отдельно; схема ответа с `ConfigDict(from_attributes=True)`      |

Новая сущность = та же цепочка файлов (router → dependency → service → repository → model → schema), без «срезания» слоёв.

## Конвенции

- PEP 604 для опциональных типов (`str | None`), типизированные колонки `Mapped[...] = mapped_column(...)`.
- Преобразование ORM → Pydantic через `Schema.model_validate(obj)`.
- Ошибки: доменное исключение в сервисе, `HTTPException(status_code=status.HTTP_*)` в роутере.
- Роутер: `APIRouter(prefix="/tasks")`, префикс на роутере, а не в `include_router`. Аннотация возвращаемого типа — вместо `response_model`.
- Git: `add` / `commit` / `push` / `rebase` — только по явной просьбе. Сообщения коммитов — conventional commits, по-английски.

## Чеклист для нового FastAPI-кода

Проект подключил скилл `.agents/skills/fastapi/SKILL.md` — сверяться с ним. Главное отличие от текущего кода:

- зависимости через `Annotated[T, Depends(...)]` и type-alias, а не `param = Depends(...)`;
- возвращаемый тип вместо `response_model`, `...` как значение по умолчанию не использовать.

Существующий код написан в старом стиле (`param: T = Depends(...)`). Мигрировать постепенно и **не смешивать два стиля в одном файле**: правишь файл — приводи его к `Annotated` целиком.

## Известные шероховатости (чинить при касании файла)

- `TaskUpdateSchema.completed: bool | None = False` — дефолт `None`, иначе `PATCH` только с `title` молча сбрасывает `completed` в `False`.
- `TaskService.update_task` ловит `Exception`, но `TaskRepository.get_by_id` возвращает `None` для отсутствующего id → исключение не срабатывает, падает `AttributeError` на `None.title`. Проверять `None`, а не ловить исключения.
- `main.py` хардкодит CORS-origins, хотя они есть в `get_settings().CORS_ALLOW_ORIGINS` — источник правды должен быть один.
- Схема БД создаётся через `Base.metadata.create_all` в `lifespan`; миграций нет. Изменение существующей таблицы требует пересоздания (`docker compose down -v`) или ручного SQL.
- `redis` поднят в `docker-compose.yml`, но кодом не используется.
- Остался отладочный `print(...)` в `TaskService.get_tasks`.
- `async def` эндпоинты вызывают **синхронный** SQLAlchemy `Session` и блокируют event loop. Держать работу с БД в обычных `def` эндпоинтах либо переходить на async SQLAlchemy — не смешивать.

## Структура

```
app/main.py        создание app, lifespan, CORS, include_router
app/api/           dependencies.py, routers/
app/core/          config.py (настройки из env)
app/db/            session.py (engine, session_factory, get_db)
app/models/        base.py (Base с UUID pk), ORM-модели
app/repositories/  доступ к данным
app/schemas/       Pydantic-контракты
app/services/      бизнес-логика
```
