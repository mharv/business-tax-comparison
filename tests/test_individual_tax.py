"""Tests for individual tax calculator."""

from decimal import Decimal

import pytest

from tax_comparison.calculators.individual import (
    calculate_income_tax,
    calculate_individual_tax,
    calculate_medicare_levy,
    calculate_sbito,
)
from tax_comparison.rates import get_rates


class TestCalculateIncomeTax:
    """Test income tax bracket calculations."""
    
    def test_zero_income(self):
        """Zero income should result in zero tax."""
        rates = get_rates("2024-25")
        assert calculate_income_tax(Decimal("0"), rates) == Decimal("0")
    
    def test_tax_free_threshold(self):
        """Income up to $18,200 should be tax-free."""
        rates = get_rates("2024-25")
        assert calculate_income_tax(Decimal("18200"), rates) == Decimal("0")
    
    def test_first_bracket(self):
        """Income $18,201 - $45,000 taxed at 16%."""
        rates = get_rates("2024-25")
        # $30,000 income: ($30,000 - $18,200) * 16% = $1,888
        result = calculate_income_tax(Decimal("30000"), rates)
        assert result == Decimal("1888.00")
    
    def test_second_bracket(self):
        """Income $45,001 - $135,000 taxed at 30%."""
        rates = get_rates("2024-25")
        # $80,000 income: $4,288 + ($80,000 - $45,000) * 30% = $4,288 + $10,500 = $14,788
        result = calculate_income_tax(Decimal("80000"), rates)
        assert result == Decimal("14788.00")
    
    def test_third_bracket(self):
        """Income $135,001 - $190,000 taxed at 37%."""
        rates = get_rates("2024-25")
        # $160,000 income: $31,288 + ($160,000 - $135,000) * 37% = $31,288 + $9,250 = $40,538
        result = calculate_income_tax(Decimal("160000"), rates)
        assert result == Decimal("40538.00")
    
    def test_top_bracket(self):
        """Income above $190,000 taxed at 45%."""
        rates = get_rates("2024-25")
        # $250,000 income: $51,638 + ($250,000 - $190,000) * 45% = $51,638 + $27,000 = $78,638
        result = calculate_income_tax(Decimal("250000"), rates)
        assert result == Decimal("78638.00")


class TestCalculateMedicareLevy:
    """Test Medicare levy calculations."""
    
    def test_zero_income(self):
        """Zero income should have zero Medicare levy."""
        rates = get_rates("2024-25")
        assert calculate_medicare_levy(Decimal("0"), rates) == Decimal("0")
    
    def test_standard_rate(self):
        """Medicare levy should be 2% of taxable income."""
        rates = get_rates("2024-25")
        # $100,000 * 2% = $2,000
        result = calculate_medicare_levy(Decimal("100000"), rates)
        assert result == Decimal("2000.00")


class TestCalculateSbito:
    """Test Small Business Income Tax Offset calculations."""
    
    def test_zero_business_income(self):
        """No business income should result in zero SBITO."""
        rates = get_rates("2024-25")
        result = calculate_sbito(
            income_tax=Decimal("10000"),
            business_income=Decimal("0"),
            total_income=Decimal("80000"),
            rates=rates,
        )
        assert result == Decimal("0")
    
    def test_full_business_income(self):
        """All income from business should get full SBITO rate."""
        rates = get_rates("2024-25")
        # $14,788 tax * 16% = $2,366.08, but capped at $1,000
        result = calculate_sbito(
            income_tax=Decimal("14788"),
            business_income=Decimal("80000"),
            total_income=Decimal("80000"),
            rates=rates,
        )
        assert result == Decimal("1000.00")  # Capped at maximum
    
    def test_partial_business_income(self):
        """Mixed income should get proportional SBITO."""
        rates = get_rates("2024-25")
        # Total income $100,000, business income $50,000 (50%)
        # Tax $22,788, business portion = $11,394
        # SBITO = $11,394 * 16% = $1,823.04, capped at $1,000
        result = calculate_sbito(
            income_tax=Decimal("22788"),
            business_income=Decimal("50000"),
            total_income=Decimal("100000"),
            rates=rates,
        )
        assert result == Decimal("1000.00")  # Still capped
    
    def test_low_business_income_not_capped(self):
        """Low business income SBITO should not be capped."""
        rates = get_rates("2024-25")
        # Total income $30,000, all business
        # Tax $1,888 * 16% = $302.08
        result = calculate_sbito(
            income_tax=Decimal("1888"),
            business_income=Decimal("30000"),
            total_income=Decimal("30000"),
            rates=rates,
        )
        assert result == Decimal("302.08")


class TestCalculateIndividualTax:
    """Test complete individual tax breakdown."""
    
    def test_example_from_website(self):
        """Test against worked example: $80,000 profit."""
        # From website:
        # Taxable Income: $80,000
        # Income Tax: $4,288 + (30% of $35,000) = $14,788
        # Medicare Levy (2%): $1,600
        # SBITO (est.): -$1,000 (maximum offset)
        # Total Tax Payable: $15,388
        
        result = calculate_individual_tax(
            taxable_income=Decimal("80000"),
            business_income=Decimal("80000"),
        )
        
        assert result.income_tax == Decimal("14788.00")
        assert result.medicare_levy == Decimal("1600.00")
        assert result.sbito == Decimal("1000.00")  # Capped at max
        assert result.total_tax == Decimal("15388.00")
    
    def test_example_160k(self):
        """Test against worked example: $160,000 profit."""
        # From website:
        # Taxable Income: $160,000
        # Income Tax: $31,288 + (37% of $25,000) = $40,538
        # Medicare Levy (2%): $3,200
        # SBITO (est.): -$1,000 (maximum offset)
        # Total Tax Payable: $42,738
        
        result = calculate_individual_tax(
            taxable_income=Decimal("160000"),
            business_income=Decimal("160000"),
        )
        
        assert result.income_tax == Decimal("40538.00")
        assert result.medicare_levy == Decimal("3200.00")
        assert result.sbito == Decimal("1000.00")
        assert result.total_tax == Decimal("42738.00")
    
    def test_effective_rate(self):
        """Test effective tax rate calculation."""
        result = calculate_individual_tax(
            taxable_income=Decimal("100000"),
            business_income=Decimal("100000"),
        )
        
        # Total tax / taxable income
        expected_rate = result.total_tax / Decimal("100000")
        assert result.effective_rate == expected_rate
