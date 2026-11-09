# Практична №7: порівняльне тестування пошуку BookShelf-KB

Дата: 2026-11-09. Джерело: `C:\Users\user\BookShelf-KB`, 13 Markdown-файлів. Виконано 10 окремих викликів `bookshelf-kb.search_notes(query, top_k=5)`; усі повернули по 5 результатів без помилок. Попередній пошук з іншого turn не використано.

## Методика

У поточному MCP та перевіреному сервері keyword-інструмент відсутній. Для базового порівняння прочитано локальні Markdown-файли та виконано пошук у пам'яті JavaScript; застосунок не змінено. YAML frontmatter вилучено, приховані шляхи виключено. Keyword шукає цілі токени без урахування регістру, без стемінгу/лематизації/синонімів, за умовою OR. Токенізація: Unicode літери, цифри, `_`, внутрішній апостроф. Повторені слова запиту рахуються один раз. Стоп-слова: `які, та, з, них, де, й, що, чому, як, до, через, для, в, у, за, на, і, це, має, може, яким, яких`. Оцінка keyword = кількість різних знайдених слів / кількість різних слів запиту після фільтрації; нульові результати вилучено; максимум 5 нотаток; за однакових оцінок — лексикографічний порядок повного шляху. Фрагменти keyword — рядки з точними збігами.

