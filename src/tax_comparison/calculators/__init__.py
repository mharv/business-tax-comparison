"""Calculator modules for tax comparison."""

from tax_comparison.calculators.individual import (
    calculate_income_tax,
    calculate_medicare_levy,
    calculate_individual_tax,
)
from tax_comparison.calculators.sole_trader import calculate_sole_trader_tax
from tax_comparison.calculators.company import (
    calculate_company_salary,
    calculate_company_dividends,
    calculate_company_mixed,
)

__all__ = [
    "calculate_income_tax",
    "calculate_medicare_levy",
    "calculate_individual_tax",
    "calculate_sole_trader_tax",
    "calculate_company_salary",
    "calculate_company_dividends",
    "calculate_company_mixed",
]
