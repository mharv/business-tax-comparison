#!/usr/bin/env python3
"""
Optimization and Charting Script

This script analyzes tax implications across different Annual Revenue Rates (ARR)
for your business, comparing sole trader vs company structures.

Usage:
    uv run python scripts/analyze_arr.py --salary 80000 --arr-min 20000 --arr-max 200000
    uv run python scripts/analyze_arr.py --salary 120000 --arr-min 50000 --arr-max 300000 --step 10000
"""

import argparse
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

# Optional matplotlib import
try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed. Run 'uv add matplotlib' for charts.")

from tax_comparison.calculators.company import (
    calculate_company_dividends,
    calculate_company_mixed,
    calculate_company_salary,
)
from tax_comparison.calculators.sole_trader import calculate_sole_trader_tax
from tax_comparison.models import Config
from tax_comparison.optimizer import optimize_salary_dividend_split


@dataclass
class AnalysisResult:
    """Result for a single ARR point."""
    
    arr: float
    
    # Sole trader
    sole_trader_tax: float
    sole_trader_take_home: float
    sole_trader_effective_rate: float
    
    # Company - Salary
    company_salary_tax: float
    company_salary_take_home: float
    company_salary_super: float
    company_salary_effective_rate: float
    
    # Company - Dividends
    company_dividends_tax: float
    company_dividends_take_home: float
    company_dividends_effective_rate: float
    
    # Company - Optimized Mix
    company_mixed_tax: float
    company_mixed_take_home: float
    company_mixed_super: float
    company_mixed_effective_rate: float
    company_mixed_optimal_salary: float
    company_mixed_optimal_dividend: float
    
    @property
    def best_structure(self) -> str:
        """Return the name of the best structure (lowest tax)."""
        options = [
            ("Sole Trader", self.sole_trader_tax),
            ("Company (Salary)", self.company_salary_tax),
            ("Company (Dividends)", self.company_dividends_tax),
            ("Company (Mixed)", self.company_mixed_tax),
        ]
        return min(options, key=lambda x: x[1])[0]
    
    @property
    def best_take_home(self) -> float:
        """Return the best take-home amount."""
        return max(
            self.sole_trader_take_home,
            self.company_salary_take_home,
            self.company_dividends_take_home,
            self.company_mixed_take_home,
        )


def analyze_arr(
    employment_salary: float,
    business_profit: float,
    include_compliance_costs: bool = False,
    include_setup_costs: bool = False,
) -> AnalysisResult:
    """
    Analyze tax for a specific ARR (Annual Revenue Rate / business profit).
    
    Args:
        employment_salary: Your annual salary from employment
        business_profit: Annual profit from the business
        include_compliance_costs: Whether to include compliance costs
        include_setup_costs: Whether to include setup costs (amortized)
        
    Returns:
        AnalysisResult with all scenarios
    """
    config = Config(
        business_profit=Decimal(str(business_profit)),
        employment_salary=Decimal(str(employment_salary)),
        include_compliance_costs=include_compliance_costs,
        include_setup_costs=include_setup_costs,
        include_super=True,
    )
    
    # Sole trader
    sole_trader = calculate_sole_trader_tax(config)
    
    # Company - Salary only
    company_salary = calculate_company_salary(config)
    
    # Company - Dividends only
    company_dividends = calculate_company_dividends(config)
    
    # Company - Optimized mix
    opt_result = optimize_salary_dividend_split(config)
    company_mixed = opt_result.result
    
    return AnalysisResult(
        arr=business_profit,
        
        sole_trader_tax=float(sole_trader.total_tax),
        sole_trader_take_home=float(sole_trader.take_home),
        sole_trader_effective_rate=float(sole_trader.effective_rate),
        
        company_salary_tax=float(company_salary.total_tax),
        company_salary_take_home=float(company_salary.take_home_cash),
        company_salary_super=float(company_salary.super_contribution),
        company_salary_effective_rate=float(company_salary.effective_rate),
        
        company_dividends_tax=float(company_dividends.total_tax),
        company_dividends_take_home=float(company_dividends.take_home_cash),
        company_dividends_effective_rate=float(company_dividends.effective_rate),
        
        company_mixed_tax=float(opt_result.total_tax),
        company_mixed_take_home=float(company_mixed.take_home_cash),
        company_mixed_super=float(company_mixed.super_contribution),
        company_mixed_effective_rate=float(company_mixed.effective_rate),
        company_mixed_optimal_salary=float(opt_result.optimal_salary),
        company_mixed_optimal_dividend=float(opt_result.optimal_dividend),
    )