Семантичний пошук ранжує **фрагменти**, а не унікальні нотатки: повторення шляхів збережено. За поточною реалізацією використано `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, нормалізовані вектори та косинусну подібність. MCP перевіряє відповідність SHA-256 файлів індексу перед пошуком; індекс не перебудовувався. Косинусна оцінка не є ймовірністю і не порівнюється чисельно з keyword-оцінкою. Результати в таблиці округлено до 6 знаків; точні MCP-оцінки й фрагменти наведено нижче.

Для кожного запиту за прочитаним Vault вручну визначено одну основну цільову нотатку. Hit@k означає наявність її шляху серед перших k результатів, а не повноту відповіді у фрагменті. Це мала тематична вибірка, а не універсальна оцінка якості.

## Таблиця 10 запитів

| № | Запит / основна ціль | Keyword: фактичний top-5 (оцінка) | Семантичний: фактичний top-5 (оцінка) | Аналіз |
|---|---|---|---|---|
| 1 | Які технології використовуються в BookShelf?<br>Ціль: `Decisions/ADR-001 Technology Stack.md` | 1. `BookShelf MOC.md` — 0.333333<br>2. `Components/Agent Harness.md` — 0.333333<br>3. `Concepts/Book.md` — 0.333333<br>4. `Decisions/ADR-002 Separate Knowledge Base.md` — 0.333333<br>5. `Decisions/ADR-003 MCP Integration.md` — 0.333333 | 1. `README.md` — 0.622816<br>2. `BookShelf MOC.md` — 0.559699<br>3. `Glossary/BookShelf Glossary.md` — 0.544387<br>4. `Components/Agent Harness.md` — 0.542333<br>5. `Concepts/Book.md` — 0.463585 | Обидва методи пропустили ADR-001: слово BookShelf дає загальний шум, а семантика підняла README. |
| 2 | Які поля має книга та які з них обов'язкові?<br>Ціль: `Concepts/Book.md` | 1. `Concepts/Book.md` — 1.000000 | 1. `Concepts/Book.md` — 0.517669<br>2. `README.md` — 0.507396<br>3. `BookShelf MOC.md` — 0.419158<br>4. `Components/Agent Harness.md` — 0.398633<br>5. `Glossary/BookShelf Glossary.md` — 0.379264 | Семантика поставила Book першою; keyword знаходить її за точними словами полів/обов'язковості. |
| 3 | Які значення може мати статус читання книги?<br>Ціль: `Concepts/Reading Status.md` | 1. `Concepts/Reading Status.md` — 0.600000<br>2. `Components/Agent Harness.md` — 0.200000<br>3. `Components/SQLite Storage.md` — 0.200000<br>4. `Glossary/BookShelf Glossary.md` — 0.200000 | 1. `Concepts/Reading Status.md` — 0.718875<br>2. `BookShelf MOC.md` — 0.563055<br>3. `Concepts/Book.md` — 0.555718<br>4. `BookShelf MOC.md` — 0.439874<br>5. `README.md` — 0.430701 | Семантика розпізнала тему й поставила Reading Status першою; keyword також знаходить точні слова. |
| 4 | Де зберігаються книги та які операції підтримує сховище?<br>Ціль: `Components/SQLite Storage.md` | 1. `Components/SQLite Storage.md` — 0.200000<br>2. `Concepts/Reading Status.md` — 0.200000 | 1. `Components/Agent Harness.md` — 0.464934<br>2. `README.md` — 0.459592<br>3. `Glossary/BookShelf Glossary.md` — 0.432462<br>4. `BookShelf MOC.md` — 0.414416<br>5. `Components/SQLite Storage.md` — 0.367988 | Семантика знайшла SQLite Storage лише п'ятою; keyword залежить від буквальних «книги» та «операції», а не від синоніма «сховище». |
| 5 | Що дозволяє робити вебінтерфейс користувача?<br>Ціль: `Components/Streamlit UI.md` | 1. `Components/Streamlit UI.md` — 0.250000 | 1. `Components/Streamlit UI.md` — 0.567391<br>2. `Decisions/ADR-001 Technology Stack.md` — 0.375731<br>3. `Glossary/BookShelf Glossary.md` — 0.373440<br>4. `Decisions/ADR-002 Separate Knowledge Base.md` — 0.363401<br>5. `Decisions/ADR-001 Technology Stack.md` — 0.326096 | Семантика поставила Streamlit UI першою. Keyword також має буквальний збіг «вебінтерфейс», але не розуміє значення решти запиту. |
| 6 | Чому базу знань відокремлено від коду застосунку?<br>Ціль: `Decisions/ADR-002 Separate Knowledge Base.md` | 1. `Decisions/ADR-002 Separate Knowledge Base.md` — 0.666667<br>2. `Components/Agent Harness.md` — 0.166667<br>3. `Components/SQLite Storage.md` — 0.166667<br>4. `Concepts/Book.md` — 0.166667<br>5. `Decisions/ADR-003 MCP Integration.md` — 0.166667 | 1. `Decisions/ADR-002 Separate Knowledge Base.md` — 0.616315<br>2. `Decisions/ADR-002 Separate Knowledge Base.md` — 0.609782<br>3. `Decisions/ADR-003 MCP Integration.md` — 0.601258<br>4. `Decisions/ADR-002 Separate Knowledge Base.md` — 0.533085<br>5. `BookShelf MOC.md` — 0.517237 | Семантика знаходить ADR-002, але перший фрагмент — тільки заголовок; корисний наслідок є четвертим. |
| 7 | Як агент підключається до бази знань через MCP?<br>Ціль: `Decisions/ADR-003 MCP Integration.md` | 1. `Components/Agent Harness.md` — 0.400000<br>2. `Decisions/ADR-002 Separate Knowledge Base.md` — 0.400000<br>3. `Decisions/ADR-003 MCP Integration.md` — 0.400000<br>4. `Decisions/BookShelf GitHub Development History.md` — 0.200000<br>5. `Glossary/BookShelf Glossary.md` — 0.200000 | 1. `Decisions/ADR-003 MCP Integration.md` — 0.679608<br>2. `Components/Agent Harness.md` — 0.601006<br>3. `Decisions/ADR-002 Separate Knowledge Base.md` — 0.498709<br>4. `Decisions/ADR-003 MCP Integration.md` — 0.487228<br>5. `Decisions/BookShelf GitHub Development History.md` — 0.480288 | Семантика повертає зміст ADR-003 першим; keyword знаходить MCP, але не розуміє перефразування «підключається». |
| 8 | Які шари заплановані для Agent Harness?<br>Ціль: `Components/Agent Harness.md` | 1. `Components/Agent Harness.md` — 0.750000<br>2. `BookShelf MOC.md` — 0.500000<br>3. `Decisions/ADR-002 Separate Knowledge Base.md` — 0.500000<br>4. `Decisions/ADR-003 MCP Integration.md` — 0.500000<br>5. `Decisions/BookShelf GitHub Development History.md` — 0.500000 | 1. `Components/Agent Harness.md` — 0.655090<br>2. `Decisions/ADR-003 MCP Integration.md` — 0.455511<br>3. `Decisions/BookShelf GitHub Development History.md` — 0.442952<br>4. `Glossary/BookShelf Glossary.md` — 0.426611<br>5. `Decisions/ADR-003 MCP Integration.md` — 0.414533 | Обидва методи використовують Agent Harness; семантика повернула саме опис запланованих шарів першим. |
| 9 | Що означає CRUD?<br>Ціль: `Glossary/BookShelf Glossary.md` | 1. `Glossary/BookShelf Glossary.md` — 0.500000 | 1. `Templates/Note Template.md` — 0.437239<br>2. `Templates/Note Template.md` — 0.298099<br>3. `Concepts/Reading Status.md` — 0.258569<br>4. `Templates/Note Template.md` — 0.240420<br>5. `Glossary/BookShelf Glossary.md` — 0.231607 | Keyword точно знаходить CRUD у словнику; семантика ставить сторонній шаблон першим, словник лише п'ятим. |
| 10 | Які коміти зафіксовані в історії розробки BookShelf?<br>Ціль: `Decisions/BookShelf GitHub Development History.md` | 1. `Decisions/BookShelf GitHub Development History.md` — 0.400000<br>2. `BookShelf MOC.md` — 0.200000<br>3. `Components/Agent Harness.md` — 0.200000<br>4. `Concepts/Book.md` — 0.200000<br>5. `Decisions/ADR-002 Separate Knowledge Base.md` — 0.200000 | 1. `README.md` — 0.577030<br>2. `BookShelf MOC.md` — 0.556367<br>3. `Concepts/Book.md` — 0.521952<br>4. `Glossary/BookShelf Glossary.md` — 0.488838<br>5. `Components/Agent Harness.md` — 0.447789 | Семантика пропустила історію комітів; keyword може знайти «розробки», але загальне BookShelf створює нічиї. |

Keyword: Hit@1 = 8/10; Hit@5 = 9/10.

Семантичний: Hit@1 = 6/10; Hit@5 = 8/10.

## Короткий аналіз

Keyword простий, прозорий і корисний для точних ідентифікаторів: CRUD. Він не потребує embedding-моделі, але відмінювання та синоніми погіршують збіги; загальні слова BookShelf й «розробки» дають шум, а лексикографічне розв'язання нічиїх не оцінює зміст. Семантика розуміє запити про інтерфейс, статуси й інтеграцію, проте не гарантує корисної відповіді: запити 1 та 10 пропускають основне джерело, а запит 9 віддає перевагу шаблону перед точним CRUD. Високий score README у запиті 1 (0.622816) не означає, що знайдено перелік технологій. Кілька фрагментів тієї самої нотатки займають місця top-5 (запити 3, 5, 6–9); сам заголовок теж може бути першим результатом.

Практичний напрям покращення: комбінувати keyword і семантику, групувати результати за нотаткою та додавати сусідній зміст до заголовків. Це рекомендації; реалізацію не змінено. Швидкодію не порівнювали: час MCP включає завантаження моделі й транспорт, а keyword працював по вже прочитаних текстах.

## Фактичні фрагменти та повні оцінки

### 1. Які технології використовуються в BookShelf?

Keyword, слова запиту: `технології`, `використовуються`, `bookshelf`.

```json
[
  {
    "path": "BookShelf MOC.md",
    "score": 0.3333333333333333,
    "matched": [
      "bookshelf"
    ],
    "fragment": "# BookShelf — Map of Content\n- [[BookShelf Glossary]]"
  },
  {
    "path": "Components/Agent Harness.md",
    "score": 0.3333333333333333,
    "matched": [
      "bookshelf"
    ],
    "fragment": "Інфраструктура для контрольованої роботи Codex CLI над BookShelf."
  },
  {
    "path": "Concepts/Book.md",
    "score": 0.3333333333333333,
    "matched": [
      "bookshelf"
    ],
    "fragment": "**Книга** — основна сутність застосунку BookShelf."
  },
  {
    "path": "Decisions/ADR-002 Separate Knowledge Base.md",
    "score": 0.3333333333333333,
    "matched": [
      "bookshelf"
    ],
    "fragment": "Зберігати Obsidian vault у власному Git-репозиторії `BookShelf-KB`. Для доступу агента в наступній практичній роботі передбачити MCP-конектор."
  },
  {
    "path": "Decisions/ADR-003 MCP Integration.md",
    "score": 0.3333333333333333,
    "matched": [
      "bookshelf"
    ],
    "fragment": "Для інтеграції Agent Harness із базою знань BookShelf використовується власний MCP-сервер на Python."
  }
]
```

Фактична відповідь MCP:

```json
{
  "results": [
    {
      "path": "README.md",
      "fragment": "# BookShelf Knowledge Base",
      "score": 0.6228156685829163
    },
    {
      "path": "BookShelf MOC.md",
      "fragment": "# BookShelf — Map of Content",
      "score": 0.5596990585327148
    },
    {
      "path": "Glossary/BookShelf Glossary.md",
      "fragment": "# BookShelf Glossary\n\n- **Book** — запис про книгу; див. [[Book]].\n- **Reading Status** — стан читання; див. [[Reading Status]].\n- **CRUD** — створення, читання, оновлення, видалення.\n- **Vault** — папка нотаток Obsidian.\n- **MCP** — Model Context Protocol, протокол інтеграції інструментів з агентом.\n- **Agent Harness** — інфраструктура контрольованої роботи агента; див. [[Agent Harness]].",
      "score": 0.5443868637084961
    },
    {
      "path": "Components/Agent Harness.md",
      "fragment": "# Agent Harness\n\nІнфраструктура для контрольованої роботи Codex CLI над BookShelf.\n\nПлановані шари: джерела даних, база знань, MCP-конектор, guardrails, skills, orchestration, evaluation.\n\nБаза знань зберігається окремо: [[ADR-002 Separate Knowledge Base]].\n\n**Статус:** заплановано; реалізація відбуватиметься в наступних практичних роботах.",
      "score": 0.5423329472541809
    },
    {
      "path": "Concepts/Book.md",
      "fragment": "# Book\n\n**Книга** — основна сутність застосунку BookShelf.\n\nПоля: `id`, `title`, `author`, `status`, `created_at`.\n\nНазва й автор обов'язкові. Ідентифікатор унікальний.\n\nПов'язані нотатки: [[Reading Status]], [[SQLite Storage]], [[Streamlit UI]].",
      "score": 0.4635847508907318
    }
  ]
}
```

### 2. Які поля має книга та які з них обов'язкові?

Keyword, слова запиту: `поля`, `книга`, `обов'язкові`.

