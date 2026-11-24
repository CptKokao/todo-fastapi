# python-fastapi

Учебный REST API для задач (TODO) на **FastAPI** со слоистой архитектурой. Проект небольшой, но разложен «по-взрослому»: HTTP-слой отделён от бизнес-логики, бизнес-логика — от доступа к данным, схемы Pydantic — от ORM-моделей.

Цель проекта — показать, как связать FastAPI, SQLAlchemy 2 и PostgreSQL, не сваливая всё в один файл. Всё, что нужно, чтобы начать работать: этот README и [`AGENTS.md`](AGENTS.md) (правила для разработки).

---

## Содержание

- [Стек](#стек)
- [Быстрый старт](#быстрый-старт)
  - [Вариант 1: Docker Compose (всё сразу)](#вариант-1-docker-compose-всё-сразу)
  - [Вариант 2: локально с venv](#вариант-2-локально-с-venv)
- [Конфигурация](#конфигурация)
- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [Модель данных](#модель-данных)
- [API](#api)
- [Примеры запросов](#примеры-запросов)
- [Как добавить новую сущность](#как-добавить-новую-сущность)
- [Конвенции кода](#конвенции-кода)
- [Известные ограничения и TODO](#известные-ограничения-и-todo)

---

## Стек

| Компонент  | Версия      | Роль                                         |
| ---------- | ----------- | -------------------------------------------- |
| Python     | 3.12        | рантайм                                      |
| FastAPI    | 0.162.0     | HTTP-фреймворк, валидация, OpenAPI           |
| Starlette  | 1.10.0      | ASGI-основа FastAPI                          |
| Uvicorn    | 0.54.0      | ASGI-сервер                                  |
| Pydantic   | 2.14.2      | схемы запросов/ответов (v2)                  |
| SQLAlchemy | 2.1.6       | ORM и доступ к БД                            |
| psycopg    | 3.3.6       | драйвер PostgreSQL (psycopg 3, не psycopg2!) |
| PostgreSQL | 16 (alpine) | база данных                                  |
| Redis      | 7 (alpine)  | кэш списка задач для `GET /tasks`            |

Полный список с точными версиями — [`requirements.txt`](requirements.txt). Других менеджеров зависимостей (`pyproject.toml`, Poetry, Pipenv) в проекте нет.

---

## Быстрый старт

Требуется либо Docker + Docker Compose v2, либо Python 3.12 локально.

### Вариант 1: Docker Compose (всё сразу)

Поднимает три сервиса: `api`, `db` (PostgreSQL 16), `redis`.

```bash
docker compose up --build
```

- API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- PostgreSQL: `localhost:5432`, пользователь `user`, пароль `pass`, база `mydb`

Остановить: `docker compose down`. Удалить и данные БД: `docker compose down -v`.

> [`docker-compose.yml`](docker-compose.yml) поднимает `api` в dev-режиме: `./app` монтируется в `/app`, uvicorn стартует с `--reload`, поэтому правки кода на хосте применяются сразу, без пересборки. Правки `requirements.txt` и `Dockerfile` по-прежнему требуют `docker compose up -d --build api`. Образ собирается по [`Dockerfile`](Dockerfile): `requirements.txt` ставится в образ, содержимое `app/` копируется в `/app`, запускается `uvicorn main:app` (эта копия используется, если убрать `volumes`).

### Вариант 2: локально с venv

```bash
python3.12 -m venv venv
./venv/bin/pip install -r requirements.txt
```

Для запуска нужна доступная PostgreSQL. Проще всего поднять только её:

```bash
docker compose up -d db
```

Затем (обратите внимание на `cd app` — см. [структуру](#структура-проекта)):

```bash
cd app
../venv/bin/uvicorn main:app --reload
```

> **Важно:** весь код лежит в `app/`, импорты абсолютные **от корня `app/`** (`from models.base import Base`). Из корня репозитория `import app.main` падает с `ModuleNotFoundError: No module named 'models'` — это ожидаемо, а не баг.
>
> **Порт 8000 занят?** Контейнер `api` публикует тот же порт. Освободить: `docker compose stop api`. Либо запустить локально с `--port 8001`.

---

## Конфигурация

Настройки собираются в [`app/core/config.py`](app/core/config.py) функцией `get_settings()` и читаются из переменных окружения.

| Переменная     | По умолчанию                                 | Описание                                                                                              |
| -------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `DATABASE_URL` | `postgresql://user:pass@localhost:5432/mydb` | DSN для SQLAlchemy. Схема `postgresql://` в SQLAlchemy 2.1 автоматически мапится на драйвер psycopg 3 |
| `REDIS_URL`    | `redis://localhost:6379/0`                   | адрес Redis для `RedisCache`. Кэшируется только список `GET /tasks`                                   |

В `docker-compose.yml` значения переопределяются: `DATABASE_URL=postgresql://user:pass@db:5432/mydb` и `REDIS_URL=redis://redis:6379/0` (хосты `db` и `redis` — имена сервисов внутри compose-сети; `localhost` там указывал бы на сам контейнер `api`).

CORS: разрешён источник `http://localhost:3000`. Список продублирован в `main.py` и в `Config.CORS_ALLOW_ORIGINS` — это известная шероховатость (см. [ограничения](#известные-ограничения-и-todo)).

---

## Архитектура

Четыре слоя, вызов строго сверху вниз. Каждый слой знает только о следующем и не перепрыгивает через него.

```mermaid
flowchart TD
    Client["Клиент (curl, фронтенд)"] --> Router["api/routers/tasks.py\nHTTP: валидация, статусы, HTTPException"]
    Router --> DI["api/dependencies.py\nget_task_service — сборка зависимостей"]
    DI --> Service["services/task.py\nTaskService — бизнес-логика, commit, TaskNotFound"]
    Service --> Repo["repositories/task.py\nTaskRepository — все SQL-запросы"]
    Repo --> Model["models/task.py\nTaskORM — таблица tasks"]
    Model --> DB[("PostgreSQL")]
    Service -.->|model_validate| Schema["schemas/tasks.py\nPydantic-контракты"]
```

| Слой        | Каталог                   | Отвечает за                                                             | Чего делать нельзя                  |
| ----------- | ------------------------- | ----------------------------------------------------------------------- | ----------------------------------- |
| Роутеры     | `app/api/routers/`        | маршруты, статус-коды, преобразование доменных ошибок в `HTTPException` | писать SQL, содержать бизнес-логику |
| DI          | `app/api/dependencies.py` | создание сервисов для роутеров                                          | бизнес-логика                       |
| Сервисы     | `app/services/`           | сценарии, транзакции (`db.commit()`), доменные исключения               | прямые SQL-запросы, знание про HTTP |
| Репозитории | `app/repositories/`       | **все** запросы к SQLAlchemy                                            | `commit()`, бизнес-правила          |
| Кэш         | `app/cache/`              | Redis-кэш (`RedisCache`), создаётся в DI                                | бизнес-логика, SQL                  |
| Модели      | `app/models/`             | ORM-описание таблиц                                                     | Pydantic-валидация                  |
| Схемы       | `app/schemas/`            | контракты API (Pydantic)                                                | SQL, ORM-логика                     |

**Путь одного запроса** (например, `GET /tasks`):

1. FastAPI находит маршрут в `router = APIRouter(prefix="/tasks")` (`app/api/routers/tasks.py`).
2. Внедряется зависимость `task_service` — `get_task_service` из `app/api/dependencies.py`.
3. Она получает SQLAlchemy-сессию через `get_db` (`app/db/session.py`) и создаёт `TaskService(db)`.
4. Сервис просит данные у `TaskRepository.get_all()` — единственное место, где живёт `db.query(TaskORM)`.
5. ORM возвращает объекты `TaskORM`; сервис превращает их в `TaskSchema` через `model_validate` (`from_attributes=True`).
6. Роутер возвращает список; аннотация `-> list[TaskSchema]` используется FastAPI и для валидации, и для OpenAPI-схемы.

Перед обращением к репозиторию сервис проверяет кэш `tasks:all` в Redis: при попадании сразу возвращает данные, при промахе читает БД и заполняет кэш. `POST`, `PATCH` и `DELETE` инвалидируют ключ.

---

## Структура проекта

```
.
├── app/                     # весь код приложения (корень импортов)
│   ├── main.py              # создание FastAPI, lifespan, CORS, include_router
│   ├── api/
│   │   ├── dependencies.py  # DI: get_task_service, get_redis_cache
│   │   └── routers/
│   │       └── tasks.py     # эндпоинты /tasks
│   ├── cache/
│   │   └── redis.py         # RedisCache: get/set/delete
│   ├── core/
│   │   └── config.py        # Config + get_settings() из env
│   ├── db/
│   │   └── session.py       # engine, session_factory, get_db
│   ├── models/
│   │   ├── base.py          # DeclarativeBase с UUID pk
│   │   └── task.py          # TaskORM → таблица tasks
│   ├── repositories/
│   │   └── task.py          # TaskRepository (SQLAlchemy-запросы)
│   ├── schemas/
│   │   └── tasks.py         # TaskSchema, TaskCreateSchema, TaskUpdateSchema
│   └── services/
│       └── task.py          # TaskService, TaskNotFound
├── .agents/skills/fastapi/  # подключённый скилл с best practices FastAPI
├── AGENTS.md                # правила для AI-агентов и контрибьюторов
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

Файлов `__init__.py` нет — это namespace-пакеты, работающие за счёт того, что корень `app/` попадает в `sys.path` (через `cwd` при локальном запуске или через `WORKDIR /app` в контейнере).

### Ключевые файлы

- [`app/main.py`](app/main.py) — точка входа. В `lifespan` вызывает `Base.metadata.create_all(bind=engine)`: таблицы создаются при старте, миграций нет.
- [`app/db/session.py`](app/db/session.py) — `create_engine` выполняется на импорте модуля; `get_db` — генератор, закрывающий сессию в `finally`.
- [`app/models/base.py`](app/models/base.py) — общий `Base`; первичный ключ `id: Mapped[str]` со значением `str(uuid4())`, генерируемым в Python.
- [`app/services/task.py`](app/services/task.py) — единственный слой, вызывающий `db.commit()`; здесь же чтение/запись кэша и его инвалидация.
- [`app/cache/redis.py`](app/cache/redis.py) — тонкая обёртка над `redis.Redis`: `get`/`set`/`delete`, JSON-сериализация, опциональный TTL.

---

## Модель данных

Одна таблица — `tasks`.

| Колонка     | Тип (SQLAlchemy → SQL)     | Ограничения                 | Описание                                     |
| ----------- | -------------------------- | --------------------------- | -------------------------------------------- |
| `id`        | `Mapped[str]` → `VARCHAR`  | `PRIMARY KEY`               | UUID в виде строки, генерируется приложением |
| `title`     | `Mapped[str]` → `VARCHAR`  | `NOT NULL`                  | текст задачи                                 |
| `completed` | `Mapped[bool]` → `BOOLEAN` | `NOT NULL`, `DEFAULT false` | признак выполнения                           |

Схема создаётся автоматически при старте (`Base.metadata.create_all`). Миграций (Alembic) нет: **изменение структуры существующей таблицы потребует ручного SQL или пересоздания БД** (`docker compose down -v`).

---

## API

Базовый префикс — `/tasks` (задаётся на роутере, не в `include_router`). Интерактивная документация — `/docs`.

| Метод    | Путь               | Тело запроса       | Успешный ответ            | Ошибки                                             |
| -------- | ------------------ | ------------------ | ------------------------- | -------------------------------------------------- |
| `GET`    | `/tasks`           | —                  | `200`, `list[TaskSchema]` | —                                                  |
| `GET`    | `/tasks/{task_id}` | —                  | `200`, `TaskSchema`       | `404` — задача не найдена                          |
| `POST`   | `/tasks`           | `TaskCreateSchema` | `201`, `TaskSchema`       | `422` — невалидное тело                            |
| `PATCH`  | `/tasks/{task_id}` | `TaskUpdateSchema` | `200`, `TaskSchema`       | `404` — задача не найдена, `422` — невалидное тело |
| `DELETE` | `/tasks/{task_id}` | —                  | `204`, пустое тело        | `404` — задача не найдена                          |

Путь объявлен как `""` при `prefix="/tasks"`, поэтому канонический URL — `/tasks` без завершающего слэша (`/tasks/` даёт редирект).

### Схемы

```python
class TaskSchema(BaseModel):           # ответ
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    completed: bool = False

class TaskCreateSchema(BaseModel):     # POST
    title: str

class TaskUpdateSchema(BaseModel):     # PATCH (частичное обновление)
    title: str | None = None
    completed: bool | None = False     # ⚠️ см. ограничения
```

Доменные ошибки: `TaskNotFound` объявлен в `app/services/task.py`, роутер переводит его в `HTTPException(status_code=404)`.

---

## Примеры запросов

```bash
# список задач
curl http://localhost:8000/tasks

# получить одну
curl http://localhost:8000/tasks/<id>
# → 200 {"id": "a3f…", "title": "Написать README", "completed": false}

# создать
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Написать README"}'
# → 201 {"id": "a3f…", "title": "Написать README", "completed": false}

# отметить выполненной (шлём оба поля — см. ограничения)
curl -X PATCH http://localhost:8000/tasks/<id> \
  -H "Content-Type: application/json" \
  -d '{"title": "Написать README", "completed": true}'

# удалить
curl -i -X DELETE http://localhost:8000/tasks/<id>
# → 204 No Content
```

---

## Как добавить новую сущность

Цепочка всегда одна и та же — например, для `Project`:

1. **Модель** — `app/models/project.py`: `class ProjectORM(Base)` с `__tablename__ = "projects"`.
2. **Схемы** — `app/schemas/projects.py`: `ProjectSchema` (с `ConfigDict(from_attributes=True)`), `ProjectCreateSchema`, `ProjectUpdateSchema`.
3. **Репозиторий** — `app/repositories/project.py`: класс `ProjectRepository(db)`, только запросы, без `commit()`.
4. **Сервис** — `app/services/project.py`: `ProjectService`, бизнес-правила, `db.commit()`, доменные исключения (`ProjectNotFound`).
5. **DI** — `get_project_service(db: Session = Depends(get_db))` в `app/api/dependencies.py` (в новом коде — через `Annotated`, см. [`AGENTS.md`](AGENTS.md)).
6. **Роутер** — `app/api/routers/projects.py`: `APIRouter(prefix="/projects")`, аннотации возвращаемых типов.
7. **Регистрация** — `app.include_router(project_router)` в `app/main.py`.

Не «срезайте» слои: роутер не должен обращаться к репозиторию напрямую, а репозиторий — коммитить.

---

## Конвенции кода

- Python 3.12, PEP 604 для опциональных типов: `str | None`, без `Optional[...]`.
- Типизированные ORM-колонки: `Mapped[bool] = mapped_column(...)`.
- ORM → Pydantic только через `Schema.model_validate(obj)`.
- Ошибки: доменное исключение в сервисе → `HTTPException(status_code=status.HTTP_*)` в роутере.
- Префикс и общие параметры — на `APIRouter`, а не в `include_router`.
- Аннотация возвращаемого типа вместо `response_model`.
- Новый код — в стиле `Annotated[T, Depends(...)]` (подключённый скилл `.agents/skills/fastapi/SKILL.md`). Существующий код написан в старом стиле `param: T = Depends(...)`; мигрировать постепенно и не смешивать оба стиля в одном файле.
- Git: `add` / `commit` / `push` / `rebase` — только по явной просьбе. Сообщения коммитов — conventional commits, по-английски.

Подробные правила и чеклисты для агентов — в [`AGENTS.md`](AGENTS.md).

---

## Известные ограничения и TODO

Проект учебный, поэтому часть мест намеренно или случайно оставлена «как есть». Полный список с указаниями, что чинить при касании файла, — в [`AGENTS.md`](AGENTS.md#известные-шероховатости-чинить-при-касании-файла). Кратко:

- **`PATCH` сбрасывает `completed`**: у `TaskUpdateSchema.completed` дефолт `False` вместо `None`, поэтому обновление только `title` молча ставит `completed=false`. Обходной путь — всегда передавать оба поля.
- **Нет миграций**: схема создаётся через `create_all`, `Alembic` не подключён.
- **Нет тестов и линтеров**: `pytest`, `ruff` и `pyproject.toml` отсутствуют. Команды `pytest`/`ruff` не существуют — не запускайте их «на всякий случай».
- **Кэш с ручной инвалидацией**: кэшируется только `GET /tasks` (ключ `tasks:all`), TTL не задан, мутации сбрасывают ключ в сервисе. Если Redis недоступен, запрос падает с исключением — fallback на БД нет.
- **CORS-источники продублированы** в `main.py` и `core/config.py`.
- **Нет аутентификации, пагинации, временных меток** (`created_at`/`updated_at`) у задач.