def run_analysis(
    employment_salary: float,
    arr_min: float,
    arr_max: float,
    step: float = 5000,
    include_compliance_costs: bool = False,
    include_setup_costs: bool = False,
) -> list[AnalysisResult]:
    """
    Run analysis across a range of ARR values.
    
    Args:
        employment_salary: Your annual salary from employment
        arr_min: Minimum ARR to analyze
        arr_max: Maximum ARR to analyze
        step: Step size between ARR values
        include_compliance_costs: Whether to include compliance costs
        include_setup_costs: Whether to include setup costs (amortized)
        
    Returns:
        List of AnalysisResult for each ARR point
    """
    results = []
    current = arr_min
    
    while current <= arr_max:
        result = analyze_arr(
            employment_salary=employment_salary,
            business_profit=current,
            include_compliance_costs=include_compliance_costs,
            include_setup_costs=include_setup_costs,
        )
        results.append(result)
        current += step
    
    return results


def print_summary_table(results: list[AnalysisResult], employment_salary: float) -> None:
    """Print a summary table of results."""
    print(f"\n{'='*100}")
    print(f"Tax Comparison Analysis - Employment Salary: ${employment_salary:,.0f}")
    print(f"{'='*100}")
    print(f"{'ARR':>12} | {'Sole Trader':>14} | {'Co. Salary':>14} | {'Co. Dividends':>14} | {'Co. Mixed':>14} | {'Best Option':>18}")
    print(f"{'':>12} | {'Tax / Rate':>14} | {'Tax / Rate':>14} | {'Tax / Rate':>14} | {'Tax / Rate':>14} | {'':>18}")
    print(f"{'-'*12}-+-{'-'*14}-+-{'-'*14}-+-{'-'*14}-+-{'-'*14}-+-{'-'*18}")
    
    for r in results:
        print(
            f"${r.arr:>10,.0f} | "
            f"${r.sole_trader_tax:>8,.0f} {r.sole_trader_effective_rate*100:>4.1f}% | "
            f"${r.company_salary_tax:>8,.0f} {r.company_salary_effective_rate*100:>4.1f}% | "
            f"${r.company_dividends_tax:>8,.0f} {r.company_dividends_effective_rate*100:>4.1f}% | "
            f"${r.company_mixed_tax:>8,.0f} {r.company_mixed_effective_rate*100:>4.1f}% | "
            f"{r.best_structure:>18}"
        )
    
    print(f"{'='*100}\n")


def print_optimal_splits(results: list[AnalysisResult]) -> None:
    """Print optimal salary/dividend splits for company mixed structure."""
    print(f"\n{'='*80}")
    print("Optimal Salary/Dividend Split (Company Mixed Structure)")
    print(f"{'='*80}")
    print(f"{'ARR':>12} | {'Optimal Salary':>15} | {'Optimal Dividend':>16} | {'Total Tax':>12} | {'Take-Home':>12}")
    print(f"{'-'*12}-+-{'-'*15}-+-{'-'*16}-+-{'-'*12}-+-{'-'*12}")
    
    for r in results:
        print(
            f"${r.arr:>10,.0f} | "
            f"${r.company_mixed_optimal_salary:>13,.0f} | "
            f"${r.company_mixed_optimal_dividend:>14,.0f} | "
            f"${r.company_mixed_tax:>10,.0f} | "
            f"${r.company_mixed_take_home:>10,.0f}"
        )
    
    print(f"{'='*80}\n")