```json
[
  {
    "path": "Concepts/Book.md",
    "score": 1,
    "matched": [
      "поля",
      "книга",
      "обов'язкові"
    ],
    "fragment": "**Книга** — основна сутність застосунку BookShelf.\nПоля: `id`, `title`, `author`, `status`, `created_at`.\nНазва й автор обов'язкові. Ідентифікатор унікальний."
  }
]
```

Фактична відповідь MCP:

```json
{
  "results": [
    {
      "path": "Concepts/Book.md",
      "fragment": "# Book\n\n**Книга** — основна сутність застосунку BookShelf.\n\nПоля: `id`, `title`, `author`, `status`, `created_at`.\n\nНазва й автор обов'язкові. Ідентифікатор унікальний.\n\nПов'язані нотатки: [[Reading Status]], [[SQLite Storage]], [[Streamlit UI]].",
      "score": 0.5176692605018616
    },
    {
      "path": "README.md",
      "fragment": "# BookShelf Knowledge Base",
      "score": 0.5073962211608887
    },
    {
      "path": "BookShelf MOC.md",
      "fragment": "# BookShelf — Map of Content",
      "score": 0.4191575050354004
    },
    {
      "path": "Components/Agent Harness.md",
      "fragment": "# Agent Harness\n\nІнфраструктура для контрольованої роботи Codex CLI над BookShelf.\n\nПлановані шари: джерела даних, база знань, MCP-конектор, guardrails, skills, orchestration, evaluation.\n\nБаза знань зберігається окремо: [[ADR-002 Separate Knowledge Base]].\n\n**Статус:** заплановано; реалізація відбуватиметься в наступних практичних роботах.",
      "score": 0.39863306283950806
    },
    {
      "path": "Glossary/BookShelf Glossary.md",
      "fragment": "# BookShelf Glossary\n\n- **Book** — запис про книгу; див. [[Book]].\n- **Reading Status** — стан читання; див. [[Reading Status]].\n- **CRUD** — створення, читання, оновлення, видалення.\n- **Vault** — папка нотаток Obsidian.\n- **MCP** — Model Context Protocol, протокол інтеграції інструментів з агентом.\n- **Agent Harness** — інфраструктура контрольованої роботи агента; див. [[Agent Harness]].",
      "score": 0.37926435470581055
    }
  ]
}
```

