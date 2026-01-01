# Tax Comparison Tool - Usage Guide

This guide explains how to use the tax comparison tools to analyze sole trader vs company structures for your situation.

## Quick Start

```bash
# Basic comparison: $105k salary, $50k business profit
uv run tax-compare --salary 105000 --business-profit 50000

# Include all costs for realistic comparison
uv run tax-compare --salary 105000 --business-profit 50000 \
    --include-compliance-costs --include-setup-costs --detailed

# Run ARR analysis across multiple profit levels
uv run python scripts/analyze_arr.py --salary 105000 --compliance-costs --setup-costs --compare
```

---

## Command Reference

### Main CLI: `tax-compare`

```bash
uv run tax-compare [OPTIONS]
```

#### Required Options
| Option | Description |
|--------|-------------|
| `--business-profit` | Annual profit from your business (ARR) |

#### Common Options
| Option | Default | Description |
|--------|---------|-------------|
| `--salary` | 0 | Your employment salary from main job |
| `--include-compliance-costs` | off | Include annual compliance costs |
| `--include-setup-costs` | off | Include one-time setup costs (amortized over 5 years) |
| `--detailed` | off | Show full breakdown for each scenario |
| `--optimize` | off | Find optimal salary/dividend split |

#### Cost Customization
| Option | Default | Description |
|--------|---------|-------------|
| `--compliance-cost-sole-trader` | $500 | Annual sole trader costs |
| `--compliance-cost-company` | $3,500 | Annual company costs |
| `--setup-cost-sole-trader` | $100 | One-time sole trader setup |
| `--setup-cost-company` | $1,500 | One-time company setup |
| `--years-to-amortize` | 5 | Years to spread setup costs |

### Analysis Script: `analyze_arr.py`

```bash
uv run python scripts/analyze_arr.py [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--salary` | 80000 | Employment salary |
| `--arr-min` | 20000 | Minimum ARR to analyze |
| `--arr-max` | 200000 | Maximum ARR to analyze |
| `--step` | 5000 | Step between ARR values |
| `--compliance-costs` | off | Include compliance costs |
| `--setup-costs` | off | Include setup costs |
| `--compare` | off | Show side-by-side comparison table |
| `--no-charts` | off | Skip chart generation |

---

## Scenario Examples

### Scenario 1: No Employment - Business Only

**Situation**: You're starting a business with no other income.

```bash
uv run tax-compare --business-profit 80000 --detailed
```

**Output Explained**:
```
        Sole Trader Breakdown         
┌──────────────────────┬─────────────┐
│ Business Profit      │  $80,000.00 │
│ Total Taxable Income │  $80,000.00 │
│                      │             │
│ Income Tax           │  $14,788.00 │  ← Tax on $80k (uses low brackets)
│ Medicare Levy (2%)   │   $1,600.00 │
│ SBITO Offset         │    -$740.00 │  ← Small business tax offset
│                      │             │
│ Total Tax            │  $15,648.00 │
│ Take-Home            │  $64,352.00 │  ← What you keep
└──────────────────────┴─────────────┘
```

**Key Points**:
- With no employment income, you start from the $0 tax bracket
- SBITO (Small Business Income Tax Offset) reduces tax by up to $1,000
- Sole trader is often better at lower incomes due to tax-free threshold

---

### Scenario 2: Full-Time Employee with Side Business

**Situation**: $105k salary, $50k side business profit.

```bash
uv run tax-compare --salary 105000 --business-profit 50000 \
    --include-compliance-costs --include-setup-costs --detailed
```

**Output Explained**:
```
        Sole Trader Breakdown         
┌──────────────────────┬─────────────┐
│ Employment Salary    │ $105,000.00 │
│ Business Profit      │  $50,000.00 │
│ Total Taxable Income │ $155,000.00 │  ← Combined = higher brackets!
│                      │             │
│ Income Tax           │  $38,688.00 │  ← 37% marginal rate kicks in
│ Medicare Levy (2%)   │   $3,100.00 │
│ SBITO Offset         │  -$1,000.00 │
│ Compliance Costs     │     $520.00 │  ← $500 + $100/5yr setup
│                      │             │
│ Total Tax            │  $40,788.00 │
│ Take-Home            │ $113,692.00 │
└──────────────────────┴─────────────┘

    Company (Salary Only) Breakdown     
┌─────────────────────────┬────────────┐
│ Company Profit          │ $50,000.00 │
│ Salary Paid             │ $44,843.05 │  ← After super deduction
│ Super Guarantee (11.5%) │  $5,156.95 │  ← Bonus retirement savings!
│ Company Taxable Income  │      $0.00 │  ← No company tax (all paid as salary)
│ Company Tax             │      $0.00 │
│                         │            │
│ Personal Income Tax     │ $36,779.93 │  ← Tax on $105k + $44.8k salary
│ Medicare Levy           │  $2,996.86 │
│ Compliance Costs        │  $3,800.00 │  ← $3,500 + $1,500/5yr setup
│                         │            │
│ Total Tax               │ $15,388.79 │  ← Tax attributable to company only
│ Take-Home Cash          │ $25,654.26 │  ← Cash from company
│ + Super Benefit         │  $5,156.95 │  ← Plus super contribution
└─────────────────────────┴────────────┘
```