def print_comparison_table(
    employment_salary: float,
    arr_min: float,
    arr_max: float,
    step: float = 10000,
    include_compliance_costs: bool = True,
    include_setup_costs: bool = True,
) -> None:
    """
    Print a detailed side-by-side comparison of Sole Trader vs Company.
    
    Args:
        employment_salary: Annual salary from employment
        arr_min: Minimum ARR to analyze
        arr_max: Maximum ARR to analyze
        step: Step size between ARR values
        include_compliance_costs: Include ongoing compliance costs
        include_setup_costs: Include amortized setup costs
    """
    print()
    print('=' * 120)
    costs_note = ""
    if include_compliance_costs or include_setup_costs:
        costs = []
        if include_compliance_costs:
            costs.append("Compliance")
        if include_setup_costs:
            costs.append("Setup")
        costs_note = f" | Includes {' & '.join(costs)} Costs"
    print(f'Sole Trader vs Company Comparison | Employment Salary: ${employment_salary:,.0f}{costs_note}')
    print('=' * 120)
    print(f"{'ARR':>12} | {'SOLE TRADER':^35} | {'COMPANY (Salary)':^40} | {'BENEFIT':^18}")
    print(f"{'':>12} | {'Tax+Costs':>12} {'Take-Home':>12} {'Eff.Rate':>8} | {'Tax+Costs':>12} {'Cash':>12} {'Super':>10} | {'Tax Saved':>9} {'Extra $':>8}")
    print('-' * 120)
    
    current = arr_min
    while current <= arr_max:
        config = Config(
            business_profit=Decimal(str(current)),
            employment_salary=Decimal(str(employment_salary)),
            include_compliance_costs=include_compliance_costs,
            include_setup_costs=include_setup_costs,
        )
        
        st = calculate_sole_trader_tax(config)
        co = calculate_company_salary(config)
        
        # Sole trader totals
        st_total_cost = float(st.total_tax + st.compliance_costs)
        st_take_home = float(st.take_home)
        st_eff_rate = st_total_cost / (employment_salary + current) * 100
        
        # Company totals  
        co_total_cost = float(co.total_tax + co.compliance_costs)
        co_cash = float(co.take_home_cash)
        co_super = float(co.super_contribution)
        
        # Savings
        st_business_take_home = st_take_home - employment_salary
        tax_saved = st_total_cost - co_total_cost
        extra_cash = co_cash - st_business_take_home + co_super
        
        print(
            f'${current:>10,.0f} | '
            f'${st_total_cost:>10,.0f} ${st_take_home:>10,.0f} {st_eff_rate:>7.1f}% | '
            f'${co_total_cost:>10,.0f} ${co_cash:>10,.0f} ${co_super:>8,.0f} | '
            f'${tax_saved:>7,.0f} ${extra_cash:>7,.0f}'
        )
        current += step
    
    print('-' * 120)
    print()
    print('NOTES:')
    print('  • Tax+Costs = Income Tax + Medicare Levy - SBITO + Compliance + Amortized Setup')
    print('  • Sole Trader Take-Home = Employment Salary + Business Profit - Tax - Costs')
    print('  • Company Cash = Salary from Company - Additional Personal Tax - Costs')
    print('  • Super = Superannuation (11.5% of company salary) - additional retirement benefit')
    print('  • Tax Saved = What you save by using Company instead of Sole Trader')
    print('  • Extra $ = Total additional benefit (cash + super) vs Sole Trader')
    print()


