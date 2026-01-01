# Australian Business Tax Comparison Tool — Design Document

## Overview

A Python CLI tool that compares total tax obligations between **sole trader** and **company (Pty Ltd)** business structures in Australia. The tool helps business owners make informed decisions about their business structure by modelling different scenarios and payout strategies.

**Target Users**: Australian residents considering starting a business or restructuring an existing sole trader operation into a company.

**Financial Year**: 2024-25 (tax return lodged in 2025)

---

## Core Concepts

### Sole Trader Taxation

As a sole trader, you and your business are the same legal entity. All business profits are added to your personal income and taxed at individual marginal rates.

**Inputs**:
- `employment_salary`: Your annual salary from employment (if any)
- `business_profit`: Net profit from your sole trader business

**Tax Calculation**:
1. Total taxable income = employment_salary + business_profit
2. Apply individual tax brackets (progressive rates)
3. Add Medicare levy (2% of taxable income)
4. Subtract Small Business Income Tax Offset (SBITO) — up to $1,000, calculated as percentage of business income

### Company Taxation

A company (Pty Ltd) is a separate legal entity. The company pays tax on its profits, and you must use formal mechanisms to extract money for personal use.

**Inputs**:
- `business_profit`: Net profit earned by the company
- `extraction_method`: How you take money out (salary, dividends, or mixed)

**Key Difference**: Your employment salary from another job does NOT flow through the company — it remains personal income taxed separately. However, if comparing structures, the company scenario assumes the business profit is your only/primary income source from that entity.

---

## Tax Rates (2024-25 Financial Year)

### Individual Tax Brackets (Residents)

| Taxable Income       | Tax Rate                                    |
|----------------------|---------------------------------------------|
| $0 – $18,200         | Nil                                         |
| $18,201 – $45,000    | 16% of amount over $18,200                  |
| $45,001 – $135,000   | $4,288 + 30% of amount over $45,000         |
| $135,001 – $190,000  | $31,288 + 37% of amount over $135,000       |
| $190,001+            | $51,638 + 45% of amount over $190,000       |

### Medicare Levy

- **Rate**: 2% of taxable income
- **Low-income threshold**: Reduced rate applies below $26,000 (not modelled in v1)

### Small Business Income Tax Offset (SBITO)

- **Maximum offset**: $1,000 per year
- **Rate**: 16% of income tax attributable to small business income
- **Eligibility**: Sole traders with aggregated turnover < $5 million

### Company Tax Rate

| Entity Type                          | Rate |
|--------------------------------------|------|
| Base rate entity (turnover < $50M)   | 25%  |
| All other companies                  | 30%  |

This tool assumes **base rate entity** status (25% rate).

### Superannuation Guarantee

- **Rate (2024-25)**: 11.5% of ordinary time earnings
- **Maximum contribution base**: $62,500 per quarter ($250,000 annually)

---

## Company Payout Methods

### 1. Salary Only

The company pays you a wage/salary for work performed. This is the most straightforward method.

**Mechanics**:
- Salary is a tax-deductible expense for the company (reduces company tax)
- You pay personal income tax on the salary via PAYG withholding
- Company must pay superannuation guarantee (11.5%) on top of salary
- You receive super contributions as a retirement benefit

**Calculation**:
```
Company profit = $X
Salary paid to you = $X (can equal full profit minus super cost)
Super guarantee = Salary × 11.5%
Company taxable income = Profit - Salary - Super = $0 (if fully distributed)
Your personal tax = Individual tax on Salary
```

**Total cost**: Personal income tax + super (which is deferred benefit, not lost)

### 2. Dividends Only

The company retains profit, pays company tax, then distributes remaining as dividends.

**Mechanics**:
- Company pays 25% tax on profits
- Remaining 75% distributed as fully franked dividends
- You "gross up" the dividend by adding the franking credit
- Pay personal tax on grossed-up amount, then subtract franking credit

**Calculation**:
```
Company profit = $100,000
Company tax (25%) = $25,000
Dividend paid = $75,000
Franking credit = $25,000
Grossed-up dividend = $100,000
Personal tax on $100,000 = (use brackets)
Tax payable = Personal tax - Franking credit
```

**Note**: If your marginal rate is below 25%, you receive a franking credit refund.

### 3. Salary + Dividends Mix

Optimal strategy: Pay yourself a salary up to a certain threshold, then take remaining profit as dividends.

