# BookShelf

**BookShelf** — навчальний проєкт особистої бібліотеки та інфраструктури контрольованої роботи AI-агента (**Agent Harness**). README описує фактичні результати практичних робіт №1–7.

Реалізовано окремий модуль пошуку книг, MCP-сервер, частковий технічний захист Guardrails, два Skills, рольову оркестрацію та семантичний пошук бази знань. Streamlit-інтерфейс, SQLite-сховище, CRUD і керування статусами читання залишаються вимогами: повного вебзастосунку в репозиторії ще немає.

## Результати практичних робіт

| Робота | Фактичний результат |
| --- | --- |
| №1 | Вимоги до застосунку та Agent Harness. |
| №2 | Окрема база знань BookShelf-KB в Obsidian: поняття, компоненти, ADR, словник і зв'язки. |
| №3 | MCP-сервер: доступність, читання, локальний запис та окрема Git-синхронізація нотаток. |
| №4 | Онтологія, політика ALLOW/WARN/BLOCK, PreToolUse hook для захисту ADR і тести. |
| №5 | Skills bookshelf-code-review і bookshelf-adr та оцінювання п'яти сценаріїв їх застосування. |
| №6 | Процес Planner → Coder → Reviewer, промпти, JSON Schema та завершений цикл створення пошуку книг. |
| №7 | Embeddings, локальний індекс, семантичний MCP-пошук і порівняння з keyword на 10 запитах. |

## Призначення й технології

Мета бібліотеки — облік книг, пошук за назвою чи автором і відстеження читання. Наявний `search_books(books, query)` у `search.py` шукає буквальний фрагмент у `title` або `author` через Unicode `casefold()`. Порожній після `strip()` запит повертає весь каталог; порядок зберігається, вхідні записи не змінюються. Модуль працює з переданими даними в пам'яті та ще не інтегрований з UI чи БД.

| Технологія | Використання |
| --- | --- |
| Python | Пошук книг, MCP, retrieval, індексатор і hook. |
| MCP Python SDK / FastMCP | Сервер BookShelf-KB через транспорт stdio. |
| sentence-transformers | Багатомовні embeddings нотаток і запитів. |
| NumPy | Вектори, косинусне ранжування та індекс .npz. |
| pytest | Тести пошуку книг, retrieval і hook. |
| Obsidian, Markdown, YAML | Окрема база знань, метадані й зв'язки. |
| Git, GitHub | Версіонування проєкту та окремого KB-репозиторію. |
| Codex CLI | Агент, Skills і послідовні рольові сесії. |
| Streamlit, SQLite | Обрані у вимогах; UI та сховище ще не реалізовані. |

## Структура проєкту

```text
BookShelf/
├── README.md
├── search.py                         # пошук книг
├── mcp-server/
│   ├── server.py                     # MCP-інструменти
│   ├── retrieval.py                  # Markdown, embeddings, індекс, пошук
│   └── requirements.txt              # залежності MCP, RAG і тестів
├── scripts/
│   ├── build_kb_index.py             # CLI індексації
│   └── guardrails_hook.py            # перевірка PreToolUse
├── tests/
│   ├── test_search.py
│   ├── test_kb_retrieval.py
│   └── test_guardrails_hook.py
├── .codex/hooks.json                 # конфігурація hook
├── .agents/skills/
│   ├── bookshelf-code-review/SKILL.md
│   └── bookshelf-adr/SKILL.md
├── orchestration/
│   ├── prompts/                      # Planner, Coder, Reviewer
│   └── schemas/handoff.schema.json
├── artifacts/
│   ├── orchestration/                # плани, погодження, звіти ролей
│   └── kb-index/index.npz            # локальний індекс, виключений із Git
└── docs/                             # вимоги, правила й оцінювання
```

Основні документи: [вимоги застосунку](docs/app-requirements.md), [вимоги Harness](docs/harness-requirements.md), [онтологія](docs/ontology.md), [Guardrails](docs/guardrails.md), [перевірки Guardrails](docs/guardrails-test-cases.md), [оцінювання Skills](docs/skills-evaluation.md), [оркестрація](docs/orchestration.md), [retrieval](docs/kb-retrieval.md), [порівняння пошуку](docs/rag-evaluation.md).

## BookShelf-KB: окрема база знань

BookShelf-KB — окремий Git-репозиторій та Obsidian vault поза каталогом застосунку. Типовий шлях — `C:\Users\user\BookShelf-KB`; налаштовується через `BOOKSHELF_KB_PATH`. Агент отримує контекст через MCP, а сервер та індексатор працюють із Vault локально.