def create_charts(
    results: list[AnalysisResult],
    employment_salary: float,
    output_dir: Path | None = None,
) -> None:
    """
    Create comparison charts.
    
    Args:
        results: List of analysis results
        employment_salary: Employment salary for title
        output_dir: Directory to save charts (None = display only)
    """
    if not HAS_MATPLOTLIB:
        print("Charts require matplotlib. Install with: uv add matplotlib")
        return
    
    arr_values = [r.arr for r in results]
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"Business Structure Tax Comparison\nEmployment Salary: ${employment_salary:,.0f}",
        fontsize=14,
        fontweight="bold",
    )
    
    # Chart 1: Total Tax Comparison
    ax1 = axes[0, 0]
    ax1.plot(arr_values, [r.sole_trader_tax for r in results], label="Sole Trader", linewidth=2, marker="o", markersize=4)
    ax1.plot(arr_values, [r.company_salary_tax for r in results], label="Company (Salary)", linewidth=2, marker="s", markersize=4)
    ax1.plot(arr_values, [r.company_dividends_tax for r in results], label="Company (Dividends)", linewidth=2, marker="^", markersize=4)
    ax1.plot(arr_values, [r.company_mixed_tax for r in results], label="Company (Mixed)", linewidth=2, marker="d", markersize=4)
    ax1.set_xlabel("Business Profit (ARR)")
    ax1.set_ylabel("Total Tax ($)")
    ax1.set_title("Total Tax by Business Structure")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))
    
    # Chart 2: Take-Home Cash Comparison
    ax2 = axes[0, 1]
    ax2.plot(arr_values, [r.sole_trader_take_home for r in results], label="Sole Trader", linewidth=2, marker="o", markersize=4)
    ax2.plot(arr_values, [r.company_salary_take_home for r in results], label="Company (Salary)", linewidth=2, marker="s", markersize=4)
    ax2.plot(arr_values, [r.company_dividends_take_home for r in results], label="Company (Dividends)", linewidth=2, marker="^", markersize=4)
    ax2.plot(arr_values, [r.company_mixed_take_home for r in results], label="Company (Mixed)", linewidth=2, marker="d", markersize=4)
    ax2.set_xlabel("Business Profit (ARR)")
    ax2.set_ylabel("Take-Home Cash ($)")
    ax2.set_title("Take-Home Cash by Business Structure")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))
    
    # Chart 3: Effective Tax Rate Comparison
    ax3 = axes[1, 0]
    ax3.plot(arr_values, [r.sole_trader_effective_rate * 100 for r in results], label="Sole Trader", linewidth=2, marker="o", markersize=4)
    ax3.plot(arr_values, [r.company_salary_effective_rate * 100 for r in results], label="Company (Salary)", linewidth=2, marker="s", markersize=4)
    ax3.plot(arr_values, [r.company_dividends_effective_rate * 100 for r in results], label="Company (Dividends)", linewidth=2, marker="^", markersize=4)
    ax3.plot(arr_values, [r.company_mixed_effective_rate * 100 for r in results], label="Company (Mixed)", linewidth=2, marker="d", markersize=4)
    ax3.set_xlabel("Business Profit (ARR)")
    ax3.set_ylabel("Effective Tax Rate (%)")
    ax3.set_title("Effective Tax Rate by Business Structure")
    ax3.legend(loc="lower right")
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))
    ax3.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:.0f}%"))
    
    # Chart 4: Optimal Salary/Dividend Split
    ax4 = axes[1, 1]
    ax4.fill_between(
        arr_values,
        [0] * len(results),
        [r.company_mixed_optimal_salary for r in results],
        label="Salary",
        alpha=0.7,
    )
    ax4.fill_between(
        arr_values,
        [r.company_mixed_optimal_salary for r in results],
        [r.company_mixed_optimal_salary + r.company_mixed_optimal_dividend for r in results],
        label="Dividend",
        alpha=0.7,
    )
    ax4.plot(
        arr_values,
        [r.company_mixed_optimal_salary + r.company_mixed_optimal_dividend + r.company_mixed_super for r in results],
        label="+ Super",
        linewidth=2,
        linestyle="--",
        color="green",
    )
    ax4.set_xlabel("Business Profit (ARR)")
    ax4.set_ylabel("Amount ($)")
    ax4.set_title("Optimal Company Extraction (Mixed)")
    ax4.legend(loc="upper left")
    ax4.grid(True, alpha=0.3)
    ax4.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))
    ax4.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))
    
    plt.tight_layout()
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "tax_comparison_charts.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Charts saved to: {output_path}")
    
    plt.show()