### 3. Які значення може мати статус читання книги?

Keyword, слова запиту: `значення`, `мати`, `статус`, `читання`, `книги`.

```json
[
  {
    "path": "Concepts/Reading Status.md",
    "score": 0.6,
    "matched": [
      "статус",
      "читання",
      "книги"
    ],
    "fragment": "Статус читання книги має одне з трьох значень:\nСтатус належить сутності [[Book]] і змінюється через [[Streamlit UI]]."
  },
  {
    "path": "Components/Agent Harness.md",
    "score": 0.2,
    "matched": [
      "статус"
    ],
    "fragment": "**Статус:** заплановано; реалізація відбуватиметься в наступних практичних роботах."
  },
  {
    "path": "Components/SQLite Storage.md",
    "score": 0.2,
    "matched": [
      "читання"
    ],
    "fragment": "Основні операції: створення, читання, оновлення та видалення записів [[Book]]."
  },
  {
    "path": "Glossary/BookShelf Glossary.md",
    "score": 0.2,
    "matched": [
      "читання"
    ],
    "fragment": "- **Reading Status** — стан читання; див. [[Reading Status]].\n- **CRUD** — створення, читання, оновлення, видалення."
  }
]
```

Фактична відповідь MCP:

```json
{
  "results": [
    {
      "path": "Concepts/Reading Status.md",
      "fragment": "# Reading Status\n\nСтатус читання книги має одне з трьох значень:\n- `To Read` — планується прочитати;\n- `Reading` — читається;\n- `Read` — прочитано.\n\nСтатус належить сутності [[Book]] і змінюється через [[Streamlit UI]].",
      "score": 0.7188748121261597
    },
    {
      "path": "BookShelf MOC.md",
      "fragment": "## Поняття\n- [[Book]]\n- [[Reading Status]]",
      "score": 0.5630553364753723
    },
    {
      "path": "Concepts/Book.md",
      "fragment": "# Book\n\n**Книга** — основна сутність застосунку BookShelf.\n\nПоля: `id`, `title`, `author`, `status`, `created_at`.\n\nНазва й автор обов'язкові. Ідентифікатор унікальний.\n\nПов'язані нотатки: [[Reading Status]], [[SQLite Storage]], [[Streamlit UI]].",
      "score": 0.5557176470756531
    },
    {
      "path": "BookShelf MOC.md",
      "fragment": "# BookShelf — Map of Content",
      "score": 0.4398740231990814
    },
    {
      "path": "README.md",
      "fragment": "# BookShelf Knowledge Base",
      "score": 0.4307006597518921
    }
  ]
}
```

### 4. Де зберігаються книги та які операції підтримує сховище?

Keyword, слова запиту: `зберігаються`, `книги`, `операції`, `підтримує`, `сховище`.

```json
[
  {
    "path": "Components/SQLite Storage.md",
    "score": 0.2,
    "matched": [
      "операції"
    ],
    "fragment": "Основні операції: створення, читання, оновлення та видалення записів [[Book]]."
  },
  {
    "path": "Concepts/Reading Status.md",
    "score": 0.2,
    "matched": [
      "книги"
    ],
    "fragment": "Статус читання книги має одне з трьох значень:"
  }
]
```

Фактична відповідь MCP:

