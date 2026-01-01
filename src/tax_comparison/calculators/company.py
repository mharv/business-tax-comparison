"""
Company tax calculator.

Calculates tax for company (Pty Ltd) structure with different
extraction methods: salary, dividends, or mixed.
"""

from decimal import Decimal

from tax_comparison.calculators.individual import calculate_individual_tax
from tax_comparison.models import (
    CompanyDividendResult,
    CompanyMixedResult,
    CompanySalaryResult,
    CompanyTaxBreakdown,
    Config,
    DividendBreakdown,
    SuperTreatment,
)
from tax_comparison.rates import TaxRates, get_rates


def calculate_company_tax(
    taxable_income: Decimal,
    rates: TaxRates,
    is_base_rate_entity: bool = True,
) -> CompanyTaxBreakdown:
    """
    Calculate company tax on profits.
    
    Args:
        taxable_income: Company's taxable income
        rates: Tax rates for the relevant year
        is_base_rate_entity: Whether company qualifies for 25% rate
        
    Returns:
        CompanyTaxBreakdown with tax details
    """
    if taxable_income <= 0:
        return CompanyTaxBreakdown(
            company_profit=taxable_income,
            company_tax_rate=Decimal("0"),
            company_tax=Decimal("0"),
        )
    
    tax_rate = rates.company_base_rate if is_base_rate_entity else rates.company_full_rate
    tax = (taxable_income * tax_rate).quantize(Decimal("0.01"))
    
    return CompanyTaxBreakdown(
        company_profit=taxable_income,
        company_tax_rate=tax_rate,
        company_tax=tax,
    )


def calculate_super_guarantee(
    salary: Decimal,
    rates: TaxRates,
) -> Decimal:
    """
    Calculate superannuation guarantee on salary.
    
    Args:
        salary: Salary paid (ordinary time earnings)
        rates: Tax rates for the relevant year
        
    Returns:
        Super guarantee amount
    """
    if salary <= 0:
        return Decimal("0")
    
    # Cap at maximum contribution base (quarterly × 4)
    max_base = rates.super_max_contribution_base_quarterly * 4
    capped_salary = min(salary, max_base)
    
    super_amount = (capped_salary * rates.super_guarantee_rate).quantize(Decimal("0.01"))
    return super_amount


def calculate_company_salary(config: Config) -> CompanySalaryResult:
    """
    Calculate tax for company paying salary only.
    
    When paying yourself a salary:
    - Salary is tax-deductible expense for company
    - Company pays super guarantee on salary (11.5%)
    - You pay personal income tax on salary via PAYG
    - If salary + super >= profit, company tax = $0
    
    IMPORTANT: If you have employment_salary from another job, the company
    salary is ADDED to your personal income and taxed at marginal rates.
    We calculate the ADDITIONAL tax from the company salary, not tax on
    company salary alone.
    
    Args:
        config: Configuration with business_profit and employment_salary
        
    Returns:
        CompanySalaryResult with complete breakdown
    """
    rates = get_rates(config.tax_year)
    
    company_profit = config.business_profit
    employment_salary = config.employment_salary
    
    # Calculate super guarantee
    # Super is an additional cost on top of salary
    # We need to figure out max salary that can be paid given profit
    # profit = salary + super = salary + (salary × super_rate)
    # profit = salary × (1 + super_rate)
    # salary = profit / (1 + super_rate)
    
    if config.include_super:
        # Calculate salary that can be paid given profit
        super_rate = rates.super_guarantee_rate
        max_salary = (company_profit / (1 + super_rate)).quantize(Decimal("0.01"))
        salary_paid = max_salary
        super_contribution = calculate_super_guarantee(salary_paid, rates)
    else:
        # No super - full profit paid as salary
        salary_paid = company_profit
        super_contribution = Decimal("0")
    
    # Company has no taxable income (salary + super = profit)
    company_tax_breakdown = CompanyTaxBreakdown(
        company_profit=company_profit,
        company_tax_rate=Decimal("0"),
        company_tax=Decimal("0"),
    )
    
    # Personal tax calculation:
    # If you have employment salary, we need to calculate the ADDITIONAL tax
    # from the company salary, not the tax on company salary alone.
    # 
    # Additional tax = Tax on (employment + company salary) - Tax on (employment alone)
    
    total_personal_income = employment_salary + salary_paid
    
    # Tax on combined income
    combined_tax_breakdown = calculate_individual_tax(
        taxable_income=total_personal_income,
        business_income=Decimal("0"),
        rates=rates,
    )
    
    # Tax on employment income alone (what you'd pay without the company)
    if employment_salary > 0:
        employment_only_tax = calculate_individual_tax(
            taxable_income=employment_salary,
            business_income=Decimal("0"),
            rates=rates,
        )
        # Additional tax from company salary
        additional_personal_tax = combined_tax_breakdown.total_tax - employment_only_tax.total_tax
    else:
        additional_personal_tax = combined_tax_breakdown.total_tax
    
    # Store the breakdown for the company portion
    # We use the combined breakdown but track that it includes employment
    personal_tax_breakdown = combined_tax_breakdown
    
    # Compliance costs if enabled (annual ongoing + amortized setup)
    compliance_costs = Decimal("0")
    if config.include_compliance_costs:
        compliance_costs = config.compliance_cost_company
    if config.include_setup_costs:
        amortized_setup = config.setup_cost_company / Decimal(str(config.years_to_amortize))
        compliance_costs += amortized_setup
    
    result = CompanySalaryResult(
        company_profit=company_profit,
        salary_paid=salary_paid,
        employment_salary=employment_salary,
        super_contribution=super_contribution,
        company_tax_breakdown=company_tax_breakdown,
        personal_tax_breakdown=personal_tax_breakdown,
        additional_personal_tax=additional_personal_tax,
        compliance_costs=compliance_costs,
        super_as_benefit=(config.super_treatment == SuperTreatment.AS_BENEFIT),
    )
    
    return result


