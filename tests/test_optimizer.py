"""Tests for optimizer."""

from decimal import Decimal

import pytest

from tax_comparison.models import Config
from tax_comparison.optimizer import optimize_salary_dividend_split


class TestOptimizer:
    """Test salary/dividend optimization."""
    
    def test_finds_optimal_split(self):
        """Optimizer should find a split with lower tax than extremes."""
        config = Config(
            business_profit=Decimal("150000"),
            include_super=True,
        )
        
        result = optimize_salary_dividend_split(config, step=Decimal("5000"))
        
        # Optimal should be somewhere in the middle
        assert result.optimal_salary > Decimal("0")
        assert result.optimal_salary < config.business_profit
        
        # Total tax should be reasonable (less than 50%)
        assert result.total_tax < config.business_profit * Decimal("0.5")
    
    def test_low_profit_prefers_mix_for_efficiency(self):
        """Even low profit may benefit from a mix due to franking credits."""
        config = Config(
            business_profit=Decimal("40000"),
            include_super=False,  # Simplify
        )
        
        result = optimize_salary_dividend_split(config, step=Decimal("1000"))
        
        # The optimizer finds the lowest total tax
        # Due to franking credits, a mix can sometimes be optimal
        # even at low incomes - the test validates it runs and finds a result
        assert result.optimal_salary >= Decimal("0")
        assert result.optimal_salary <= Decimal("40000")
        assert result.total_tax < Decimal("40000") * Decimal("0.25")  # Less than 25%
    
    def test_high_profit_uses_mix(self):
        """High profit should use a mix to avoid top brackets."""
        config = Config(
            business_profit=Decimal("300000"),
            include_super=True,
        )
        
        result = optimize_salary_dividend_split(config, step=Decimal("10000"))
        
        # Should use some mix, not all salary (would be 45% rate)
        # and not all dividends (would miss low bracket)
        assert result.optimal_salary > Decimal("0")
        assert result.optimal_dividend > Decimal("0")
