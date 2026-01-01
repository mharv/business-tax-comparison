"""
Optimizer for finding optimal salary/dividend split.

Iterates through possible salary amounts to find the
combination that minimizes total tax.
"""

from decimal import Decimal
from typing import NamedTuple

from tax_comparison.calculators.company import calculate_company_mixed
from tax_comparison.models import CompanyMixedResult, Config
from tax_comparison.rates import get_rates


class OptimizationResult(NamedTuple):
    """Result of salary/dividend optimization."""
    
    optimal_salary: Decimal
    optimal_dividend: Decimal
    result: CompanyMixedResult
    total_tax: Decimal


def optimize_salary_dividend_split(
    config: Config,
    step: Decimal | None = None,
) -> OptimizationResult:
    """
    Find the optimal salary/dividend split that minimizes total tax.
    
    Algorithm:
    1. Iterate salary from $0 to full profit (with super deducted)
    2. For each salary level, calculate total tax (company + personal)
    3. Return the salary level with minimum total tax
    
    Args:
        config: Configuration with business_profit
        step: Step size for iteration (default: config.optimization_step)
        
    Returns:
        OptimizationResult with optimal split and result
    """
    if step is None:
        step = config.optimization_step
    
    rates = get_rates(config.tax_year)
    company_profit = config.business_profit
    
    # If including super, max salary is reduced
    if config.include_super:
        max_salary = (company_profit / (1 + rates.super_guarantee_rate)).quantize(Decimal("0.01"))
    else:
        max_salary = company_profit
    
    best_result: CompanyMixedResult | None = None
    best_salary = Decimal("0")
    best_tax = Decimal("999999999")
    
    # Iterate through possible salary amounts
    current_salary = Decimal("0")
    while current_salary <= max_salary:
        result = calculate_company_mixed(config, salary_amount=current_salary)
        
        # Calculate total tax for this split
        # Company tax + personal tax (after franking credit)
        company_tax = result.company_tax_breakdown.company_tax
        personal_tax = result.personal_tax_breakdown.total_tax
        franking_credit = result.dividend_breakdown.franking_credit
        
        # Personal tax after franking credit offset
        net_personal_tax = max(Decimal("0"), personal_tax - franking_credit)
        
        total_tax = company_tax + net_personal_tax
        
        if total_tax < best_tax:
            best_tax = total_tax
            best_salary = current_salary
            best_result = result
        
        current_salary += step
    
    # Also check max salary
    if current_salary != max_salary:
        result = calculate_company_mixed(config, salary_amount=max_salary)
        company_tax = result.company_tax_breakdown.company_tax
        personal_tax = result.personal_tax_breakdown.total_tax
        franking_credit = result.dividend_breakdown.franking_credit
        net_personal_tax = max(Decimal("0"), personal_tax - franking_credit)
        total_tax = company_tax + net_personal_tax
        
        if total_tax < best_tax:
            best_tax = total_tax
            best_salary = max_salary
            best_result = result
    
    if best_result is None:
        # Fallback - should not happen
        best_result = calculate_company_mixed(config, salary_amount=Decimal("0"))
        best_tax = best_result.total_tax
    
    return OptimizationResult(
        optimal_salary=best_salary,
        optimal_dividend=best_result.dividend_paid,
        result=best_result,
        total_tax=best_tax,
    )