У базі є `Concepts/`, `Components/`, `Decisions/`, `Glossary/`, `Templates/`, карта змісту `BookShelf MOC.md` і README. Нотатки описують Book, Reading Status, Streamlit UI, SQLite Storage, Agent Harness, рішення про стек, відокремлення KB та MCP-інтеграцію. Наявність опису компонента не доводить його реалізації в коді.

Онтологія визначає типи `concept`, `component`, `decision`, `glossary`, YAML frontmatter та спрямовані зв'язки `depends_on`, `implements`, `documents`, `supersedes`. Посилання між нотатками використовують Obsidian wikilinks.

## MCP-сервер та інструменти

`mcp-server/server.py` створює FastMCP-сервер **BookShelf-KB** із транспортом `stdio`.

| Інструмент | Реалізована дія |
| --- | --- |
| `ping()` | Повідомлення про доступність сервера. |
| `get_note(category, title)` | Читання нотатки; за відсутності — NOT_FOUND. |
| `ingest_note(category, title, content, links=None)` | Локальне створення або заміна без мережі; однаковий сформований вміст дає UNCHANGED. |
| `sync_note(category, title)` | Git add/commit конкретної нотатки та push; результат SYNCED, UNCHANGED або SYNC_ERROR. |
| `search_notes(query, top_k=5)` | Семантичні результати з path, fragment, score; у разі помилки — порожні results та error. |

Для читання, запису й синхронізації підтримуються категорії `Components`, `Concepts`, `Decisions`, `Glossary`. Семантичний пошук охоплює також кореневі Markdown-файли й Templates.

`ingest_note` формує frontmatter заново та не зберігає довільні попередні YAML-поля або текст. `sync_note` відправляє гілку, тому може відправити також попередні локальні коміти. Запис і синхронізація — окремі дії з окремим погодженням. Після зміни коду сервера MCP-підключення потрібно перезапустити.

## Agent Harness, Guardrails і Hooks

Harness поєднує код, документацію, KB, MCP, правила, Skills, передачі між ролями та докази перевірок. Це інфраструктура розробки.

- **ALLOW:** потрібне читання проєкту, KB через MCP, безпечні локальні тести та документація в погоджених межах.
- **WARN:** зміни основного коду, ADR і push/sync потребують явного погодження конкретного обсягу.
- **BLOCK:** видалення ADR, видалення всієї KB та прямий push у main без погодженого процесу перевірки й прийняття.

У `.codex/hooks.json` налаштовано **PreToolUse**, що запускає `scripts/guardrails_hook.py`. Hook аналізує JSON-подію та розпізнає певні операції видалення захищеного `BookShelf-KB/Decisions` через shell, patch і MCP-інструменти видалення. Для забороненої дії повертає deny з BL-01. Конфігурація містить абсолютні Windows-шляхи поточного середовища.

Це частковий захист: автоматичне погодження WARN та перевірка push у main цим hook не реалізовані. У [звіті ПР4](docs/guardrails-test-cases.md) зафіксовано блокування BL-01 у тестовій конфігурації зі збереженням sandbox-файла. Після відновлення робочої конфігурації інтеграційний тест не повторювався. Конфігурація та unit-тести не доводять активності hook у кожній новій сесії.

## Skills і мультиагентна оркестрація

Створено два локальні Skills:

- [bookshelf-code-review](.agents/skills/bookshelf-code-review/SKILL.md) — рев'ю коду або diff з перевіркою вимог, KB-контексту та Guardrails, без автоматичних виправлень.
- [bookshelf-adr](.agents/skills/bookshelf-adr/SKILL.md) — підготовка проєкту ADR із контекстом через MCP; запис нової нотатки лише після явного погодження.

[Оцінювання ПР5](docs/skills-evaluation.md) охоплює три сценарії рев'ю та два проєкти ADR зі статусом proposed. Це оцінювання поведінки Skills, а не п'ять автоматизованих тестів застосунку; у цих сценаріях KB не змінювалася.

Оркестрація — послідовні окремі рольові сесії **Planner → погодження → Coder → Reviewer**, з повтором Coder/Reviewer за потреби. Переходи перевіряє оператор; автоматичного runner немає. Промпти задають обов'язки ролей, JSON Schema — структуру handoff із планом, дозволеними файлами, тестами, зауваженнями й обмеженнями.

Завершений цикл `bookshelf-search-plan-20261109-001` створив `search.py` і його тести. Фінальний Reviewer повернув pass, зауваження закрито. План, погодження, попередні й фінальні handoff та джерела доказів збережено в [артефактах циклу](artifacts/orchestration/bookshelf-search-plan-20261109-001/cycle-summary.md). Інтеграція з UI/SQLite до циклу не входила.

