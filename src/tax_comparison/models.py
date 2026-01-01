"""
Data models for tax comparison calculations.

Defines dataclasses for:
- Configuration options
- Tax calculation results
- Comparison scenarios
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional


class ExtractionMethod(str, Enum):
    """Methods for extracting money from a company."""
    
    SALARY = "salary"           # Pay yourself a wage/salary
    DIVIDENDS = "dividends"     # Distribute profits as dividends
    MIXED = "mixed"             # Combination of salary and dividends
    ALL = "all"                 # Calculate all methods for comparison


class SuperTreatment(str, Enum):
    """How to treat superannuation in calculations."""
    
    AS_BENEFIT = "benefit"      # Super adds to total remuneration package
    AS_COST = "cost"            # Super is a cost reducing available profit


class OutputFormat(str, Enum):
    """Output format for results."""
    
    TABLE = "table"             # Rich formatted table
    JSON = "json"               # JSON output
    CSV = "csv"                 # CSV output


@dataclass
class Config:
    """
    Configuration options for tax comparison.
    
    These are passed through from CLI arguments and control
    how calculations are performed and results displayed.
    """
    
    # Required inputs
    business_profit: Decimal
    
    # Optional inputs
    employment_salary: Decimal = Decimal("0")
    extraction_method: ExtractionMethod = ExtractionMethod.ALL
    
    # Tax year
    tax_year: str = "2024-25"
    
    # Superannuation options
    include_super: bool = True
    super_treatment: SuperTreatment = SuperTreatment.AS_BENEFIT
    
    # Compliance costs (annual ongoing)
    include_compliance_costs: bool = False
    compliance_cost_sole_trader: Decimal = Decimal("500")
    compliance_cost_company: Decimal = Decimal("3500")
    
    # Setup costs (one-time, amortized over years_to_amortize)
    include_setup_costs: bool = False
    setup_cost_sole_trader: Decimal = Decimal("100")
    setup_cost_company: Decimal = Decimal("1500")
    years_to_amortize: int = 5  # Spread setup costs over this many years
    
    # Optimization
    optimize: bool = False
    optimization_step: Decimal = Decimal("1000")  # Step size for optimization
    
    # Output options
    show_chart: bool = False
    output_format: OutputFormat = OutputFormat.TABLE
    
    # Company assumptions
    is_base_rate_entity: bool = True  # Assume <$50M turnover, <80% passive income


@dataclass
class IndividualTaxBreakdown:
    """Breakdown of individual income tax calculation."""
    
    taxable_income: Decimal
    
    # Tax components
    income_tax: Decimal              # Base income tax from brackets
    medicare_levy: Decimal           # Medicare levy (usually 2%)
    
    # Offsets
    sbito: Decimal = Decimal("0")    # Small Business Income Tax Offset
    
    # Derived
    @property
    def total_tax(self) -> Decimal:
        """Total tax payable after offsets."""
        return max(Decimal("0"), self.income_tax + self.medicare_levy - self.sbito)
    
    @property
    def effective_rate(self) -> Decimal:
        """Effective tax rate as a decimal."""
        if self.taxable_income == 0:
            return Decimal("0")
        return self.total_tax / self.taxable_income


@dataclass
class CompanyTaxBreakdown:
    """Breakdown of company tax calculation."""
    
    company_profit: Decimal
    company_tax_rate: Decimal
    
    # Tax paid by company
    company_tax: Decimal
    
    # Amount available for distribution
    @property
    def after_tax_profit(self) -> Decimal:
        """Profit available after company tax."""
        return self.company_profit - self.company_tax


@dataclass
class DividendBreakdown:
    """Breakdown of dividend taxation."""
    
    dividend_amount: Decimal         # Cash dividend received
    franking_credit: Decimal         # Franking credit attached
    
    @property
    def grossed_up_dividend(self) -> Decimal:
        """Dividend grossed up with franking credit."""
        return self.dividend_amount + self.franking_credit


@dataclass
class SoleTraderResult:
    """Complete result for sole trader scenario."""
    
    # Inputs
    employment_salary: Decimal
    business_profit: Decimal
    
    # Tax breakdown
    tax_breakdown: IndividualTaxBreakdown
    
    # Optional costs
    compliance_costs: Decimal = Decimal("0")
    
    @property
    def total_income(self) -> Decimal:
        """Total taxable income."""
        return self.employment_salary + self.business_profit
    
    @property
    def total_tax(self) -> Decimal:
        """Total tax payable."""
        return self.tax_breakdown.total_tax
    
    @property
    def take_home(self) -> Decimal:
        """Take-home cash after tax and compliance costs."""
        return self.total_income - self.total_tax - self.compliance_costs
    
    @property
    def effective_rate(self) -> Decimal:
        """Effective tax rate on total income."""
        if self.total_income == 0:
            return Decimal("0")
        return self.total_tax / self.total_income


@dataclass
class CompanySalaryResult:
    """Result for company paying salary only."""
    
    # Inputs
    company_profit: Decimal
    salary_paid: Decimal
    
    # Employment context (for marginal rate calculation)
    employment_salary: Decimal = Decimal("0")
    
    # Super
    super_contribution: Decimal = Decimal("0")
    
    # Tax breakdowns
    company_tax_breakdown: CompanyTaxBreakdown = field(default_factory=lambda: CompanyTaxBreakdown(
        company_profit=Decimal("0"),
        company_tax_rate=Decimal("0"),
        company_tax=Decimal("0"),
    ))
    personal_tax_breakdown: IndividualTaxBreakdown = field(default_factory=lambda: IndividualTaxBreakdown(
        taxable_income=Decimal("0"),
        income_tax=Decimal("0"),
        medicare_levy=Decimal("0"),
    ))
    
    # Additional personal tax from company income (when employment_salary > 0)
    additional_personal_tax: Decimal | None = None
    
    # Optional costs
    compliance_costs: Decimal = Decimal("0")
    
    # Super treatment
    super_as_benefit: bool = True
    
    @property
    def total_tax(self) -> Decimal:
        """
        Total tax attributable to the company.
        
        If you have employment salary, this is the ADDITIONAL tax caused by
        the company income (company tax + marginal personal tax on salary).
        """
        company_tax = self.company_tax_breakdown.company_tax
        if self.additional_personal_tax is not None:
            return company_tax + self.additional_personal_tax
        return company_tax + self.personal_tax_breakdown.total_tax
    
    @property
    def take_home_cash(self) -> Decimal:
        """Cash received from company (salary after additional personal tax)."""
        if self.additional_personal_tax is not None:
            return self.salary_paid - self.additional_personal_tax - self.compliance_costs
        return self.salary_paid - self.personal_tax_breakdown.total_tax - self.compliance_costs
    
    @property
    def total_benefit(self) -> Decimal:
        """Total benefit including super (if treated as benefit)."""
        if self.super_as_benefit:
            return self.take_home_cash + self.super_contribution
        return self.take_home_cash
    
    @property
    def effective_rate(self) -> Decimal:
        """Effective tax rate on company profit."""
        if self.company_profit == 0:
            return Decimal("0")
        return self.total_tax / self.company_profit


@dataclass
class CompanyDividendResult:
    """Result for company paying dividends only."""
    
    # Inputs
    company_profit: Decimal
    
    # Employment context (for marginal rate calculation)
    employment_salary: Decimal = Decimal("0")
    
    # Tax breakdowns
    company_tax_breakdown: CompanyTaxBreakdown = field(default_factory=lambda: CompanyTaxBreakdown(
        company_profit=Decimal("0"),
        company_tax_rate=Decimal("0"),
        company_tax=Decimal("0"),
    ))
    dividend_breakdown: DividendBreakdown = field(default_factory=lambda: DividendBreakdown(
        dividend_amount=Decimal("0"),
        franking_credit=Decimal("0"),
    ))
    personal_tax_breakdown: IndividualTaxBreakdown = field(default_factory=lambda: IndividualTaxBreakdown(
        taxable_income=Decimal("0"),
        income_tax=Decimal("0"),
        medicare_levy=Decimal("0"),
    ))
    
    # Additional personal tax on dividends (after franking credit)
    # This accounts for employment salary marginal rate
    personal_tax_on_dividends: Decimal = Decimal("0")
    
    # Optional costs
    compliance_costs: Decimal = Decimal("0")
    
    @property
    def total_tax(self) -> Decimal:
        """
        Total tax attributable to the company.
        
        Company tax + additional personal tax on dividends (at marginal rate).
        """
        return self.company_tax_breakdown.company_tax + max(Decimal("0"), self.personal_tax_on_dividends)
    
    @property
    def take_home_cash(self) -> Decimal:
        """Cash received from company (dividend minus additional personal tax)."""
        # If personal_tax_on_dividends is negative, it's a franking credit refund
        return self.dividend_breakdown.dividend_amount - max(Decimal("0"), self.personal_tax_on_dividends) - self.compliance_costs
    
    @property
    def effective_rate(self) -> Decimal:
        """Effective tax rate on company profit."""
        if self.company_profit == 0:
            return Decimal("0")
        return self.total_tax / self.company_profit


@dataclass
class CompanyMixedResult:
    """Result for company paying salary + dividends mix."""
    
    # Inputs
    company_profit: Decimal
    salary_paid: Decimal
    dividend_paid: Decimal
    
    # Employment context (for marginal rate calculation)
    employment_salary: Decimal = Decimal("0")
    
    # Super
    super_contribution: Decimal = Decimal("0")
    
    # Tax breakdowns
    company_tax_breakdown: CompanyTaxBreakdown = field(default_factory=lambda: CompanyTaxBreakdown(
        company_profit=Decimal("0"),
        company_tax_rate=Decimal("0"),
        company_tax=Decimal("0"),
    ))
    dividend_breakdown: DividendBreakdown = field(default_factory=lambda: DividendBreakdown(
        dividend_amount=Decimal("0"),
        franking_credit=Decimal("0"),
    ))
    personal_tax_breakdown: IndividualTaxBreakdown = field(default_factory=lambda: IndividualTaxBreakdown(
        taxable_income=Decimal("0"),
        income_tax=Decimal("0"),
        medicare_levy=Decimal("0"),
    ))
    
    # Additional personal tax from company (accounts for employment salary marginal rate)
    additional_personal_tax: Decimal | None = None
    
    # Optional costs
    compliance_costs: Decimal = Decimal("0")
    
    # Super treatment
    super_as_benefit: bool = True
    
    @property
    def total_tax(self) -> Decimal:
        """
        Total tax attributable to the company.
        
        Company tax + additional personal tax (at marginal rate after employment income).
        """
        company_tax = self.company_tax_breakdown.company_tax
        if self.additional_personal_tax is not None:
            return company_tax + max(Decimal("0"), self.additional_personal_tax)
        # Fallback: use full personal tax minus franking credit
        franking = self.dividend_breakdown.franking_credit
        return company_tax + max(Decimal("0"), self.personal_tax_breakdown.total_tax - franking)
    
    @property
    def take_home_cash(self) -> Decimal:
        """Cash received from company (salary + dividend after additional personal tax)."""
        total_from_company = self.salary_paid + self.dividend_paid
        if self.additional_personal_tax is not None:
            return total_from_company - max(Decimal("0"), self.additional_personal_tax) - self.compliance_costs
        # Fallback
        franking = self.dividend_breakdown.franking_credit
        net_personal_tax = max(Decimal("0"), self.personal_tax_breakdown.total_tax - franking)
        return total_from_company - net_personal_tax - self.compliance_costs
    
    @property
    def total_benefit(self) -> Decimal:
        """Total benefit including super (if treated as benefit)."""
        if self.super_as_benefit:
            return self.take_home_cash + self.super_contribution
        return self.take_home_cash
    
    @property
    def effective_rate(self) -> Decimal:
        """Effective tax rate on company profit."""
        if self.company_profit == 0:
            return Decimal("0")
        return self.total_tax / self.company_profit


@dataclass
class ComparisonResult:
    """Complete comparison result across all scenarios."""
    
    config: Config
    
    # Results
    sole_trader: Optional[SoleTraderResult] = None
    company_salary: Optional[CompanySalaryResult] = None
    company_dividends: Optional[CompanyDividendResult] = None
    company_mixed: Optional[CompanyMixedResult] = None
    
    # Optimization results (if optimize=True)
    optimal_salary: Optional[Decimal] = None
    optimal_dividends: Optional[Decimal] = None
    
    @property
    def best_scenario(self) -> str:
        """Name of the scenario with lowest total tax."""
        scenarios = []
        
        if self.sole_trader:
            scenarios.append(("Sole Trader", self.sole_trader.total_tax))
        if self.company_salary:
            scenarios.append(("Company (Salary)", self.company_salary.total_tax))
        if self.company_dividends:
            scenarios.append(("Company (Dividends)", self.company_dividends.total_tax))
        if self.company_mixed:
            scenarios.append(("Company (Mixed)", self.company_mixed.total_tax))
        
        if not scenarios:
            return "N/A"
        
        return min(scenarios, key=lambda x: x[1])[0]
