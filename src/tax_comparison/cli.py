"""
CLI entry point for tax comparison tool.

Usage:
    uv run tax-compare --business-profit 100000
    uv run tax-compare --salary 80000 --business-profit 50000
    uv run tax-compare --business-profit 150000 --extraction-method mixed --optimize
"""

from decimal import Decimal

import click
from rich.console import Console

from tax_comparison.calculators.company import (
    calculate_company_dividends,
    calculate_company_mixed,
    calculate_company_salary,
)
from tax_comparison.calculators.sole_trader import calculate_sole_trader_tax
from tax_comparison.models import (
    ComparisonResult,
    Config,
    ExtractionMethod,
    OutputFormat,
    SuperTreatment,
)
from tax_comparison.optimizer import optimize_salary_dividend_split
from tax_comparison.output.export import export_to_csv, export_to_json
from tax_comparison.output.table import (
    render_comparison_table,
    render_detailed_breakdown,
    render_disclaimer,
)


console = Console()


@click.command()
@click.option(
    "--business-profit",
    "-p",
    type=float,
    required=True,
    help="Net profit from the business (required).",
)
@click.option(
    "--salary",
    "-s",
    type=float,
    default=0,
    help="Employment salary from another job (sole trader scenario only).",
)
@click.option(
    "--extraction-method",
    "-e",
    type=click.Choice(["salary", "dividends", "mixed", "all"], case_sensitive=False),
    default="all",
    help="How to extract money from company: salary, dividends, mixed, or all.",
)
@click.option(
    "--tax-year",
    "-y",
    type=click.Choice(["2024-25"]),
    default="2024-25",
    help="Tax year for rate calculations.",
)
@click.option(
    "--include-super/--no-include-super",
    default=True,
    help="Include superannuation in calculations.",
)
@click.option(
    "--super-as-benefit/--super-as-cost",
    default=True,
    help="Treat super as benefit (adds to total package) or cost (reduces profit).",
)
@click.option(
    "--include-compliance-costs/--no-compliance-costs",
    default=False,
    help="Include annual compliance costs in comparison.",
)
@click.option(
    "--compliance-cost-sole-trader",
    type=float,
    default=500,
    help="Annual compliance cost for sole trader (default: $500).",
)
@click.option(
    "--compliance-cost-company",
    type=float,
    default=3500,
    help="Annual compliance cost for company (default: $3500).",
)
@click.option(
    "--include-setup-costs/--no-setup-costs",
    default=False,
    help="Include one-time setup costs (amortized over 5 years).",
)
@click.option(
    "--setup-cost-sole-trader",
    type=float,
    default=100,
    help="One-time setup cost for sole trader (default: $100).",
)
@click.option(
    "--setup-cost-company",
    type=float,
    default=1500,
    help="One-time setup cost for company (default: $1500).",
)
@click.option(
    "--years-to-amortize",
    type=int,
    default=5,
    help="Years to spread setup costs over (default: 5).",
)
@click.option(
    "--optimize",
    is_flag=True,
    default=False,
    help="Find optimal salary/dividend split for mixed extraction.",
)
@click.option(
    "--output-format",
    "-o",
    type=click.Choice(["table", "json", "csv"], case_sensitive=False),
    default="table",
    help="Output format: table, json, or csv.",
)
@click.option(
    "--detailed",
    "-d",
    is_flag=True,
    default=False,
    help="Show detailed breakdown for each scenario.",
)
@click.option(
    "--no-disclaimer",
    is_flag=True,
    default=False,
    help="Hide the disclaimer notice.",
)
def main(
    business_profit: float,
    salary: float,
    extraction_method: str,
    tax_year: str,
    include_super: bool,
    super_as_benefit: bool,
    include_compliance_costs: bool,
    compliance_cost_sole_trader: float,
    compliance_cost_company: float,
    include_setup_costs: bool,
    setup_cost_sole_trader: float,
    setup_cost_company: float,
    years_to_amortize: int,
    optimize: bool,
    output_format: str,
    detailed: bool,
    no_disclaimer: bool,
) -> None:
    """
    Compare tax between sole trader and company business structures.
    
    This tool calculates and compares the total tax obligations for different
    business structures in Australia, helping you make informed decisions
    about your business setup.
    
    \b
    Examples:
        # Basic comparison with $100,000 business profit
        uv run tax-compare --business-profit 100000
        
        # Sole trader with employment salary + side business
        uv run tax-compare --salary 80000 --business-profit 50000
        
        # Find optimal salary/dividend split
        uv run tax-compare --business-profit 150000 --optimize
        
        # Include compliance costs
        uv run tax-compare --business-profit 100000 --include-compliance-costs
        
        # Export to JSON
        uv run tax-compare --business-profit 100000 --output-format json
    """
    # Validate inputs
    if business_profit < 0:
        raise click.BadParameter("Business profit cannot be negative.")
    if salary < 0:
        raise click.BadParameter("Salary cannot be negative.")
    
    # Build configuration
    config = Config(
        business_profit=Decimal(str(business_profit)),
        employment_salary=Decimal(str(salary)),
        extraction_method=ExtractionMethod(extraction_method.lower()),
        tax_year=tax_year,
        include_super=include_super,
        super_treatment=SuperTreatment.AS_BENEFIT if super_as_benefit else SuperTreatment.AS_COST,
        include_compliance_costs=include_compliance_costs,
        compliance_cost_sole_trader=Decimal(str(compliance_cost_sole_trader)),
        compliance_cost_company=Decimal(str(compliance_cost_company)),
        include_setup_costs=include_setup_costs,
        setup_cost_sole_trader=Decimal(str(setup_cost_sole_trader)),
        setup_cost_company=Decimal(str(setup_cost_company)),
        years_to_amortize=years_to_amortize,
        optimize=optimize,
    )
    
    # Calculate scenarios
    result = calculate_all_scenarios(config)
    
    # Output results
    output_fmt = OutputFormat(output_format.lower())
    
    if output_fmt == OutputFormat.JSON:
        click.echo(export_to_json(result))
    elif output_fmt == OutputFormat.CSV:
        click.echo(export_to_csv(result))
    else:
        # Table output
        if not no_disclaimer:
            render_disclaimer(console)
        
        if detailed:
            render_detailed_breakdown(result, console)
        
        render_comparison_table(result, console)


def calculate_all_scenarios(config: Config) -> ComparisonResult:
    """
    Calculate all requested scenarios based on configuration.
    
    Args:
        config: Configuration with inputs and options
        
    Returns:
        ComparisonResult with all calculated scenarios
    """
    result = ComparisonResult(config=config)
    
    # Always calculate sole trader
    result.sole_trader = calculate_sole_trader_tax(config)
    
    extraction = config.extraction_method
    
    # Calculate company scenarios based on extraction method
    if extraction in (ExtractionMethod.ALL, ExtractionMethod.SALARY):
        result.company_salary = calculate_company_salary(config)
    
    if extraction in (ExtractionMethod.ALL, ExtractionMethod.DIVIDENDS):
        result.company_dividends = calculate_company_dividends(config)
    
    if extraction in (ExtractionMethod.ALL, ExtractionMethod.MIXED):
        if config.optimize:
            # Find optimal split
            opt_result = optimize_salary_dividend_split(config)
            result.company_mixed = opt_result.result
            result.optimal_salary = opt_result.optimal_salary
            result.optimal_dividends = opt_result.optimal_dividend
        else:
            # Use default split (salary up to $45,000)
            result.company_mixed = calculate_company_mixed(config)
    
    return result


if __name__ == "__main__":
    main()