**Comparison**:
| Structure | Tax + Costs | From Business You Keep |
|-----------|------------:|----------------------:|
| Sole Trader | $41,308 | $8,692 (profit - extra tax - costs) |
| Company | $19,189 | $30,811 (cash + super) |
| **Savings** | **$22,119** | |

**Why Company Wins**:
1. Your $105k salary already uses up the low tax brackets
2. Business profit as sole trader is taxed at 30-37% marginal rates
3. Company can deduct salary as expense, reducing company tax to $0
4. You get 11.5% super contribution as bonus

---

### Scenario 3: Low ARR - Is Company Worth It?

**Situation**: Only $20k business profit. Are the company costs worth it?

```bash
uv run python scripts/analyze_arr.py --salary 105000 \
    --compliance-costs --setup-costs --compare \
    --arr-min 0 --arr-max 30000 --step 5000
```

**Output**:
```
=========================================================
Sole Trader vs Company Comparison | Employment Salary: $105,000
=========================================================
         ARR |    Tax+Costs    Take-Home | Tax+Costs     Cash    Super | Tax Saved
----------------------------------------------------------------------------------
$         0 |     $24,908     $80,092 |    $3,800   -$3,800      $0 | $21,108
$     5,000 |     $26,335     $83,665 |    $5,235     -$751    $516 | $21,100
$    10,000 |     $27,756     $87,244 |    $6,670    $2,299  $1,031 | $21,086
$    15,000 |     $29,172     $90,828 |    $8,105    $5,348  $1,547 | $21,067
$    20,000 |     $30,584     $94,416 |    $9,540    $8,397  $2,063 | $21,044
$    25,000 |     $31,991     $98,009 |   $10,975   $11,447  $2,578 | $21,017
$    30,000 |     $33,508    $101,492 |   $12,410   $14,496  $3,094 | $21,098
```

**Reading This Table**:

- **$0 ARR**: Company shows -$3,800 cash = you're paying $3,800/year for nothing!
  - ❌ Don't set up a company if you have no business income
  
- **$5,000 ARR**: Company cash is -$751, but with $516 super = -$235 net
  - ⚠️ Borderline - super helps but you're still slightly negative
  
- **$10,000 ARR**: Company gives $2,299 cash + $1,031 super = $3,330 benefit
  - ✅ Company is now clearly beneficial
  
- **$20,000+ ARR**: Company saves $21k+ per year
  - ✅ Company is the clear winner

**Rule of Thumb**: At $105k salary, a company becomes worth it around **$5,000-$10,000 ARR**. Below that, the compliance costs eat up the tax savings.

---

### Scenario 4: Finding the Optimal Payout Method

**Situation**: $150k business profit - should you use salary, dividends, or mix?

```bash
uv run tax-compare --salary 105000 --business-profit 150000 --optimize --detailed
```

**Output Explained**:
```
Company (Salary Only): Total Tax $54,329
Company (Dividends Only): Total Tax $61,600  
Company (Mixed): Total Tax $54,329

Recommendation: Company (Salary)
```

**Why Salary Beats Dividends at High Income**:

| Method | How It Works | Your Situation |
|--------|--------------|----------------|
| **Salary** | Company deducts salary → no company tax → you pay personal tax | With $105k salary, you're at 30%+ marginal rate. Salary is fully deductible. |
| **Dividends** | Company pays 25% tax → you get franked dividend → pay personal tax minus franking credit | At 30%+ marginal rate, you pay more than the franking credit gives back |
| **Mixed** | Optimal blend of both | At your income level, 100% salary is optimal |

**When Dividends Are Better**:
- If your total income (employment + business) stays under ~$45,000
- The 25% company tax is then higher than your marginal rate
- Franking credits give you a refund

