"""Testes de qualidade e limpeza das bases."""

from src.cleaning import EXPENSE_REQUIRED_COLUMNS, SALES_REQUIRED_COLUMNS, validate_expenses, validate_sales


def test_required_fields_and_no_missing_values(clean_datasets):
    sales, expenses, _, _ = clean_datasets
    assert SALES_REQUIRED_COLUMNS.issubset(sales.columns)
    assert EXPENSE_REQUIRED_COLUMNS.issubset(expenses.columns)
    assert not sales[list(SALES_REQUIRED_COLUMNS)].isna().any().any()
    assert not expenses[list(EXPENSE_REQUIRED_COLUMNS)].isna().any().any()


def test_duplicates_are_removed(clean_datasets):
    sales, expenses, sales_audit, expenses_audit = clean_datasets
    assert not sales.duplicated().any()
    assert not expenses.duplicated().any()
    assert sales_audit["duplicatas_removidas"] > 0
    assert expenses_audit["duplicatas_removidas"] > 0


def test_dates_types_and_business_ranges(clean_datasets):
    sales, expenses, _, _ = clean_datasets
    assert str(sales["data"].dtype).startswith("datetime64")
    assert str(expenses["data"].dtype).startswith("datetime64")
    assert sales["quantidade"].gt(0).all()
    assert sales["desconto"].between(0, 0.70).all()
    assert expenses["valor"].gt(0).all()
    assert validate_sales(sales) == []
    assert validate_expenses(expenses) == []
