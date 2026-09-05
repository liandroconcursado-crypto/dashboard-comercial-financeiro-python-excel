"""Fixtures compartilhadas pelos testes."""

import pytest

from src.cleaning import clean_expenses, clean_sales
from src.generate_data import generate_expense_data, generate_sales_data


@pytest.fixture(scope="session")
def clean_datasets():
    sales_raw = generate_sales_data(seed=123, target_rows=420)
    expenses_raw = generate_expense_data(seed=321, target_rows=120)
    sales, sales_audit = clean_sales(sales_raw)
    expenses, expenses_audit = clean_expenses(expenses_raw)
    return sales, expenses, sales_audit, expenses_audit
