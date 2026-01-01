# Australian Business Tax Comparison Tool

Compare tax obligations between **sole trader** and **company (Pty Ltd)** business structures in Australia.

## Features

- 📊 Compare tax across sole trader and company structures
- 💰 Model different company payout methods (salary, dividends, mixed)
- 🔍 Find optimal salary/dividend split to minimize tax
- 📈 Include superannuation and compliance costs
- 📋 Export to table, JSON, or CSV formats

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/business-tax-comparison.git
cd business-tax-comparison

# Install with uv
uv sync
```

## Usage

### Basic Comparison

```bash
# Compare $100,000 business profit across all structures
uv run tax-compare --business-profit 100000

# Sole trader with $80,000 employment salary + $50,000 side business
uv run tax-compare --salary 80000 --business-profit 50000
```

### Company Extraction Methods

```bash
# Company paying only salary
uv run tax-compare --business-profit 150000 --extraction-method salary

# Company paying only dividends
uv run tax-compare --business-profit 150000 --extraction-method dividends

# Optimized salary/dividend mix
uv run tax-compare --business-profit 150000 --extraction-method mixed --optimize
```

### Additional Options

```bash
# Include compliance costs in comparison
uv run tax-compare --business-profit 100000 --include-compliance-costs

# Show detailed breakdown
uv run tax-compare --business-profit 100000 --detailed

# Export to JSON
uv run tax-compare --business-profit 100000 --output-format json

# Export to CSV
uv run tax-compare --business-profit 100000 --output-format csv
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--business-profit, -p` | Net profit from the business (required) |
| `--salary, -s` | Employment salary from another job |
| `--extraction-method, -e` | How to extract from company: `salary`, `dividends`, `mixed`, `all` |
| `--tax-year, -y` | Tax year for rates (default: `2024-25`) |
| `--include-super / --no-include-super` | Include superannuation (default: yes) |
| `--super-as-benefit / --super-as-cost` | Treat super as benefit or cost |
| `--include-compliance-costs` | Include annual compliance costs |
| `--compliance-cost-sole-trader` | Custom sole trader compliance cost |
| `--compliance-cost-company` | Custom company compliance cost |
| `--optimize` | Find optimal salary/dividend split |
| `--output-format, -o` | Output format: `table`, `json`, `csv` |
| `--detailed, -d` | Show detailed breakdown |
| `--no-disclaimer` | Hide disclaimer notice |

## Tax Year Support

Currently supports:
- **2024-25** (default)

## Disclaimer

⚠️ This tool provides estimates for educational purposes only. It does not constitute financial or tax advice. Consult a registered tax agent or accountant before making business structure decisions.

**Not modelled**: Medicare levy surcharge, HELP/HECS repayments, private health insurance rebate, low-income offsets, carried-forward losses, Division 293 tax, Personal Services Income (PSI) rules.

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=tax_comparison

# Run specific test
uv run pytest tests/test_individual_tax.py -v
```

## License

MIT
# business-tax-comparison