```json
{
  "results": [
    {
      "path": "Components/Agent Harness.md",
      "fragment": "# Agent Harness\n\nІнфраструктура для контрольованої роботи Codex CLI над BookShelf.\n\nПлановані шари: джерела даних, база знань, MCP-конектор, guardrails, skills, orchestration, evaluation.\n\nБаза знань зберігається окремо: [[ADR-002 Separate Knowledge Base]].\n\n**Статус:** заплановано; реалізація відбуватиметься в наступних практичних роботах.",
      "score": 0.46493422985076904
    },
    {
      "path": "README.md",
      "fragment": "# BookShelf Knowledge Base",
      "score": 0.45959189534187317
    },
    {
      "path": "Glossary/BookShelf Glossary.md",
      "fragment": "# BookShelf Glossary\n\n- **Book** — запис про книгу; див. [[Book]].\n- **Reading Status** — стан читання; див. [[Reading Status]].\n- **CRUD** — створення, читання, оновлення, видалення.\n- **Vault** — папка нотаток Obsidian.\n- **MCP** — Model Context Protocol, протокол інтеграції інструментів з агентом.\n- **Agent Harness** — інфраструктура контрольованої роботи агента; див. [[Agent Harness]].",
      "score": 0.43246155977249146
    },
    {
      "path": "BookShelf MOC.md",
      "fragment": "# BookShelf — Map of Content",
      "score": 0.4144158363342285
    },
    {
      "path": "Components/SQLite Storage.md",
      "fragment": "# SQLite Storage\n\nЛокальна база даних SQLite з таблицею `books`.\n\nОсновні операції: створення, читання, оновлення та видалення записів [[Book]].\n\nВалідація значень [[Reading Status]] виконується на рівні застосунку; за потреби — обмеженням у схемі БД.\n\nДив. [[ADR-001 Technology Stack]].",
      "score": 0.3679881691932678
    }
  ]
}
```

### 5. Що дозволяє робити вебінтерфейс користувача?

Keyword, слова запиту: `дозволяє`, `робити`, `вебінтерфейс`, `користувача`.

```json
[
  {
    "path": "Components/Streamlit UI.md",
    "score": 0.25,
    "matched": [
      "вебінтерфейс"
    ],
    "fragment": "Мінімальний вебінтерфейс для перегляду списку книг, додавання, редагування, видалення, пошуку та зміни статусу."
  }
]
```

Фактична відповідь MCP:

```json
{
  "results": [
    {
      "path": "Components/Streamlit UI.md",
      "fragment": "# Streamlit UI\n\nМінімальний вебінтерфейс для перегляду списку книг, додавання, редагування, видалення, пошуку та зміни статусу.\n\nІнтерфейс взаємодіє з [[SQLite Storage]] і відображає сутності [[Book]].\n\nТехнологічне рішення: [[ADR-001 Technology Stack]].",
      "score": 0.5673909783363342
    },
    {
      "path": "Decisions/ADR-001 Technology Stack.md",
      "fragment": "## Контекст\nПотрібен невеликий локальний застосунок із простим інтерфейсом та автоматизованими тестами.",
      "score": 0.37573084235191345
    },
    {
      "path": "Glossary/BookShelf Glossary.md",
      "fragment": "# BookShelf Glossary\n\n- **Book** — запис про книгу; див. [[Book]].\n- **Reading Status** — стан читання; див. [[Reading Status]].\n- **CRUD** — створення, читання, оновлення, видалення.\n- **Vault** — папка нотаток Obsidian.\n- **MCP** — Model Context Protocol, протокол інтеграції інструментів з агентом.\n- **Agent Harness** — інфраструктура контрольованої роботи агента; див. [[Agent Harness]].",
      "score": 0.3734399974346161
    },
    {
      "path": "Decisions/ADR-002 Separate Knowledge Base.md",
      "fragment": "## Наслідки\nОкреме версіонування знань і контрольований доступ через [[Agent Harness]].",
      "score": 0.36340102553367615
    },
    {
      "path": "Decisions/ADR-001 Technology Stack.md",
      "fragment": "## Наслідки\nШвидка розробка, мінімум залежностей, просте локальне тестування.\n\nПов'язані компоненти: [[Streamlit UI]], [[SQLite Storage]].",
      "score": 0.32609638571739197
    }
  ]
}
```

### 6. Чому базу знань відокремлено від коду застосунку?

Keyword, слова запиту: `базу`, `знань`, `відокремлено`, `від`, `коду`, `застосунку`.

```json
[
  {
    "path": "Decisions/ADR-002 Separate Knowledge Base.md",
    "score": 0.6666666666666666,
    "matched": [
      "знань",
      "від",
      "коду",
      "застосунку"
    ],
    "fragment": "База знань повинна бути відокремлена від коду застосунку.\nОкреме версіонування знань і контрольований доступ через [[Agent Harness]]."
  },
  {
    "path": "Components/Agent Harness.md",
    "score": 0.16666666666666666,
    "matched": [
      "знань"
    ],
    "fragment": "Плановані шари: джерела даних, база знань, MCP-конектор, guardrails, skills, orchestration, evaluation.\nБаза знань зберігається окремо: [[ADR-002 Separate Knowledge Base]]."
  },
  {
    "path": "Components/SQLite Storage.md",
    "score": 0.16666666666666666,
    "matched": [
      "застосунку"
    ],
    "fragment": "Валідація значень [[Reading Status]] виконується на рівні застосунку; за потреби — обмеженням у схемі БД."
  },
  {
    "path": "Concepts/Book.md",
    "score": 0.16666666666666666,
    "matched": [
      "застосунку"
    ],
    "fragment": "**Книга** — основна сутність застосунку BookShelf."
  },
  {
    "path": "Decisions/ADR-003 MCP Integration.md",
    "score": 0.16666666666666666,
    "matched": [
      "знань"
    ],
    "fragment": "Для інтеграції Agent Harness із базою знань BookShelf використовується власний MCP-сервер на Python."
  }
]
```