def calculate_company_dividends(config: Config) -> CompanyDividendResult:
    """
    Calculate tax for company paying dividends only.
    
    When paying dividends:
    - Company pays 25% tax on profits
    - Remaining 75% distributed as fully franked dividends
    - You gross up dividend by adding franking credit
    - Pay personal tax on grossed-up amount
    - Subtract franking credit from personal tax
    
    IMPORTANT: If you have employment_salary from another job, the dividend
    income is ADDED to your personal income and taxed at marginal rates.
    
    Args:
        config: Configuration with business_profit and employment_salary
        
    Returns:
        CompanyDividendResult with complete breakdown
    """
    rates = get_rates(config.tax_year)
    
    company_profit = config.business_profit
    employment_salary = config.employment_salary
    
    # Company tax
    company_tax_breakdown = calculate_company_tax(
        taxable_income=company_profit,
        rates=rates,
        is_base_rate_entity=config.is_base_rate_entity,
    )
    
    # After-tax profit becomes dividend
    dividend_amount = company_tax_breakdown.after_tax_profit
    franking_credit = company_tax_breakdown.company_tax
    
    dividend_breakdown = DividendBreakdown(
        dividend_amount=dividend_amount,
        franking_credit=franking_credit,
    )
    
    # Personal tax on grossed-up dividend
    # If you have employment income, dividend is taxed at marginal rate
    grossed_up = dividend_breakdown.grossed_up_dividend
    
    # Total personal taxable income = employment + grossed-up dividend
    total_personal_taxable = employment_salary + grossed_up
    
    # Tax on combined income
    combined_tax_breakdown = calculate_individual_tax(
        taxable_income=total_personal_taxable,
        business_income=Decimal("0"),
        rates=rates,
    )
    
    # Calculate additional tax from dividend
    if employment_salary > 0:
        employment_only_tax = calculate_individual_tax(
            taxable_income=employment_salary,
            business_income=Decimal("0"),
            rates=rates,
        )
        # Additional tax before franking credit
        additional_tax_before_credit = combined_tax_breakdown.total_tax - employment_only_tax.total_tax
    else:
        additional_tax_before_credit = combined_tax_breakdown.total_tax
    
    # Tax payable on dividend = additional tax - franking credit
    # Can be negative (refund) if marginal rate < company rate
    personal_tax_on_dividends = additional_tax_before_credit - franking_credit
    
    # Store the combined breakdown
    personal_tax_breakdown = combined_tax_breakdown
    
    # Compliance costs if enabled (annual ongoing + amortized setup)
    compliance_costs = Decimal("0")
    if config.include_compliance_costs:
        compliance_costs = config.compliance_cost_company
    if config.include_setup_costs:
        amortized_setup = config.setup_cost_company / Decimal(str(config.years_to_amortize))
        compliance_costs += amortized_setup
    
    result = CompanyDividendResult(
        company_profit=company_profit,
        employment_salary=employment_salary,
        company_tax_breakdown=company_tax_breakdown,
        dividend_breakdown=dividend_breakdown,
        personal_tax_breakdown=personal_tax_breakdown,
        personal_tax_on_dividends=personal_tax_on_dividends,
        compliance_costs=compliance_costs,
    )
    
    return result