**Rationale**:
- Salary up to ~$45,000 is taxed at 16% (below company rate of 25%)
- Salary gives super contributions (retirement benefit)
- Dividends above this threshold may be more efficient depending on marginal rate

**Optimization Goal**: Minimize total tax (company + personal) while maximizing take-home cash or total benefit (including super).

---

## CLI Parameters

### Required Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `--business-profit` | Float | Net profit from the business (required) |

### Optional Inputs

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--salary` | Float | 0 | Employment salary from another job (sole trader scenario only) |
| `--extraction-method` | Choice | `all` | How to extract money from company: `salary`, `dividends`, `mixed`, `all` |

### Configurable Options

#### `--include-super` / `--no-include-super`
**Default**: `--include-super`

Whether to include superannuation in calculations:
- **Enabled**: Shows super as part of total remuneration; company scenarios include 11.5% super guarantee cost
- **Disabled**: Ignores super; compares pure cash take-home only

**Rationale**: Super is a real cost to the company and a real benefit to you, but it's not immediate cash. Some users may want to see pure cash comparison.

#### `--super-as-benefit` / `--super-as-cost`
**Default**: `--super-as-benefit`

How to treat superannuation in the comparison:
- `--super-as-benefit`: Super is added to your total benefit (salary + super = total package)
- `--super-as-cost`: Super is shown as a cost that reduces available profit

**Rationale**: Different perspectives on super — retirement savings vs. business expense.

#### `--include-compliance-costs` / `--no-compliance-costs`
**Default**: `--no-compliance-costs`

Whether to include annual compliance costs in the comparison:

| Structure    | Estimated Annual Costs |
|--------------|------------------------|
| Sole Trader  | ~$500 (simple tax return, bookkeeping) |
| Company      | ~$2,500 (ASIC fee $319 + accountant $1,500–$3,000 + payroll) |

**Rationale**: Companies have higher ongoing compliance burden. This affects the true cost of each structure.

#### `--compliance-cost-sole-trader`
**Type**: Float  
**Default**: 500

Override the estimated annual compliance cost for sole trader structure.

#### `--compliance-cost-company`
**Type**: Float  
**Default**: 2500

Override the estimated annual compliance cost for company structure.

#### `--optimize`
**Default**: Disabled

When enabled with `--extraction-method mixed`, automatically calculate the optimal salary/dividend split that minimizes total tax.

**Algorithm**:
1. Iterate salary amounts from $0 to full profit (step $1,000)
2. For each split, calculate total tax (company + personal)
3. Return the split with minimum total tax

#### `--show-chart`
**Default**: Disabled

Generate a matplotlib chart comparing tax payable across income ranges ($0–$300k) for all scenarios.

#### `--output-format`
**Type**: Choice  
**Default**: `table`  
**Options**: `table`, `json`, `csv`

Output format for results:
- `table`: Rich formatted table in terminal
- `json`: JSON output for programmatic use
- `csv`: CSV output for spreadsheet import

#### `--tax-year`
**Type**: Choice  
**Default**: `2024-25`  
**Options**: `2024-25` (extensible for future years)

Select the tax year for rate calculations. Allows future updates without code changes.

---

## Output Structure

### Summary Table

```
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Scenario              ┃ Total Tax    ┃ Effective Rate       ┃ Take-Home Cash     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Sole Trader           │ $32,788      │ 32.8%                │ $67,212            │
│ Company (Salary)      │ $28,500      │ 28.5%                │ $71,500            │
│ Company (Dividends)   │ $31,000      │ 31.0%                │ $69,000            │
│ Company (Mixed)       │ $27,200      │ 27.2%                │ $72,800            │
└───────────────────────┴──────────────┴──────────────────────┴────────────────────┘
```

### Detailed Breakdown

For each scenario, show:
- Gross income / profit
- Taxable income calculation
- Income tax (by bracket)
- Medicare levy
- Offsets applied (SBITO, franking credits)
- Super contributions (if applicable)
- Compliance costs (if enabled)
- Final take-home amount

---

## Project Structure

```
business-tax-comparison/
├── pyproject.toml          # Project config and dependencies (uv)
├── README.md               # User documentation
├── DESIGN.md               # This document
├── src/
│   └── tax_comparison/
│       ├── __init__.py
│       ├── cli.py          # CLI entry point (click)
│       ├── models.py       # Data classes for scenarios
│       ├── rates.py        # Tax rates and thresholds
│       ├── calculators/
│       │   ├── __init__.py
│       │   ├── individual.py   # Individual tax calculation
│       │   ├── sole_trader.py  # Sole trader scenario
│       │   └── company.py      # Company scenarios (salary, dividends, mixed)
│       ├── optimizer.py    # Optimal salary/dividend split
│       └── output/
│           ├── __init__.py
│           ├── table.py    # Rich table output
│           ├── chart.py    # Matplotlib chart generation
│           └── export.py   # JSON/CSV export
└── tests/
    ├── test_individual_tax.py
    ├── test_sole_trader.py
    ├── test_company.py
    └── test_optimizer.py