Фактична відповідь MCP:

```json
{
  "results": [
    {
      "path": "Decisions/ADR-002 Separate Knowledge Base.md",
      "fragment": "# ADR-002 Separate Knowledge Base",
      "score": 0.6163147687911987
    },
    {
      "path": "Decisions/ADR-002 Separate Knowledge Base.md",
      "fragment": "## Контекст\nБаза знань повинна бути відокремлена від коду застосунку.",
      "score": 0.6097824573516846
    },
    {
      "path": "Decisions/ADR-003 MCP Integration.md",
      "fragment": "## Пов'язані нотатки\n[[Agent Harness]]\n[[ADR-002 Separate Knowledge Base]]",
      "score": 0.6012576818466187
    },
    {
      "path": "Decisions/ADR-002 Separate Knowledge Base.md",
      "fragment": "## Наслідки\nОкреме версіонування знань і контрольований доступ через [[Agent Harness]].",
      "score": 0.533084511756897
    },
    {
      "path": "BookShelf MOC.md",
      "fragment": "## Архітектурні рішення\n- [[ADR-001 Technology Stack]]\n- [[ADR-002 Separate Knowledge Base]]",
      "score": 0.517236590385437
    }
  ]
}
```

### 7. Як агент підключається до бази знань через MCP?

Keyword, слова запиту: `агент`, `підключається`, `бази`, `знань`, `mcp`.

```json
[
  {
    "path": "Components/Agent Harness.md",
    "score": 0.4,
    "matched": [
      "знань",
      "mcp"
    ],
    "fragment": "Плановані шари: джерела даних, база знань, MCP-конектор, guardrails, skills, orchestration, evaluation.\nБаза знань зберігається окремо: [[ADR-002 Separate Knowledge Base]]."
  },
  {
    "path": "Decisions/ADR-002 Separate Knowledge Base.md",
    "score": 0.4,
    "matched": [
      "знань",
      "mcp"
    ],
    "fragment": "База знань повинна бути відокремлена від коду застосунку.\nЗберігати Obsidian vault у власному Git-репозиторії `BookShelf-KB`. Для доступу агента в наступній практичній роботі передбачити MCP-конектор.\nОкреме версіонування знань і контрольований доступ через [[Agent Harness]]."
  },
  {
    "path": "Decisions/ADR-003 MCP Integration.md",
    "score": 0.4,
    "matched": [
      "знань",
      "mcp"
    ],
    "fragment": "# ADR-003 MCP Integration\nДля інтеграції Agent Harness із базою знань BookShelf використовується власний MCP-сервер на Python."
  },
  {
    "path": "Decisions/BookShelf GitHub Development History.md",
    "score": 0.2,
    "matched": [
      "mcp"
    ],
    "fragment": "Історія розробки BookShelf, отримана через GitHub MCP.\nДжерело: GitHub MCP, репозиторій TarasZhuk-333/BookShelf.\n[[ADR-003 MCP Integration]]"
  },
  {
    "path": "Glossary/BookShelf Glossary.md",
    "score": 0.2,
    "matched": [
      "mcp"
    ],
    "fragment": "- **MCP** — Model Context Protocol, протокол інтеграції інструментів з агентом."
  }
]
```

Фактична відповідь MCP:

```json
{
  "results": [
    {
      "path": "Decisions/ADR-003 MCP Integration.md",
      "fragment": "# ADR-003 MCP Integration\n\nДля інтеграції Agent Harness із базою знань BookShelf використовується власний MCP-сервер на Python.",
      "score": 0.6796079874038696
    },
    {
      "path": "Components/Agent Harness.md",
      "fragment": "# Agent Harness\n\nІнфраструктура для контрольованої роботи Codex CLI над BookShelf.\n\nПлановані шари: джерела даних, база знань, MCP-конектор, guardrails, skills, orchestration, evaluation.\n\nБаза знань зберігається окремо: [[ADR-002 Separate Knowledge Base]].\n\n**Статус:** заплановано; реалізація відбуватиметься в наступних практичних роботах.",
      "score": 0.6010064482688904
    },
    {
      "path": "Decisions/ADR-002 Separate Knowledge Base.md",
      "fragment": "## Рішення\nЗберігати Obsidian vault у власному Git-репозиторії `BookShelf-KB`. Для доступу агента в наступній практичній роботі передбачити MCP-конектор.",
      "score": 0.4987090528011322
    },
    {
      "path": "Decisions/ADR-003 MCP Integration.md",
      "fragment": "## Пов'язані нотатки\n[[Agent Harness]]\n[[ADR-002 Separate Knowledge Base]]",
      "score": 0.48722773790359497
    },
    {
      "path": "Decisions/BookShelf GitHub Development History.md",
      "fragment": "## Пов'язані нотатки\n[[Agent Harness]]\n[[ADR-003 MCP Integration]]",
      "score": 0.4802882969379425
    }
  ]
}
```