def calculate_company_mixed(
    config: Config,
    salary_amount: Decimal | None = None,
) -> CompanyMixedResult:
    """
    Calculate tax for company paying salary + dividends mix.
    
    Strategy:
    - Pay salary up to specified amount (or optimal if None)
    - Remaining profit taxed at company rate
    - After-tax remainder distributed as dividends
    
    IMPORTANT: If you have employment_salary from another job, both the
    company salary and dividends are ADDED to your personal income and
    taxed at marginal rates.
    
    Args:
        config: Configuration with business_profit and employment_salary
        salary_amount: Specific salary amount (if None, uses default split)
        
    Returns:
        CompanyMixedResult with complete breakdown
    """
    rates = get_rates(config.tax_year)
    
    company_profit = config.business_profit
    employment_salary = config.employment_salary
    
    # Default: pay salary up to $45,000 (top of 16% bracket)
    # But if you already have employment income, this needs adjustment
    # The optimal might be different when you're already in a higher bracket
    if salary_amount is None:
        # Default to the top of the second tax bracket minus employment salary
        # This way we fill up the lower brackets first
        remaining_in_low_bracket = max(Decimal("0"), Decimal("45000") - employment_salary)
        salary_amount = min(remaining_in_low_bracket, company_profit)
    
    # Calculate super on salary
    if config.include_super:
        super_contribution = calculate_super_guarantee(salary_amount, rates)
    else:
        super_contribution = Decimal("0")
    
    # Company's remaining profit after salary and super
    remaining_profit = company_profit - salary_amount - super_contribution
    remaining_profit = max(Decimal("0"), remaining_profit)
    
    # Company tax on remaining profit
    company_tax_breakdown = calculate_company_tax(
        taxable_income=remaining_profit,
        rates=rates,
        is_base_rate_entity=config.is_base_rate_entity,
    )
    
    # Dividend from after-tax remaining profit
    dividend_amount = company_tax_breakdown.after_tax_profit
    franking_credit = company_tax_breakdown.company_tax
    
    dividend_breakdown = DividendBreakdown(
        dividend_amount=dividend_amount,
        franking_credit=franking_credit,
    )
    
    # Personal income = employment + company salary + grossed-up dividend
    grossed_up_dividend = dividend_breakdown.grossed_up_dividend
    total_personal_taxable = employment_salary + salary_amount + grossed_up_dividend
    
    # Personal tax on combined income (employment + company salary + dividend)
    combined_tax_breakdown = calculate_individual_tax(
        taxable_income=total_personal_taxable,
        business_income=Decimal("0"),
        rates=rates,
    )
    
    # Calculate additional tax from company (salary + dividend)
    if employment_salary > 0:
        employment_only_tax = calculate_individual_tax(
            taxable_income=employment_salary,
            business_income=Decimal("0"),
            rates=rates,
        )
        # Additional tax before franking credit
        additional_tax_before_credit = combined_tax_breakdown.total_tax - employment_only_tax.total_tax
    else:
        additional_tax_before_credit = combined_tax_breakdown.total_tax
    
    # Adjust for franking credit
    additional_personal_tax = additional_tax_before_credit - franking_credit
    
    # Store combined breakdown
    personal_tax_breakdown = combined_tax_breakdown
    
    # Compliance costs if enabled (annual ongoing + amortized setup)
    compliance_costs = Decimal("0")
    if config.include_compliance_costs:
        compliance_costs = config.compliance_cost_company
    if config.include_setup_costs:
        amortized_setup = config.setup_cost_company / Decimal(str(config.years_to_amortize))
        compliance_costs += amortized_setup
    
    result = CompanyMixedResult(
        company_profit=company_profit,
        employment_salary=employment_salary,
        salary_paid=salary_amount,
        dividend_paid=dividend_amount,
        super_contribution=super_contribution,
        company_tax_breakdown=company_tax_breakdown,
        dividend_breakdown=dividend_breakdown,
        personal_tax_breakdown=personal_tax_breakdown,
        additional_personal_tax=additional_personal_tax,
        compliance_costs=compliance_costs,
        super_as_benefit=(config.super_treatment == SuperTreatment.AS_BENEFIT),
    )
    
    return result