---

### Scenario 5: Full ARR Analysis with Charts

**Situation**: You want to see how different ARR levels affect the comparison.

```bash
# Table output
uv run python scripts/analyze_arr.py --salary 105000 \
    --compliance-costs --setup-costs --no-charts

# With charts (requires matplotlib)
uv run python scripts/analyze_arr.py --salary 105000 \
    --compliance-costs --setup-costs --save-charts --output-dir ./output
```

**Key Output - Best Option by ARR**:
```
         ARR | Best Option
-------------+------------------
$    20,000 | Company (Salary)
$    50,000 | Company (Salary)
$   100,000 | Company (Salary)
$   150,000 | Company (Salary)
$   200,000 | Company (Salary)
```

At $105k employment salary, **Company (Salary) wins at ALL ARR levels**.

---

## Understanding the Numbers

### What Each Column Means

| Column | Meaning |
|--------|---------|
| **Tax+Costs** | Total outgoing: income tax + Medicare levy + compliance costs + amortized setup |
| **Take-Home** | What ends up in your pocket after all deductions |
| **Eff.Rate** | Effective tax rate = Tax ÷ Total Income |
| **Cash** | Actual cash paid to you from the company |
| **Super** | Superannuation contribution (extra retirement savings) |
| **Tax Saved** | How much less you pay with Company vs Sole Trader |
| **Extra $** | Additional money (cash + super) you receive with Company |

### Cost Breakdown

**Sole Trader Costs (~$520/year)**:
- Tax return preparation: $200-400
- Business name registration: $42/year
- Basic bookkeeping: $0-100

**Company Costs (~$3,800/year)**:
- ASIC annual review: $335
- Company tax return: $1,000-2,000
- BAS/IAS lodgements: $500-1,000
- Payroll processing: $500-1,000
- Bookkeeping: $500-1,000

**Setup Costs (one-time, amortized over 5 years)**:
- Sole Trader: ~$100 (ABN, business name)
- Company: ~$1,500 (ASIC registration $576 + accountant setup)

---

## Common Questions

### Q: At what income does a company make sense?

**If you have no other job**: Company becomes beneficial around $80,000-$100,000 business profit, when higher marginal rates kick in.

**If you have a $105k job**: Company is beneficial at almost any ARR above ~$10,000 because your business income is already being taxed at 30%+ marginal rates.

### Q: What about dividends vs salary?

At high marginal rates (30%+), salary is almost always better because:
- 100% deductible for the company (no company tax)
- You also get superannuation (11.5% bonus)
- Dividends require paying 25% company tax first

### Q: What's not included in this analysis?

⚠️ **Important limitations**:
- **PSI Rules**: If your income is from personal services, ATO may deem it PSI and the company benefits disappear
- **Medicare Levy Surcharge**: May apply if no private health insurance and income >$93k
- **HELP/HECS**: Repayments aren't modelled
- **Division 7A**: Loans from your company have tax implications
- **Payroll Tax**: State-based, applies if wages exceed threshold

### Q: Should I actually set up a company?

This tool shows the **tax math only**. Before setting up a company, also consider:
1. **PSI assessment** - will your income be classified as PSI?
2. **Paperwork burden** - companies have more compliance requirements
3. **Asset protection** - companies provide liability separation
4. **Exit strategy** - selling a company vs sole trader assets differs
5. **Professional advice** - always consult an accountant for your specific situation

---

## Example Commands Cheat Sheet

```bash
# Quick comparison
uv run tax-compare --salary 105000 --business-profit 50000

# Full analysis with all costs
uv run tax-compare --salary 105000 --business-profit 50000 \
    --include-compliance-costs --include-setup-costs --detailed

# ARR analysis table
uv run python scripts/analyze_arr.py --salary 105000 \
    --compliance-costs --setup-costs --compare

# Low ARR analysis (is company worth it?)
uv run python scripts/analyze_arr.py --salary 105000 \
    --compliance-costs --setup-costs --compare \
    --arr-min 0 --arr-max 30000 --step 5000

# Export to JSON
uv run tax-compare --salary 105000 --business-profit 50000 \
    --output-format json > comparison.json

# Find optimal salary/dividend split
uv run tax-compare --salary 105000 --business-profit 150000 --optimize
```

---

## Disclaimer

**This tool provides estimates for educational purposes only.** It does not constitute financial or tax advice. The Australian tax system is complex and individual circumstances vary significantly.

**Always consult a registered tax agent or accountant** before making business structure decisions.