### 8. Які шари заплановані для Agent Harness?

Keyword, слова запиту: `шари`, `заплановані`, `agent`, `harness`.

```json
[
  {
    "path": "Components/Agent Harness.md",
    "score": 0.75,
    "matched": [
      "шари",
      "agent",
      "harness"
    ],
    "fragment": "# Agent Harness\nПлановані шари: джерела даних, база знань, MCP-конектор, guardrails, skills, orchestration, evaluation."
  },
  {
    "path": "BookShelf MOC.md",
    "score": 0.5,
    "matched": [
      "agent",
      "harness"
    ],
    "fragment": "- [[Agent Harness]]"
  },
  {
    "path": "Decisions/ADR-002 Separate Knowledge Base.md",
    "score": 0.5,
    "matched": [
      "agent",
      "harness"
    ],
    "fragment": "Окреме версіонування знань і контрольований доступ через [[Agent Harness]]."
  },
  {
    "path": "Decisions/ADR-003 MCP Integration.md",
    "score": 0.5,
    "matched": [
      "agent",
      "harness"
    ],
    "fragment": "Для інтеграції Agent Harness із базою знань BookShelf використовується власний MCP-сервер на Python.\n[[Agent Harness]]"
  },
  {
    "path": "Decisions/BookShelf GitHub Development History.md",
    "score": 0.5,
    "matched": [
      "agent",
      "harness"
    ],
    "fragment": "1. df6fb10 — Add application and harness requirements — 2026-11-08 15:29:59 UTC.\n[[Agent Harness]]"
  }
]
```

Фактична відповідь MCP:

```json
{
  "results": [
    {
      "path": "Components/Agent Harness.md",
      "fragment": "# Agent Harness\n\nІнфраструктура для контрольованої роботи Codex CLI над BookShelf.\n\nПлановані шари: джерела даних, база знань, MCP-конектор, guardrails, skills, orchestration, evaluation.\n\nБаза знань зберігається окремо: [[ADR-002 Separate Knowledge Base]].\n\n**Статус:** заплановано; реалізація відбуватиметься в наступних практичних роботах.",
      "score": 0.6550896167755127
    },
    {
      "path": "Decisions/ADR-003 MCP Integration.md",
      "fragment": "## Пов'язані нотатки\n[[Agent Harness]]\n[[ADR-002 Separate Knowledge Base]]",
      "score": 0.45551103353500366
    },
    {
      "path": "Decisions/BookShelf GitHub Development History.md",
      "fragment": "## Пов'язані нотатки\n[[Agent Harness]]\n[[ADR-003 MCP Integration]]",
      "score": 0.4429517388343811
    },
    {
      "path": "Glossary/BookShelf Glossary.md",
      "fragment": "# BookShelf Glossary\n\n- **Book** — запис про книгу; див. [[Book]].\n- **Reading Status** — стан читання; див. [[Reading Status]].\n- **CRUD** — створення, читання, оновлення, видалення.\n- **Vault** — папка нотаток Obsidian.\n- **MCP** — Model Context Protocol, протокол інтеграції інструментів з агентом.\n- **Agent Harness** — інфраструктура контрольованої роботи агента; див. [[Agent Harness]].",
      "score": 0.42661094665527344
    },
    {
      "path": "Decisions/ADR-003 MCP Integration.md",
      "fragment": "# ADR-003 MCP Integration\n\nДля інтеграції Agent Harness із базою знань BookShelf використовується власний MCP-сервер на Python.",
      "score": 0.4145330786705017
    }
  ]
}
```

### 9. Що означає CRUD?

Keyword, слова запиту: `означає`, `crud`.

```json
[
  {
    "path": "Glossary/BookShelf Glossary.md",
    "score": 0.5,
    "matched": [
      "crud"
    ],
    "fragment": "- **CRUD** — створення, читання, оновлення, видалення."
  }
]
```

Фактична відповідь MCP:

```json
{
  "results": [
    {
      "path": "Templates/Note Template.md",
      "fragment": "# Назва нотатки",
      "score": 0.43723946809768677
    },
    {
      "path": "Templates/Note Template.md",
      "fragment": "## Призначення\nКороткий опис.",
      "score": 0.2980991005897522
    },
    {
      "path": "Concepts/Reading Status.md",
      "fragment": "# Reading Status\n\nСтатус читання книги має одне з трьох значень:\n- `To Read` — планується прочитати;\n- `Reading` — читається;\n- `Read` — прочитано.\n\nСтатус належить сутності [[Book]] і змінюється через [[Streamlit UI]].",
      "score": 0.2585691213607788
    },
    {
      "path": "Templates/Note Template.md",
      "fragment": "## Деталі\nОсновна інформація.",
      "score": 0.24042019248008728
    },
    {
      "path": "Glossary/BookShelf Glossary.md",
      "fragment": "# BookShelf Glossary\n\n- **Book** — запис про книгу; див. [[Book]].\n- **Reading Status** — стан читання; див. [[Reading Status]].\n- **CRUD** — створення, читання, оновлення, видалення.\n- **Vault** — папка нотаток Obsidian.\n- **MCP** — Model Context Protocol, протокол інтеграції інструментів з агентом.\n- **Agent Harness** — інфраструктура контрольованої роботи агента; див. [[Agent Harness]].",
      "score": 0.23160696029663086
    }
  ]
}
```

