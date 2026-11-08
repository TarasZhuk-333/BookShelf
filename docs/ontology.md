# Онтологія BookShelf-KB

Цей документ визначає типи нотаток і типізовані зв'язки в Obsidian Vault **BookShelf-KB** — окремій базі знань проєкту BookShelf. Структура відповідає категоріям чинного MCP-сервера. Доступ агента до Vault здійснюється через MCP.

## 1. Типи сутностей і папки

| Значення `type` | Папка у Vault | Призначення |
| --- | --- | --- |
| `concept` | `Concepts/` | Поняття предметної області, правила та абстракції, наприклад Book або Reading Status. |
| `component` | `Components/` | Частина застосунку або інфраструктури, її відповідальність та залежності. |
| `decision` | `Decisions/` | Архітектурне рішення (ADR): контекст, обраний підхід і наслідки. |
| `glossary` | `Glossary/` | Визначення терміна чи скорочення для узгодженого словника проєкту. |

Одна нотатка описує одну сутність і має рівно один `type`, узгоджений із папкою. Назва файла є назвою сутності: `Components/Streamlit UI.md`. Наявний **Agent Harness** належить до `Components/` і має `type: component`.

## 2. Типізовані зв'язки

Зв'язок спрямований від поточної нотатки до вказаної цілі.

| Ключ | Значення `A → B` | Приклад |
| --- | --- | --- |
| `depends_on` | A потребує B для виконання своєї відповідальності. | Streamlit UI → SQLite Storage |
| `implements` | A реалізує поняття, правило або рішення B. | SQLite Storage → ADR-001 Technology Stack |
| `documents` | A описує або обґрунтовує B. | ADR-001 Technology Stack → Streamlit UI |
| `supersedes` | Нове рішення A замінює попереднє рішення B. | Майбутній ADR про зміну стеку → ADR-001 Technology Stack |

`supersedes` використовується між нотатками `decision`. Це не зв'язок «пов'язано з»: він означає явну заміну рішення. Зворотні зв'язки не додаються автоматично; `documents` та `implements` мають різний зміст.

## 3. Конвенція YAML frontmatter

Frontmatter розміщується на початку Markdown-файла між рядками `---`.

- Обов'язкові поля: `type` та `project: BookShelf`.
- Наявні `tags` і `status` зберігаються. Статус рішення, наприклад `accepted`, не означає, що компонент уже реалізовано.
- Кожен тип зв'язку записується окремим ключем верхнього рівня зі списком цілей, навіть якщо ціль одна.
- Ціль — Obsidian wikilink у подвійних лапках, із папкою від кореня Vault, без `.md`: `"[[Components/SQLite Storage]]"`.
- Регістр папки й назва нотатки мають точно відповідати наявному файлу. Лапки потрібні, щоб YAML трактував wikilink як рядок.
- Ключ без зв'язків можна пропустити або записати як порожній список `[]`. Дублікати та посилання на саму нотатку не додаються.
- Звичайні wikilinks у тексті залишаються допустимими навігаційними посиланнями, але самі по собі не визначають тип зв'язку.

```yaml
---
type: component
project: BookShelf
tags: [ui, python]
depends_on:
  - "[[Components/SQLite Storage]]"
implements:
  - "[[Decisions/ADR-001 Technology Stack]]"
---
```

У перевірених нотатках Vault уже є поля `type`, `project`, `tags` та звичайні wikilinks у тексті. Типізовані поля вище — конвенція для подальшого використання, а не твердження про виконану міграцію. Чинний `ingest_note` формує власний frontmatter і додає нетипізовані посилання в текст; запис і збереження цих типізованих полів через нього потребуватимуть окремого доопрацювання.

## 4. Приклади для наявних нотаток BookShelf

Нижче наведено пропоновані фрагменти frontmatter для наявних нотаток. Цей документ не змінює Vault і не підтверджує реалізацію описаних компонентів.

### Components/Streamlit UI.md

Інтерфейс залежить від сховища та реалізує вибір Streamlit у рішенні про стек.

```yaml
---
type: component
project: BookShelf
tags: [ui, python]
depends_on:
  - "[[Components/SQLite Storage]]"
implements:
  - "[[Decisions/ADR-001 Technology Stack]]"
---
```

### Components/SQLite Storage.md

Сховище реалізує вибір SQLite у рішенні про стек.

```yaml
---
type: component
project: BookShelf
tags: [database, sqlite]
implements:
  - "[[Decisions/ADR-001 Technology Stack]]"
---
```

### Components/Agent Harness.md

Наявна нотатка описує заплановану інфраструктуру та посилається на ADR-002 Separate Knowledge Base. Зв'язок `implements` нижче описує цільове втілення цього рішення; поточний статус «заплановано» у тексті нотатки слід зберігати.

```yaml
---
type: component
project: BookShelf
tags: [agent, harness]
implements:
  - "[[Decisions/ADR-002 Separate Knowledge Base]]"
---
```

### Decisions/ADR-001 Technology Stack.md

Рішення обґрунтовує Python, Streamlit, SQLite та pytest і документує технологічний вибір для інтерфейсу та сховища.

```yaml
---
type: decision
status: accepted
project: BookShelf
tags: [architecture, adr]
documents:
  - "[[Components/Streamlit UI]]"
  - "[[Components/SQLite Storage]]"
supersedes: []
---
```

Для `supersedes` поки не задається ціль: перевірена нотатка ADR-001 не вказує попереднього рішення. Якщо майбутнє рішення замінить ADR-001, саме в новій нотатці слід записати:

```yaml
supersedes:
  - "[[Decisions/ADR-001 Technology Stack]]"
```

## 5. Узгодженість

Перед додаванням зв'язку слід перевірити існування цільової нотатки через MCP, відповідність її типу папці та зміст зв'язку. Опис архітектури у Vault не є доказом наявності відповідного коду чи успішного виконання тестів.
