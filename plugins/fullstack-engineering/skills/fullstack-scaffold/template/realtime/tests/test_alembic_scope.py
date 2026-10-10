from types import SimpleNamespace

import pytest

pytest.importorskip("alembic")


def test_foreign_tables_are_ignored(monkeypatch):
    # env.py runs migrations on import; load only its filter function.
    import ast
    from pathlib import Path

    source = Path(__file__).parents[1].joinpath("alembic", "env.py").read_text()
    tree = ast.parse(source)
    func = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "include_object"
    )
    namespace: dict = {}
    exec(compile(ast.Module(body=[func], type_ignores=[]), "env.py", "exec"), namespace)  # noqa: S102
    include_object = namespace["include_object"]

    django_table = SimpleNamespace(name="users_user")
    assert include_object(django_table, "users_user", "table", True, None) is False
    assert (
        include_object(django_table, "realtime_run", "table", False, object()) is True
    )
