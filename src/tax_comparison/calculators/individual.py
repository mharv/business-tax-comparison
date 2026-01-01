"""
Individual income tax calculator.

Calculates income tax using progressive brackets, Medicare levy,
and applicable offsets.
"""

from decimal import Decimal

from tax_comparison.models import IndividualTaxBreakdown
from tax_comparison.rates import TaxRates, get_rates


def calculate_income_tax(taxable_income: Decimal, rates: TaxRates) -> Decimal:
    """
    Calculate income tax using progressive tax brackets.
    
    Args:
        taxable_income: Total taxable income
        rates: Tax rates for the relevant year
        
    Returns:
        Income tax payable (before Medicare levy and offsets)
    """
    if taxable_income <= 0:
        return Decimal("0")
    
    # Find the applicable bracket
    applicable_bracket = rates.individual_brackets[0]
    for bracket in rates.individual_brackets:
        if taxable_income > bracket.threshold:
            applicable_bracket = bracket
        else:
            break
    
    # Calculate tax: base_tax + (income - threshold) * rate
    income_above_threshold = taxable_income - applicable_bracket.threshold
    tax = applicable_bracket.base_tax + (income_above_threshold * applicable_bracket.rate)
    
    return tax.quantize(Decimal("0.01"))


def calculate_medicare_levy(
    taxable_income: Decimal,
    rates: TaxRates,
) -> Decimal:
    """
    Calculate Medicare levy.
    
    Note: This simplified calculation does not account for:
    - Low-income thresholds and phase-in
    - Medicare levy surcharge
    - Exemptions
    
    Args:
        taxable_income: Total taxable income
        rates: Tax rates for the relevant year
        
    Returns:
        Medicare levy payable
    """
    if taxable_income <= 0:
        return Decimal("0")
    
    levy = taxable_income * rates.medicare_levy_rate
    return levy.quantize(Decimal("0.01"))


def calculate_sbito(
    income_tax: Decimal,
    business_income: Decimal,
    total_income: Decimal,
    rates: TaxRates,
) -> Decimal:
    """
    Calculate Small Business Income Tax Offset (SBITO).
    
    The offset is calculated as a percentage of the income tax
    attributable to small business income, capped at a maximum amount.
    
    Args:
        income_tax: Total income tax before offsets
        business_income: Income from small business
        total_income: Total taxable income (business + other)
        rates: Tax rates for the relevant year
        
    Returns:
        SBITO amount
    """
    if total_income <= 0 or business_income <= 0 or income_tax <= 0:
        return Decimal("0")
    
    # Proportion of income from business
    business_proportion = min(Decimal("1"), business_income / total_income)
    
    # Tax attributable to business income
    tax_on_business = income_tax * business_proportion
    
    # Offset is percentage of tax on business income
    offset = tax_on_business * rates.sbito_rate
    
    # Cap at maximum
    offset = min(offset, rates.sbito_max)
    
    return offset.quantize(Decimal("0.01"))


def calculate_individual_tax(
    taxable_income: Decimal,
    business_income: Decimal = Decimal("0"),
    rates: TaxRates | None = None,
    tax_year: str = "2024-25",
) -> IndividualTaxBreakdown:
    """
    Calculate complete individual tax breakdown.
    
    Args:
        taxable_income: Total taxable income
        business_income: Portion of income from small business (for SBITO)
        rates: Tax rates (if None, uses tax_year to get rates)
        tax_year: Financial year for rates (if rates not provided)
        
    Returns:
        IndividualTaxBreakdown with full calculation details
    """
    if rates is None:
        rates = get_rates(tax_year)
    
    # Calculate components
    income_tax = calculate_income_tax(taxable_income, rates)
    medicare_levy = calculate_medicare_levy(taxable_income, rates)
    
    # Calculate SBITO if business income present
    sbito = Decimal("0")
    if business_income > 0:
        sbito = calculate_sbito(income_tax, business_income, taxable_income, rates)
    
    return IndividualTaxBreakdown(
        taxable_income=taxable_income,
        income_tax=income_tax,
        medicare_levy=medicare_levy,
        sbito=sbito,
    )
