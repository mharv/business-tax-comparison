"""
Australian tax rates and thresholds for 2024-25 financial year.

Sources:
- ATO Individual Tax Rates: https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents
- ATO Company Tax Rates: https://www.ato.gov.au/tax-rates-and-codes/company-tax-rate-changes
- Superannuation Guarantee: https://www.ato.gov.au/tax-rates-and-codes/super-guarantee-percentage
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import NamedTuple


class TaxBracket(NamedTuple):
    """A single tax bracket with threshold, base tax, and marginal rate."""
    
    threshold: Decimal  # Income threshold where this bracket starts
    base_tax: Decimal   # Cumulative tax from lower brackets
    rate: Decimal       # Marginal rate for income above threshold (as decimal, e.g., 0.30 for 30%)


@dataclass(frozen=True)
class TaxRates:
    """Tax rates and thresholds for a specific financial year."""
    
    # Financial year identifier (e.g., "2024-25")
    year: str
    
    # Individual tax brackets (Australian residents)
    # Each bracket: (threshold, base_tax, marginal_rate)
    individual_brackets: tuple[TaxBracket, ...]
    
    # Medicare levy rate (as decimal, e.g., 0.02 for 2%)
    medicare_levy_rate: Decimal
    
    # Small Business Income Tax Offset (SBITO)
    sbito_rate: Decimal      # Percentage of tax attributable to business income
    sbito_max: Decimal       # Maximum offset amount
    sbito_turnover_limit: Decimal  # Aggregated turnover limit for eligibility
    
    # Company tax rates
    company_base_rate: Decimal      # Base rate entity (turnover < $50M, <80% passive income)
    company_full_rate: Decimal      # Full rate for other companies
    company_turnover_threshold: Decimal  # Aggregated turnover threshold for base rate
    
    # Superannuation guarantee
    super_guarantee_rate: Decimal   # Rate on ordinary time earnings
    super_max_contribution_base_quarterly: Decimal  # Maximum quarterly contribution base


# 2024-25 Financial Year Tax Rates
RATES_2024_25 = TaxRates(
    year="2024-25",
    
    # Individual tax brackets (Australian residents)
    # Source: https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents
    individual_brackets=(
        # $0 - $18,200: Nil
        TaxBracket(
            threshold=Decimal("0"),
            base_tax=Decimal("0"),
            rate=Decimal("0"),
        ),
        # $18,201 - $45,000: 16% of amount over $18,200
        TaxBracket(
            threshold=Decimal("18200"),
            base_tax=Decimal("0"),
            rate=Decimal("0.16"),
        ),
        # $45,001 - $135,000: $4,288 + 30% of amount over $45,000
        TaxBracket(
            threshold=Decimal("45000"),
            base_tax=Decimal("4288"),
            rate=Decimal("0.30"),
        ),
        # $135,001 - $190,000: $31,288 + 37% of amount over $135,000
        TaxBracket(
            threshold=Decimal("135000"),
            base_tax=Decimal("31288"),
            rate=Decimal("0.37"),
        ),
        # $190,001+: $51,638 + 45% of amount over $190,000
        TaxBracket(
            threshold=Decimal("190000"),
            base_tax=Decimal("51638"),
            rate=Decimal("0.45"),
        ),
    ),
    
    # Medicare levy: 2%
    medicare_levy_rate=Decimal("0.02"),
    
    # Small Business Income Tax Offset
    # Source: https://www.ato.gov.au/individuals-and-families/income-deductions-offsets-and-records/tax-offsets/small-business-income-tax-offset
    sbito_rate=Decimal("0.16"),  # 16% of tax on business income
    sbito_max=Decimal("1000"),   # Capped at $1,000
    sbito_turnover_limit=Decimal("5000000"),  # $5 million aggregated turnover
    
    # Company tax rates
    # Source: https://www.ato.gov.au/tax-rates-and-codes/company-tax-rate-changes
    company_base_rate=Decimal("0.25"),      # 25% for base rate entities
    company_full_rate=Decimal("0.30"),      # 30% for other companies
    company_turnover_threshold=Decimal("50000000"),  # $50 million threshold
    
    # Superannuation guarantee (2024-25)
    # Source: https://www.ato.gov.au/tax-rates-and-codes/super-guarantee-percentage
    super_guarantee_rate=Decimal("0.115"),  # 11.5%
    super_max_contribution_base_quarterly=Decimal("62500"),  # $62,500 per quarter
)


# Default compliance cost estimates (annual, ongoing)
# Source: https://business.gov.au/planning/business-structures-and-types/business-structures/difference-between-a-sole-trader-and-a-company
#
# SOLE TRADER ongoing costs:
#   - ABN registration: Free
#   - Business name (if not your own): $42/year
#   - Accountant for tax return: $200-500
#   - Bookkeeping software: $0-300/year
#   - Total: ~$300-800/year
#
# COMPANY ongoing costs:
#   - ASIC annual review fee: $335 (special purpose) or $319 (small proprietary)
#   - Company tax return (accountant): $1,000-2,500
#   - BAS/IAS lodgements: $500-1,000/year
#   - Payroll processing: $500-1,500/year
#   - Bookkeeping: $1,000-3,000/year
#   - Total: ~$3,000-8,000/year
#
# COMPANY setup costs (one-time):
#   - ASIC company registration: $576
#   - Legal/accountant setup: $500-2,000
#   - Total: ~$1,000-2,500

DEFAULT_COMPLIANCE_COST_SOLE_TRADER = Decimal("500")   # Conservative estimate for simple operation
DEFAULT_COMPLIANCE_COST_COMPANY = Decimal("3500")      # ASIC $335 + accountant $2000 + bookkeeping $1000 + payroll $165

# One-time setup costs
DEFAULT_SETUP_COST_SOLE_TRADER = Decimal("100")   # ABN + business name registration
DEFAULT_SETUP_COST_COMPANY = Decimal("1500")      # ASIC $576 + accountant/legal setup ~$900


# Registry of available tax years
TAX_RATES_REGISTRY: dict[str, TaxRates] = {
    "2024-25": RATES_2024_25,
}


def get_rates(year: str = "2024-25") -> TaxRates:
    """
    Get tax rates for a specific financial year.
    
    Args:
        year: Financial year identifier (e.g., "2024-25")
        
    Returns:
        TaxRates for the specified year
        
    Raises:
        ValueError: If the year is not available
    """
    if year not in TAX_RATES_REGISTRY:
        available = ", ".join(sorted(TAX_RATES_REGISTRY.keys()))
        raise ValueError(f"Tax rates for {year} not available. Available years: {available}")
    return TAX_RATES_REGISTRY[year]
