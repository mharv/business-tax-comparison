# Tax Structure Comparison Findings

> **Analysis Date:** December 2024  
> **Tax Year:** 2024-25 (Australian)  
> **Employment Salary:** $105,000

## Summary

**Company structure (paying yourself as salary) is the most tax-efficient option at all ARR levels** when you have a $105,000 employment salary, even after accounting for higher compliance and setup costs.

---

## Cost Comparison: Sole Trader vs Company

### One-Time Setup Costs

| Item | Sole Trader | Company (Pty Ltd) |
|------|------------:|------------------:|
| ABN Registration | Free | Free |
| Business Name (optional) | $42 | $42 |
| ASIC Company Registration | N/A | **$576** |
| Accountant/Legal Setup | $0-100 | $500-2,000 |
| **Total Setup** | **~$100** | **~$1,500** |

### Annual Ongoing Costs

| Item | Sole Trader | Company (Pty Ltd) |
|------|------------:|------------------:|
| ASIC Annual Review Fee | N/A | **$335** |
| Tax Return (Accountant) | $200-500 | $1,000-2,500 |
| BAS/IAS Lodgements | $0-200 | $500-1,000 |
| Bookkeeping | $0-300 | $1,000-3,000 |
| Payroll Processing | N/A | $500-1,500 |
| **Total Annual** | **~$500** | **~$3,500** |

### Cost Summary

| | Sole Trader | Company | Difference |
|--|------------:|--------:|------------|
| Setup (one-time) | $100 | $1,500 | +$1,400 |
| Annual Ongoing | $500 | $3,500 | +$3,000/year |
| **5-Year Total** | $2,600 | $19,000 | +$16,400 |

---

## Tax Comparison by ARR (Including All Costs)

The following analysis includes:
- ✅ All ongoing compliance costs ($500/yr sole trader, $3,500/yr company)
- ✅ Setup costs amortized over 5 years ($20/yr sole trader, $300/yr company)

| Business ARR | Sole Trader Total* | Company Total* | Net Benefit |
|-------------:|-------------------:|---------------:|------------:|
| $20,000 | $30,584 | $9,540 | **Save $21,044** |
| $50,000 | $41,308 | $19,189 | **Save $22,119** |
| $100,000 | $62,008 | $37,052 | **Save $24,956** |
| $150,000 | $85,508 | $58,129 | **Save $27,379** |
| $200,000 | $109,008 | $79,205 | **Save $29,803** |

*Total = Tax + Compliance Costs + Amortized Setup*

### Break-Even Analysis

With ~$3,000/year higher costs for a company, you need tax savings of at least $3,000 for the company structure to be worthwhile.

At $105k employment salary, the **minimum ARR where company wins**: **$0** (company wins at all levels!)

This is because even at low ARRs, the tax savings significantly exceed the additional compliance costs.

---

## Why Company Wins at $105k Salary

### The Problem with Sole Trader

When you're a sole trader, your business profit is **added directly to your employment income** and taxed at your marginal rate:

- $105k salary already puts you in the **30% tax bracket**
- Business profit pushes you into **37% bracket** (above $135k) and eventually **45% bracket** (above $190k)
- No ability to retain profits in the business at a lower rate

### The Company Advantage

With a Pty Ltd company paying you salary:

1. **Salary is tax-deductible** for the company
2. Company pays **25% tax** on any retained profits
3. You're taxed on salary at your marginal rate, but the company structure provides flexibility
4. **Super contributions** (11.5%) further reduce your taxable income

---

## Payout Method Comparison

| Method | How It Works | Best When |
|--------|--------------|-----------|
| **Salary** ✓ | Company pays you PAYG salary + super | Your marginal rate ≤ 30% or you want super |
| **Dividends** | Company pays 25% tax, you get franked dividends | Your marginal rate < 25% (not your case) |
| **Mixed** | Combination of salary + dividends | Optimizing across tax brackets |

At $105k employment salary, **100% salary extraction** is optimal because:
- Your marginal rate (30%+) makes dividends less attractive
- Salary is fully deductible, reducing company tax to zero
- You also receive superannuation contributions

---

## Quick Reference: Your Tax Brackets

| Income Range | Marginal Rate |
|--------------|---------------|
| $0 – $18,200 | 0% |
| $18,201 – $45,000 | 16% |
| $45,001 – $135,000 | 30% |
| $135,001 – $190,000 | 37% |
| $190,001+ | 45% |

*Plus 2% Medicare levy on all taxable income*

With $105k employment salary, you're already in the 30% bracket. Any additional income starts at 30% and goes up from there.

---

## Key Takeaways

1. **Company wins at ALL ARR levels** for your $105k salary situation
2. **Tax savings ($22k-$30k) far exceed** the extra compliance costs (~$3k/year)
3. **Pay yourself salary** rather than dividends at this income level
4. **Even with setup costs**, break-even occurs in the first few months
5. **Factor in ~$3,500/year** ongoing costs when budgeting for company structure

---

## What's NOT Modelled

⚠️ **This analysis does NOT include:**
- Medicare levy surcharge (if no private health insurance and income >$93k)
- HELP/HECS repayments
- Personal Services Income (PSI) rules — **critical if your income is primarily from your personal skills/labour**
- Division 7A implications (loans from company)
- Capital gains implications
- Carried-forward losses
- State-based payroll tax (if applicable)
- Workers compensation insurance

### PSI Warning

If your business income is primarily from **your personal efforts or skills** (consulting, contracting, etc.), the ATO's **Personal Services Income (PSI) rules** may apply. This can limit the tax benefits of a company structure. Consult a tax professional to assess your situation.

---

## Running Your Own Analysis

```bash
# Compare structures for your specific situation
uv run tax-compare --salary YOUR_SALARY --business-profit YOUR_ARR

# Include compliance and setup costs
uv run tax-compare --salary 105000 --business-profit 50000 \
    --include-compliance-costs --include-setup-costs --detailed

# Run full ARR analysis with costs
uv run python scripts/analyze_arr.py --salary 105000 \
    --compliance-costs --setup-costs

# Customize cost estimates
uv run tax-compare --salary 105000 --business-profit 50000 \
    --include-compliance-costs \
    --compliance-cost-sole-trader 600 \
    --compliance-cost-company 4000
```

---

## Disclaimer

**This tool provides estimates for educational purposes only.** It does not constitute financial or tax advice. Always consult a registered tax agent or accountant before making business structure decisions.

---

*Generated by tax-comparison tool • Source: business.gov.au, ato.gov.au*