## RAG: embeddings, індексація та семантичний пошук

Реалізовано retrieval-частину RAG для контексту агента; автоматичного конвеєра генерації відповіді немає.

1. Індексатор читає Markdown із Vault, виключаючи приховані шляхи й символічні посилання.
2. Retrieval прибирає YAML frontmatter та ділить текст за ATX/Setext-заголовками, зберігаючи fenced code.
3. Модель `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` створює embeddings фрагментів.
4. Нормалізовані вектори та JSON-метадані атомарно зберігаються в `artifacts/kb-index/index.npz`. Vault не змінюється.
5. Запит кодується тією самою моделлю; скалярний добуток нормалізованих векторів дає косинусну подібність для top-k.

Метадані містять модель, корінь Vault, шляхи, фрагменти та SHA-256 нотаток. Перед пошуком перевіряються набір файлів і хеші: після зміни, додавання або видалення нотатки потрібна явна перебудова. Пошук не перебудовує індекс і не завантажує модель із мережі. Ранжуються фрагменти, тому одна нотатка може займати кілька місць; score не є ймовірністю.

## Тестування та порівняння keyword/semantic

| Перевірка | Зафіксований результат і межі |
| --- | --- |
| Пошук книг | У підсумку ПР6: **41 passed in 0.30s**, повідомлено користувачем; незалежний запуск агента тоді не відбувся через несправне .venv. |
| Hook | У звіті ПР4: повідомлено **9 успішних unit-тестів**; окремо зафіксовано інтеграційне блокування BL-01 у тестовій конфігурації. |
| Retrieval | Тести перевіряють розбиття Markdown, індекс, ранжування, валідацію та застарівання на тимчасовому Vault із детермінованим encoder без мережі. Це не оцінка якості справжньої моделі; за відсутності NumPy/MCP відповідні тести пропускаються. |
| Семантичний MCP | У ПР7: **10 викликів**, кожен повернув **5 результатів без помилок**, на базі з 13 Markdown-файлів. |

Під час оновлення README повторний запуск `.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider` завершився до запуску pytest: середовище посилається на відсутній `C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe`. Поточний повний прогін тестів не підтверджено.

[Порівняння ПР7](docs/rag-evaluation.md) використовує 10 тематичних запитів із вручну визначеною основною цільовою нотаткою. Keyword — окремий експериментальний пошук точних токенів із OR та стоп-словами; такого MCP-інструмента немає. Він відрізняється від пошуку книг у search.py.

| Метод | Hit@1 | Hit@5 |
| --- | --- | --- |
| Keyword | 8/10 | 9/10 |
| Семантичний | 6/10 | 8/10 |

Hit@k означає наявність шляху цільової нотатки серед перших k результатів, а не повноту відповіді. На цій малій вибірці keyword кращий за метриками, зокрема для точного CRUD. Семантика знаходила зміст про статуси, UI та MCP, але пропускала деякі джерела й іноді піднімала шаблони або самі заголовки. Швидкодію не порівнювали. Гібридний пошук і групування за нотаткою залишаються рекомендаціями.

## Встановлення та запуск

Команди PowerShell виконуються з кореня BookShelf. Потрібні працездатний Python, Git і окремо підготовлений Vault BookShelf-KB. Створення середовища нижче — для нового встановлення; несправне наявне середовище слід спочатку відновити.

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\.venv\Scripts\Activate.ps1
python -m pip install -r mcp-server/requirements.txt

$env:BOOKSHELF_KB_PATH = 'C:\Users\user\BookShelf-KB'

# Усі тести без запису bytecode та кешу pytest
python -B -m pytest -q -p no:cacheprovider

# Окремі набори
python -B -m pytest tests/test_search.py -q -p no:cacheprovider
python -B -m pytest tests/test_guardrails_hook.py -q -p no:cacheprovider
python -B -m pytest tests/test_kb_retrieval.py -q -p no:cacheprovider

# Перша побудова: дозволяє завантаження моделі
python -B scripts/build_kb_index.py --allow-download

# Перебудова з моделлю в локальному кеші
python -B scripts/build_kb_index.py

# Сервер stdio для підключення MCP-клієнтом
python -B mcp-server/server.py
```

Індексатор підтримує `--vault`, `--index-dir`, `--model`. MCP використовує стандартний `artifacts/kb-index/index.npz`, тому для його роботи залишайте стандартний `--index-dir`. Індекс не зберігається в Git. Команди запуску Streamlit немає: вебінтерфейс ще не створено.

Репозиторій: [TarasZhuk-333/BookShelf](https://github.com/TarasZhuk-333/BookShelf). BookShelf-KB версіонується окремо.
