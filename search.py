"""Пошук книг за буквальним фрагментом назви або автора."""

from collections.abc import Iterable, Mapping
from typing import cast


def search_books(
    books: Iterable[Mapping[str, object]], query: str
) -> list[Mapping[str, object]]:
    """Повернути записи в початковому порядку, не змінюючи їх.

    title та author мають бути рядками. Порожній після strip запит
    повертає весь каталог. Порівняння використовує Unicode casefold.
    """
    fragment = query.strip().casefold()
    if not fragment:
        return list(books)
    return [
        book
        for book in books
        if fragment in cast(str, book["title"]).casefold()
        or fragment in cast(str, book["author"]).casefold()
    ]