```

---

## Dependencies

```toml
[project]
dependencies = [
    "click>=8.1",      # CLI framework
    "rich>=13.0",      # Terminal formatting
]

[project.optional-dependencies]
charts = [
    "matplotlib>=3.8", # Chart generation
]
dev = [
    "pytest>=8.0",     # Testing
    "pytest-cov>=4.0", # Coverage
]
```

---

## Example Usage

### Basic Comparison

```bash
# Compare $100,000 business profit across all structures
uv run tax-compare --business-profit 100000

# Sole trader with $80,000 employment salary + $50,000 side business
uv run tax-compare --salary 80000 --business-profit 50000
```

### Specific Extraction Method

```bash
# Company paying only salary
uv run tax-compare --business-profit 150000 --extraction-method salary

# Company paying only dividends
uv run tax-compare --business-profit 150000 --extraction-method dividends

# Optimized salary/dividend mix
uv run tax-compare --business-profit 150000 --extraction-method mixed --optimize
```

### With Options

```bash
# Include compliance costs in comparison
uv run tax-compare --business-profit 100000 --include-compliance-costs

# Custom compliance costs
uv run tax-compare --business-profit 100000 \
    --include-compliance-costs \
    --compliance-cost-company 4000

# Exclude super from calculations (pure cash comparison)
uv run tax-compare --business-profit 100000 --no-include-super

# Generate comparison chart
uv run tax-compare --business-profit 100000 --show-chart

# Export to JSON
uv run tax-compare --business-profit 100000 --output-format json > results.json
```

---

## Validation & Edge Cases

### Input Validation

- `business_profit` must be ≥ 0
- `salary` must be ≥ 0
- Total income (salary + business_profit) should be reasonable (warn if > $1,000,000)

### Edge Cases

1. **Zero profit**: Valid scenario — sole trader may have losses from other income
2. **Very low income**: Medicare levy reduction not modelled (simplification)
3. **Very high income**: Division 293 tax on super not modelled (simplification)
4. **Negative profit (loss)**: Not supported in v1 — display error message

### Limitations & Disclaimers

The tool should display:

> ⚠️ **Disclaimer**: This tool provides estimates for educational purposes only. 
> It does not constitute financial or tax advice. Consult a registered tax agent 
> or accountant before making business structure decisions.
>
> **Not modelled**: Medicare levy surcharge, HELP/HECS repayments, private health 
> insurance rebate, low-income offsets, carried-forward losses, Division 293 tax,
> Personal Services Income (PSI) rules.

---

## Future Enhancements (Out of Scope for v1)

1. **Trust structure**: Add family trust distribution scenarios
2. **Multiple years**: Compare tax over 5-10 year projection
3. **PSI rules**: Warn when Personal Services Income rules may apply
4. **State payroll tax**: Include if salary exceeds state thresholds
5. **GST**: Model GST registration threshold and cash flow impact
6. **Interactive mode**: Web UI or TUI for parameter adjustment
7. **Tax rate updates**: Fetch rates from ATO API (if available)

---

## References

- [ATO Individual Tax Rates 2024-25](https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents)
- [ATO Company Tax Rates](https://www.ato.gov.au/tax-rates-and-codes/company-tax-rate-changes)
- [Small Business Income Tax Offset](https://www.ato.gov.au/individuals-and-families/income-deductions-offsets-and-records/tax-offsets/small-business-income-tax-offset)
- [Superannuation Guarantee Rate](https://www.ato.gov.au/tax-rates-and-codes/super-guarantee-percentage)
- [Sole Trader Tax Guide (Nanak Accountants)](https://nanakaccountants.com.au/sole-trader-tax-rate-australia-2025/)
- [Paying Yourself as Business Owner (Sprintlaw)](https://sprintlaw.com.au/articles/how-to-legally-pay-yourself-as-a-business-owner-in-australia/)