def create_savings_chart(
    results: list[AnalysisResult],
    employment_salary: float,
    output_dir: Path | None = None,
) -> None:
    """
    Create a chart showing tax savings of company vs sole trader.
    
    Args:
        results: List of analysis results
        employment_salary: Employment salary for title
        output_dir: Directory to save chart (None = display only)
    """
    if not HAS_MATPLOTLIB:
        return
    
    arr_values = [r.arr for r in results]
    
    # Calculate savings (positive = company saves money)
    salary_savings = [r.sole_trader_tax - r.company_salary_tax for r in results]
    dividend_savings = [r.sole_trader_tax - r.company_dividends_tax for r in results]
    mixed_savings = [r.sole_trader_tax - r.company_mixed_tax for r in results]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.fill_between(arr_values, 0, mixed_savings, alpha=0.3, label="Mixed Savings", color="green")
    ax.plot(arr_values, salary_savings, label="Company (Salary) vs Sole Trader", linewidth=2, marker="s", markersize=4)
    ax.plot(arr_values, dividend_savings, label="Company (Dividends) vs Sole Trader", linewidth=2, marker="^", markersize=4)
    ax.plot(arr_values, mixed_savings, label="Company (Mixed) vs Sole Trader", linewidth=2, marker="d", markersize=4, color="green")
    
    ax.set_xlabel("Business Profit (ARR)")
    ax.set_ylabel("Tax Savings ($)")
    ax.set_title(
        f"Tax Savings: Company Structure vs Sole Trader\n"
        f"(Employment Salary: ${employment_salary:,.0f})\n"
        f"Positive = Company saves money"
    )
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))
    
    plt.tight_layout()
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "tax_savings_chart.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Savings chart saved to: {output_path}")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze tax implications across different ARR levels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic analysis with $80k salary, ARR from $20k to $200k
    python scripts/analyze_arr.py --salary 80000 --arr-min 20000 --arr-max 200000
    
    # Higher salary, larger ARR range with $10k steps
    python scripts/analyze_arr.py --salary 120000 --arr-min 50000 --arr-max 500000 --step 10000
    
    # Include compliance costs and save charts
    python scripts/analyze_arr.py --salary 100000 --arr-min 30000 --arr-max 250000 --compliance-costs --save-charts
        """,
    )
    
    parser.add_argument(
        "--salary", "-s",
        type=float,
        required=True,
        help="Your annual employment salary",
    )
    parser.add_argument(
        "--arr-min",
        type=float,
        default=20000,
        help="Minimum ARR (business profit) to analyze (default: 20000)",
    )
    parser.add_argument(
        "--arr-max",
        type=float,
        default=200000,
        help="Maximum ARR (business profit) to analyze (default: 200000)",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=5000,
        help="Step size between ARR values (default: 5000)",
    )
    parser.add_argument(
        "--compliance-costs",
        action="store_true",
        help="Include compliance costs in calculations",
    )
    parser.add_argument(
        "--setup-costs",
        action="store_true",
        help="Include setup costs (amortized over 5 years) in calculations",
    )
    parser.add_argument(
        "--save-charts",
        action="store_true",
        help="Save charts to files instead of just displaying",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Directory to save chart files (default: current directory)",
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Skip chart generation",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Show detailed Sole Trader vs Company comparison table",
    )
    
    args = parser.parse_args()
    
    print(f"\n🔍 Running tax analysis...")
    print(f"   Employment Salary: ${args.salary:,.0f}")
    print(f"   ARR Range: ${args.arr_min:,.0f} - ${args.arr_max:,.0f}")
    print(f"   Step Size: ${args.step:,.0f}")
    print(f"   Include Compliance Costs: {args.compliance_costs}")
    print(f"   Include Setup Costs: {args.setup_costs}")
    
    # Show comparison table if requested
    if args.compare:
        print_comparison_table(
            employment_salary=args.salary,
            arr_min=args.arr_min,
            arr_max=args.arr_max,
            step=args.step,
            include_compliance_costs=args.compliance_costs,
            include_setup_costs=args.setup_costs,
        )
        return
    
    # Run analysis
    results = run_analysis(
        employment_salary=args.salary,
        arr_min=args.arr_min,
        arr_max=args.arr_max,
        step=args.step,
        include_compliance_costs=args.compliance_costs,
        include_setup_costs=args.setup_costs,
    )
    
    # Print summary tables
    print_summary_table(results, args.salary)
    print_optimal_splits(results)
    
    # Find breakeven points
    print("\n📊 Key Insights:")
    for i, r in enumerate(results):
        if i == 0:
            continue
        prev = results[i - 1]
        
        # Check if best structure changed
        if r.best_structure != prev.best_structure:
            print(f"   ⚡ At ~${r.arr:,.0f} ARR: Best structure changes from {prev.best_structure} to {r.best_structure}")
    
    # Create charts
    if not args.no_charts and HAS_MATPLOTLIB:
        output_dir = args.output_dir if args.save_charts else None
        create_charts(results, args.salary, output_dir)
        create_savings_chart(results, args.salary, output_dir)


if __name__ == "__main__":
    main()
