"""Tests for sole trader calculator."""

from decimal import Decimal

import pytest

from tax_comparison.calculators.sole_trader import calculate_sole_trader_tax
from tax_comparison.models import Config


class TestSoleTraderCalculator:
    """Test sole trader tax calculations."""
    
    def test_business_only_80k(self):
        """Test sole trader with $80,000 business profit only."""
        config = Config(
            business_profit=Decimal("80000"),
            employment_salary=Decimal("0"),
        )
        
        result = calculate_sole_trader_tax(config)
        
        assert result.business_profit == Decimal("80000")
        assert result.employment_salary == Decimal("0")
        assert result.total_income == Decimal("80000")
        assert result.total_tax == Decimal("15388.00")  # From worked example
        assert result.take_home == Decimal("64612.00")
    
    def test_combined_income(self):
        """Test sole trader with employment salary + business profit."""
        config = Config(
            business_profit=Decimal("50000"),
            employment_salary=Decimal("80000"),
        )
        
        result = calculate_sole_trader_tax(config)
        
        # Total income = $130,000
        assert result.total_income == Decimal("130000")
        
        # Tax breakdown:
        # Income tax: $4,288 + 30% * ($130,000 - $45,000) = $4,288 + $25,500 = $29,788
        # Medicare: $130,000 * 2% = $2,600
        # SBITO: 16% of (tax * business_proportion)
        #   Business proportion = $50,000 / $130,000 = 0.3846
        #   Tax on business = $29,788 * 0.3846 = $11,458.49
        #   SBITO = $11,458.49 * 16% = $1,833.36, capped at $1,000
        
        assert result.tax_breakdown.income_tax == Decimal("29788.00")
        assert result.tax_breakdown.medicare_levy == Decimal("2600.00")
        assert result.tax_breakdown.sbito == Decimal("1000.00")  # Capped
        
        # Total tax = $29,788 + $2,600 - $1,000 = $31,388
        assert result.total_tax == Decimal("31388.00")
    
    def test_with_compliance_costs(self):
        """Test that compliance costs are included when enabled."""
        config = Config(
            business_profit=Decimal("80000"),
            include_compliance_costs=True,
            compliance_cost_sole_trader=Decimal("600"),
        )
        
        result = calculate_sole_trader_tax(config)
        
        assert result.compliance_costs == Decimal("600")
        # Take home = income - tax - compliance
        assert result.take_home == Decimal("80000") - result.total_tax - Decimal("600")
    
    def test_zero_business_profit(self):
        """Test with zero business profit (just employment salary)."""
        config = Config(
            business_profit=Decimal("0"),
            employment_salary=Decimal("50000"),
        )
        
        result = calculate_sole_trader_tax(config)
        
        assert result.total_income == Decimal("50000")
        # No SBITO since no business income
        assert result.tax_breakdown.sbito == Decimal("0")