### 10. Які коміти зафіксовані в історії розробки BookShelf?

Keyword, слова запиту: `коміти`, `зафіксовані`, `історії`, `розробки`, `bookshelf`.

```json
[
  {
    "path": "Decisions/BookShelf GitHub Development History.md",
    "score": 0.4,
    "matched": [
      "розробки",
      "bookshelf"
    ],
    "fragment": "# BookShelf GitHub Development History\nІсторія розробки BookShelf, отримана через GitHub MCP.\n2. 4de6fb9 — Merge GitHub initial commit with BookShelf requirements — 2026-11-08 12:31:47 UTC.\n3. dc1b95f — Add initial BookShelf requirements — 2026-11-08 12:26:27 UTC.\nДжерело: GitHub MCP, репозиторій TarasZhuk-333/BookShelf."
  },
  {
    "path": "BookShelf MOC.md",
    "score": 0.2,
    "matched": [
      "bookshelf"
    ],
    "fragment": "# BookShelf — Map of Content\n- [[BookShelf Glossary]]"
  },
  {
    "path": "Components/Agent Harness.md",
    "score": 0.2,
    "matched": [
      "bookshelf"
    ],
    "fragment": "Інфраструктура для контрольованої роботи Codex CLI над BookShelf."
  },
  {
    "path": "Concepts/Book.md",
    "score": 0.2,
    "matched": [
      "bookshelf"
    ],
    "fragment": "**Книга** — основна сутність застосунку BookShelf."
  },
  {
    "path": "Decisions/ADR-002 Separate Knowledge Base.md",
    "score": 0.2,
    "matched": [
      "bookshelf"
    ],
    "fragment": "Зберігати Obsidian vault у власному Git-репозиторії `BookShelf-KB`. Для доступу агента в наступній практичній роботі передбачити MCP-конектор."
  }
]
```

Фактична відповідь MCP:

```json
{
  "results": [
    {
      "path": "README.md",
      "fragment": "# BookShelf Knowledge Base",
      "score": 0.5770299434661865
    },
    {
      "path": "BookShelf MOC.md",
      "fragment": "# BookShelf — Map of Content",
      "score": 0.5563666820526123
    },
    {
      "path": "Concepts/Book.md",
      "fragment": "# Book\n\n**Книга** — основна сутність застосунку BookShelf.\n\nПоля: `id`, `title`, `author`, `status`, `created_at`.\n\nНазва й автор обов'язкові. Ідентифікатор унікальний.\n\nПов'язані нотатки: [[Reading Status]], [[SQLite Storage]], [[Streamlit UI]].",
      "score": 0.5219515562057495
    },
    {
      "path": "Glossary/BookShelf Glossary.md",
      "fragment": "# BookShelf Glossary\n\n- **Book** — запис про книгу; див. [[Book]].\n- **Reading Status** — стан читання; див. [[Reading Status]].\n- **CRUD** — створення, читання, оновлення, видалення.\n- **Vault** — папка нотаток Obsidian.\n- **MCP** — Model Context Protocol, протокол інтеграції інструментів з агентом.\n- **Agent Harness** — інфраструктура контрольованої роботи агента; див. [[Agent Harness]].",
      "score": 0.488838255405426
    },
    {
      "path": "Components/Agent Harness.md",
      "fragment": "# Agent Harness\n\nІнфраструктура для контрольованої роботи Codex CLI над BookShelf.\n\nПлановані шари: джерела даних, база знань, MCP-конектор, guardrails, skills, orchestration, evaluation.\n\nБаза знань зберігається окремо: [[ADR-002 Separate Knowledge Base]].\n\n**Статус:** заплановано; реалізація відбуватиметься в наступних практичних роботах.",
      "score": 0.4477894902229309
    }
  ]
}
```

## Межі та перевірка

Після створення звіту повторно обчислено SHA-256 і перелік усіх 13 відкритих Markdown-файлів Vault: вони збігаються зі знімком, отриманим під час оцінювання. `git diff --check` завершився з кодом 0; у статусі BookShelf додався лише `docs/rag-evaluation.md` порівняно з початковим статусом.

Створено лише цей звіт. Наявні до початку роботи зміни застосунку, retrieval-модуля та інші untracked-файли не редагувалися. Vault використовувався лише для читання; ingest_note/sync_note, commit/push не викликалися. Git status Vault недоступний через `detected dubious ownership`; конфігурацію Git не змінено. Спроба локального Python завершилася до запуску коду: `.venv` посилається на відсутній Python313; для keyword використано прочитані PowerShell тексти й JavaScript. Це не вплинуло на 10 успішних MCP-викликів.
