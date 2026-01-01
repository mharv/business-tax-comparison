"""Tests for company tax calculators."""

from decimal import Decimal

import pytest

from tax_comparison.calculators.company import (
    calculate_company_dividends,
    calculate_company_mixed,
    calculate_company_salary,
    calculate_company_tax,
    calculate_super_guarantee,
)
from tax_comparison.models import Config
from tax_comparison.rates import get_rates


class TestCompanyTax:
    """Test company tax calculations."""
    
    def test_base_rate_entity(self):
        """Base rate entity should pay 25% tax."""
        rates = get_rates("2024-25")
        result = calculate_company_tax(
            taxable_income=Decimal("100000"),
            rates=rates,
            is_base_rate_entity=True,
        )
        
        assert result.company_tax_rate == Decimal("0.25")
        assert result.company_tax == Decimal("25000.00")
        assert result.after_tax_profit == Decimal("75000.00")
    
    def test_full_rate_entity(self):
        """Full rate entity should pay 30% tax."""
        rates = get_rates("2024-25")
        result = calculate_company_tax(
            taxable_income=Decimal("100000"),
            rates=rates,
            is_base_rate_entity=False,
        )
        
        assert result.company_tax_rate == Decimal("0.30")
        assert result.company_tax == Decimal("30000.00")


class TestSuperGuarantee:
    """Test superannuation guarantee calculations."""
    
    def test_standard_super(self):
        """Super should be 11.5% of salary."""
        rates = get_rates("2024-25")
        result = calculate_super_guarantee(Decimal("100000"), rates)
        assert result == Decimal("11500.00")
    
    def test_capped_at_max_base(self):
        """Super should be capped at maximum contribution base."""
        rates = get_rates("2024-25")
        # Max base = $62,500 * 4 = $250,000 annually
        # For $300,000 salary, super = $250,000 * 11.5% = $28,750
        result = calculate_super_guarantee(Decimal("300000"), rates)
        assert result == Decimal("28750.00")


class TestCompanySalary:
    """Test company salary extraction method."""
    
    def test_full_salary_extraction(self):
        """Company paying full profit as salary (with super)."""
        config = Config(
            business_profit=Decimal("100000"),
            include_super=True,
        )
        
        result = calculate_company_salary(config)
        
        # profit = salary + super = salary * (1 + 0.115)
        # salary = 100000 / 1.115 = $89,686.10
        expected_salary = (Decimal("100000") / Decimal("1.115")).quantize(Decimal("0.01"))
        
        assert result.salary_paid == expected_salary
        assert result.company_tax_breakdown.company_tax == Decimal("0")  # All distributed
    
    def test_no_super(self):
        """Company paying salary without super."""
        config = Config(
            business_profit=Decimal("100000"),
            include_super=False,
        )
        
        result = calculate_company_salary(config)
        
        assert result.salary_paid == Decimal("100000")
        assert result.super_contribution == Decimal("0")


class TestCompanyDividends:
    """Test company dividends extraction method."""
    
    def test_full_dividend_extraction(self):
        """Company paying all profit as dividends."""
        config = Config(
            business_profit=Decimal("100000"),
        )
        
        result = calculate_company_dividends(config)
        
        # Company tax = $100,000 * 25% = $25,000
        assert result.company_tax_breakdown.company_tax == Decimal("25000.00")
        
        # Dividend = $75,000
        assert result.dividend_breakdown.dividend_amount == Decimal("75000.00")
        
        # Franking credit = $25,000
        assert result.dividend_breakdown.franking_credit == Decimal("25000.00")
        
        # Grossed-up dividend = $100,000
        assert result.dividend_breakdown.grossed_up_dividend == Decimal("100000.00")
    
    def test_franking_credit_refund(self):
        """Low income should result in franking credit refund."""
        config = Config(
            business_profit=Decimal("40000"),  # Low profit
        )
        
        result = calculate_company_dividends(config)
        
        # Company tax = $40,000 * 25% = $10,000
        # Dividend = $30,000
        # Grossed-up = $40,000 (below tax-free threshold + first bracket)
        # Personal tax on $40,000 = ($40,000 - $18,200) * 16% = $3,488 + Medicare $800 = $4,288
        # Net personal tax = $4,288 - $10,000 franking credit = -$5,712 (refund)
        
        assert result.personal_tax_on_dividends < Decimal("0")  # Refund


class TestCompanyMixed:
    """Test company mixed extraction method."""
    
    def test_default_split(self):
        """Default should pay salary up to $45,000."""
        config = Config(
            business_profit=Decimal("150000"),
            include_super=True,
        )
        
        result = calculate_company_mixed(config)
        
        # Default salary = $45,000
        assert result.salary_paid == Decimal("45000")
        
        # Super on $45,000 = $5,175
        assert result.super_contribution == Decimal("5175.00")
        
        # Remaining profit = $150,000 - $45,000 - $5,175 = $99,825
        # Company tax = $99,825 * 25% = $24,956.25
        # Dividend = $74,868.75
    
    def test_custom_salary_amount(self):
        """Test with custom salary amount."""
        config = Config(
            business_profit=Decimal("150000"),
            include_super=True,
        )
        
        result = calculate_company_mixed(config, salary_amount=Decimal("80000"))
        
        assert result.salary_paid == Decimal("80000")
    
    def test_profit_less_than_default_salary(self):
        """When profit < $45,000, salary should be limited to profit."""
        config = Config(
            business_profit=Decimal("30000"),
            include_super=False,
        )
        
        result = calculate_company_mixed(config)
        
        # Salary limited to profit
        assert result.salary_paid == Decimal("30000")
        assert result.dividend_paid == Decimal("0")
