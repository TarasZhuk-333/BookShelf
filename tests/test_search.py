"""Перевірки погодженого контракту пошуку на даних у пам'яті."""

from copy import deepcopy

import pytest

from search import search_books


@pytest.mark.parametrize(
    "query",
    ["ЛІСОВА", "лісова", "ЛіСоВа", "піс", "ЛЕСЯ", "леся", "ЛеСя", "україн"],
)
def test_ukrainian_title_or_author_fragment(query):
    book = {"title": "Лісова пісня", "author": "Леся Українка"}
    assert search_books([book], query) == [book]


@pytest.mark.parametrize("field", ["title", "author"])
@pytest.mark.parametrize(
    "text, query",
    [("І", "і"), ("ї", "Ї"), ("Є", "є"), ("ґ", "Ґ"),
     ("Python Guide", "tHoN"), ("Straße", "STRASSE")],
)
def test_unicode_casefold_in_each_field(field, text, query):
    book = {"title": "---", "author": "---", field: text}
    assert search_books([book], query) == [book]


@pytest.mark.parametrize("query", ["", " ", "\t\n"])
def test_blank_query_returns_all_records(query):
    books = [{"title": "Друга", "author": "Б"}, {"title": "Перша", "author": "А"}]
    result = search_books(iter(books), query)
    assert result == books
    assert result is not books
    assert all(actual is original for actual, original in zip(result, books))


def test_or_order_identity_and_input_preservation():
    books = [
        {"title": "Збіг", "author": "ЗБІГ", "description": "Текст"},
        {"title": "Інше", "author": "Автор"},
        {"title": "Остання", "author": "збіг"},
    ]
    before = deepcopy(books)
    result = search_books(iter(books), "  ЗбІг\t")
    assert result == [books[0], books[2]]
    assert result[0] is books[0]
    assert result[1] is books[2]
    assert books == before


@pytest.mark.parametrize("query", ["відсутній", "секрет"])
def test_no_match_and_description_is_not_searched(query):
    books = [{"title": "Книга", "author": "Автор", "description": "секрет"}]
    assert search_books(books, query) == []


@pytest.mark.parametrize("query", ["", " ", "книга"])
def test_empty_catalog(query):
    assert search_books([], query) == []


@pytest.mark.parametrize("field", ["title", "author"])
@pytest.mark.parametrize("query", ["%", "_", "'", '"', "' OR 1=1 --", ".*"])
def test_special_characters_are_literal(field, query):
    match = {"title": "Назва", "author": "Автор", field: f"До {query} після"}
    other = {"title": "Звичайна книга", "author": "Інший автор"}
    assert search_books([other, match], query) == [match]
