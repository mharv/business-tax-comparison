"""
Sole trader tax calculator.

Calculates tax for sole trader business structure where
business profit is added to personal income.
"""

from decimal import Decimal

from tax_comparison.calculators.individual import calculate_individual_tax
from tax_comparison.models import Config, SoleTraderResult
from tax_comparison.rates import get_rates


def calculate_sole_trader_tax(
    config: Config,
) -> SoleTraderResult:
    """
    Calculate tax for sole trader scenario.
    
    As a sole trader:
    - Employment salary and business profit combine as total income
    - Tax is calculated on total income using individual rates
    - SBITO offset applies to the business income portion
    
    Args:
        config: Configuration with business_profit and employment_salary
        
    Returns:
        SoleTraderResult with complete tax breakdown
    """
    rates = get_rates(config.tax_year)
    
    # Total taxable income
    total_income = config.employment_salary + config.business_profit
    
    # Calculate individual tax with SBITO for business portion
    tax_breakdown = calculate_individual_tax(
        taxable_income=total_income,
        business_income=config.business_profit,
        rates=rates,
    )
    
    # Compliance costs if enabled (annual ongoing + amortized setup)
    compliance_costs = Decimal("0")
    if config.include_compliance_costs:
        compliance_costs = config.compliance_cost_sole_trader
    if config.include_setup_costs:
        amortized_setup = config.setup_cost_sole_trader / Decimal(str(config.years_to_amortize))
        compliance_costs += amortized_setup

    return SoleTraderResult(
        employment_salary=config.employment_salary,
        business_profit=config.business_profit,
        tax_breakdown=tax_breakdown,
        compliance_costs=compliance_costs,
    )
