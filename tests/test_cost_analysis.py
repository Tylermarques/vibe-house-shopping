"""Tests for the cost analysis module."""

import pytest
from app.cost_analysis import (
    DEFAULTS,
    CostAnalysisParams,
    YearlyAnalysis,
    calculate_loan_balance,
    run_analysis,
    compare_homes,
    get_analysis_summary,
)


class TestCostAnalysisParams:
    """Tests for the CostAnalysisParams dataclass."""

    def test_default_values(self):
        """Test that default values are applied correctly."""
        params = CostAnalysisParams(home_price=500000)

        assert params.home_price == 500000
        assert params.down_payment_pct == DEFAULTS["down_payment_pct"]
        assert params.purchase_fees == DEFAULTS["purchase_fees"]
        assert params.property_tax_rate == DEFAULTS["property_tax_rate"]
        assert params.monthly_repair_pct == DEFAULTS["monthly_repair_pct"]
        assert params.hoa_monthly == DEFAULTS["hoa_monthly"]
        assert params.annual_growth_rate == DEFAULTS["annual_growth_rate"]
        assert params.interest_rate == DEFAULTS["interest_rate"]
        assert params.loan_term_years == DEFAULTS["loan_term_years"]
        assert params.maintenance_inflation == DEFAULTS["maintenance_inflation"]

    def test_custom_values(self):
        """Test that custom values override defaults."""
        params = CostAnalysisParams(
            home_price=750000,
            down_payment_pct=0.25,
            purchase_fees=50000,
            property_tax_rate=0.015,
            monthly_repair_pct=0.0005,
            hoa_monthly=500,
            annual_growth_rate=0.04,
            interest_rate=0.06,
            loan_term_years=15,
            maintenance_inflation=0.03,
        )

        assert params.home_price == 750000
        assert params.down_payment_pct == 0.25
        assert params.purchase_fees == 50000
        assert params.property_tax_rate == 0.015
        assert params.monthly_repair_pct == 0.0005
        assert params.hoa_monthly == 500
        assert params.annual_growth_rate == 0.04
        assert params.interest_rate == 0.06
        assert params.loan_term_years == 15
        assert params.maintenance_inflation == 0.03

    def test_down_payment_property(self):
        """Test the down_payment computed property."""
        params = CostAnalysisParams(home_price=500000, down_payment_pct=0.20)
        assert params.down_payment == 100000

        params = CostAnalysisParams(home_price=1000000, down_payment_pct=0.10)
        assert params.down_payment == 100000

        params = CostAnalysisParams(home_price=400000, down_payment_pct=0.05)
        assert params.down_payment == 20000

    def test_initial_loan_property(self):
        """Test the initial_loan computed property."""
        params = CostAnalysisParams(home_price=500000, down_payment_pct=0.20)
        assert params.initial_loan == 400000

        params = CostAnalysisParams(home_price=1000000, down_payment_pct=0.10)
        assert params.initial_loan == 900000

        params = CostAnalysisParams(home_price=400000, down_payment_pct=1.0)
        assert params.initial_loan == 0  # 100% down payment

    def test_monthly_payment_property(self):
        """Test the monthly_payment computed property."""
        # Known mortgage calculation: $400k loan, 4.79% rate, 30 years
        params = CostAnalysisParams(
            home_price=500000,
            down_payment_pct=0.20,
            interest_rate=0.0479,
            loan_term_years=30,
        )
        # Expected: approximately $2,097 per month
        assert 2090 < params.monthly_payment < 2110

    def test_monthly_payment_zero_loan(self):
        """Test monthly_payment when loan is zero (100% down payment)."""
        params = CostAnalysisParams(
            home_price=500000,
            down_payment_pct=1.0,  # 100% down
            interest_rate=0.0479,
            loan_term_years=30,
        )
        assert params.monthly_payment == 0.0

    def test_monthly_payment_zero_interest(self):
        """Test monthly_payment with zero interest rate."""
        params = CostAnalysisParams(
            home_price=500000,
            down_payment_pct=0.20,
            interest_rate=0.0,  # 0% interest
            loan_term_years=30,
        )
        # With no interest, payment is simply principal / months
        expected = 400000 / (30 * 12)
        assert abs(params.monthly_payment - expected) < 0.01

    def test_annual_maintenance_property(self):
        """Test the annual_maintenance computed property."""
        params = CostAnalysisParams(home_price=500000, hoa_monthly=0)
        assert params.annual_maintenance == 0

        params = CostAnalysisParams(home_price=500000, hoa_monthly=500)
        assert params.annual_maintenance == 6000

        params = CostAnalysisParams(home_price=500000, hoa_monthly=250.50)
        assert params.annual_maintenance == 3006


class TestYearlyAnalysis:
    """Tests for the YearlyAnalysis dataclass."""

    def test_roi_calculation(self):
        """Test ROI calculation."""
        analysis = YearlyAnalysis(
            year=5,
            home_value=550000,
            loan_balance=350000,
            equity=200000,
            annual_taxes=6600,
            annual_repair=1980,
            annual_maintenance=6000,
            annual_cash_outflow=14580,
            total_cash_invested=100000,
            annual_mortgage_payment=25000,
        )
        assert analysis.roi == 2.0  # 200000 / 100000

    def test_roi_zero_investment(self):
        """Test ROI when total cash invested is zero."""
        analysis = YearlyAnalysis(
            year=0,
            home_value=500000,
            loan_balance=400000,
            equity=100000,
            annual_taxes=6000,
            annual_repair=1800,
            annual_maintenance=0,
            annual_cash_outflow=7800,
            total_cash_invested=0,
            annual_mortgage_payment=0,
        )
        assert analysis.roi is None

    def test_roi_negative_investment(self):
        """Test ROI when total cash invested is negative."""
        analysis = YearlyAnalysis(
            year=0,
            home_value=500000,
            loan_balance=400000,
            equity=100000,
            annual_taxes=6000,
            annual_repair=1800,
            annual_maintenance=0,
            annual_cash_outflow=7800,
            total_cash_invested=-1000,  # Should not happen, but handle gracefully
            annual_mortgage_payment=0,
        )
        assert analysis.roi is None


class TestCalculateLoanBalance:
    """Tests for the calculate_loan_balance function."""

    def test_initial_balance(self):
        """Test loan balance at year 0."""
        balance = calculate_loan_balance(
            principal=400000,
            annual_rate=0.0479,
            term_years=30,
            years_elapsed=0,
        )
        # At year 0, balance should equal principal
        assert abs(balance - 400000) < 100  # Within $100

    def test_final_balance(self):
        """Test loan balance at end of term."""
        balance = calculate_loan_balance(
            principal=400000,
            annual_rate=0.0479,
            term_years=30,
            years_elapsed=30,
        )
        assert balance == 0.0

    def test_balance_decreases_over_time(self):
        """Test that loan balance decreases over time."""
        balances = []
        for year in range(0, 31, 5):
            balance = calculate_loan_balance(
                principal=400000,
                annual_rate=0.0479,
                term_years=30,
                years_elapsed=year,
            )
            balances.append(balance)

        # Each balance should be less than the previous
        for i in range(1, len(balances)):
            assert balances[i] < balances[i - 1]

    def test_balance_past_term(self):
        """Test loan balance when years elapsed exceeds term."""
        balance = calculate_loan_balance(
            principal=400000,
            annual_rate=0.0479,
            term_years=30,
            years_elapsed=35,
        )
        assert balance == 0.0

    def test_zero_principal(self):
        """Test loan balance with zero principal."""
        balance = calculate_loan_balance(
            principal=0,
            annual_rate=0.0479,
            term_years=30,
            years_elapsed=10,
        )
        assert balance == 0.0

    def test_zero_interest_rate(self):
        """Test loan balance with zero interest rate."""
        balance = calculate_loan_balance(
            principal=300000,
            annual_rate=0.0,
            term_years=30,
            years_elapsed=15,
        )
        # With 0% interest, balance decreases linearly
        expected = 300000 * (15 / 30)  # Half paid off at halfway point
        assert abs(balance - expected) < 1

    def test_high_interest_rate(self):
        """Test loan balance with high interest rate (10%)."""
        balance = calculate_loan_balance(
            principal=400000,
            annual_rate=0.10,
            term_years=30,
            years_elapsed=15,
        )
        # With high interest, balance decreases slowly early on
        # At 15 years with 10% rate, should still have significant balance
        assert balance > 300000  # More than 75% remaining due to high interest

    def test_short_term_loan(self):
        """Test loan balance for a 15-year loan."""
        balance = calculate_loan_balance(
            principal=400000,
            annual_rate=0.0479,
            term_years=15,
            years_elapsed=7,
        )
        # About halfway through a 15-year loan
        assert 150000 < balance < 250000


class TestRunAnalysis:
    """Tests for the run_analysis function."""

    def test_returns_correct_number_of_years(self):
        """Test that analysis returns correct number of year entries."""
        params = CostAnalysisParams(home_price=500000)
        results = run_analysis(params, years=30)
        # Should include year 0 through year 30
        assert len(results) == 31

    def test_returns_correct_number_of_years_custom(self):
        """Test analysis with custom year count."""
        params = CostAnalysisParams(home_price=500000)
        results = run_analysis(params, years=10)
        assert len(results) == 11  # Years 0-10

    def test_year_zero_values(self):
        """Test year 0 values."""
        params = CostAnalysisParams(
            home_price=500000,
            down_payment_pct=0.20,
            purchase_fees=35000,
        )
        results = run_analysis(params, years=5)
        year0 = results[0]

        assert year0.year == 0
        assert year0.home_value == 500000
        assert year0.total_cash_invested == 100000 + 35000  # down payment + fees
        assert year0.annual_mortgage_payment == 0  # No mortgage in year 0

    def test_home_value_appreciates(self):
        """Test that home value appreciates correctly."""
        params = CostAnalysisParams(
            home_price=500000,
            annual_growth_rate=0.03,
        )
        results = run_analysis(params, years=10)

        # Year 0: 500000
        # Year 1: 500000 * 1.03 = 515000
        # Year 10: 500000 * 1.03^10 ≈ 671958
        assert results[0].home_value == 500000
        assert abs(results[1].home_value - 515000) < 1
        expected_year10 = 500000 * (1.03 ** 10)
        assert abs(results[10].home_value - expected_year10) < 1

    def test_equity_increases_over_time(self):
        """Test that equity increases over time."""
        params = CostAnalysisParams(home_price=500000)
        results = run_analysis(params, years=30)

        # Equity should generally increase
        for i in range(1, len(results)):
            assert results[i].equity >= results[i - 1].equity

    def test_loan_balance_decreases(self):
        """Test that loan balance decreases over time."""
        params = CostAnalysisParams(home_price=500000, down_payment_pct=0.20)
        results = run_analysis(params, years=30)

        # Loan balance should decrease
        for i in range(1, len(results)):
            assert results[i].loan_balance <= results[i - 1].loan_balance

        # Should be zero at end of 30-year term
        assert results[30].loan_balance == 0.0

    def test_total_cash_invested_accumulates(self):
        """Test that total cash invested accumulates correctly."""
        params = CostAnalysisParams(home_price=500000)
        results = run_analysis(params, years=5)

        # Total cash invested should increase each year
        for i in range(1, len(results)):
            assert results[i].total_cash_invested > results[i - 1].total_cash_invested

    def test_annual_costs_calculation(self):
        """Test annual costs are calculated correctly."""
        params = CostAnalysisParams(
            home_price=500000,
            property_tax_rate=0.012,
            monthly_repair_pct=0.0003,
            hoa_monthly=500,
        )
        results = run_analysis(params, years=1)

        year1 = results[1]
        expected_home_value = 500000 * (1 + params.annual_growth_rate)

        # Check taxes
        expected_taxes = expected_home_value * params.property_tax_rate
        assert abs(year1.annual_taxes - expected_taxes) < 1

        # Check repairs
        expected_repairs = expected_home_value * params.monthly_repair_pct * 12
        assert abs(year1.annual_repair - expected_repairs) < 1

    def test_maintenance_inflation(self):
        """Test that maintenance costs inflate over time."""
        params = CostAnalysisParams(
            home_price=500000,
            hoa_monthly=500,
            maintenance_inflation=0.02,
        )
        results = run_analysis(params, years=10)

        base_maintenance = 500 * 12  # $6000
        for i, result in enumerate(results):
            expected = base_maintenance * ((1 + 0.02) ** i)
            assert abs(result.annual_maintenance - expected) < 1


class TestCompareHomes:
    """Tests for the compare_homes function."""

    def test_compare_multiple_homes(self):
        """Test comparing multiple homes."""
        homes = [
            ("Home A", CostAnalysisParams(home_price=400000)),
            ("Home B", CostAnalysisParams(home_price=500000)),
            ("Home C", CostAnalysisParams(home_price=600000)),
        ]

        results = compare_homes(homes, years=10)

        assert len(results) == 3
        assert "Home A" in results
        assert "Home B" in results
        assert "Home C" in results

        # Each home should have 11 years of analysis
        for name, analysis in results.items():
            assert len(analysis) == 11

    def test_compare_single_home(self):
        """Test comparing a single home."""
        homes = [("Single Home", CostAnalysisParams(home_price=500000))]

        results = compare_homes(homes, years=5)

        assert len(results) == 1
        assert "Single Home" in results
        assert len(results["Single Home"]) == 6

    def test_compare_empty_list(self):
        """Test comparing an empty list of homes."""
        results = compare_homes([], years=10)
        assert results == {}


class TestGetAnalysisSummary:
    """Tests for the get_analysis_summary function."""

    def test_summary_basic_values(self):
        """Test basic summary values."""
        params = CostAnalysisParams(
            home_price=500000,
            down_payment_pct=0.20,
            purchase_fees=35000,
            annual_growth_rate=0.03,
        )
        results = run_analysis(params, years=10)
        summary = get_analysis_summary(results)

        assert summary["years_analyzed"] == 10
        assert summary["initial_investment"] == 135000  # 100k down + 35k fees
        assert abs(summary["final_home_value"] - 500000 * (1.03 ** 10)) < 1

    def test_summary_appreciation(self):
        """Test appreciation calculations in summary."""
        params = CostAnalysisParams(
            home_price=500000,
            annual_growth_rate=0.05,
        )
        results = run_analysis(params, years=5)
        summary = get_analysis_summary(results)

        expected_final = 500000 * (1.05 ** 5)
        expected_appreciation = expected_final - 500000

        assert abs(summary["total_appreciation"] - expected_appreciation) < 1
        assert abs(summary["appreciation_pct"] - (expected_appreciation / 500000)) < 0.0001

    def test_summary_empty_results(self):
        """Test summary with empty results."""
        summary = get_analysis_summary([])
        assert summary == {}

    def test_summary_roi(self):
        """Test ROI in summary."""
        params = CostAnalysisParams(home_price=500000)
        results = run_analysis(params, years=10)
        summary = get_analysis_summary(results)

        assert summary["final_roi"] == results[-1].roi

    def test_summary_total_costs(self):
        """Test total costs in summary."""
        params = CostAnalysisParams(
            home_price=500000,
            property_tax_rate=0.012,
            monthly_repair_pct=0.0003,
            hoa_monthly=500,
        )
        results = run_analysis(params, years=5)
        summary = get_analysis_summary(results)

        # Verify these are positive values
        assert summary["total_taxes_paid"] > 0
        assert summary["total_repair_costs"] > 0
        assert summary["total_maintenance"] > 0


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_down_payment(self):
        """Test analysis with zero down payment."""
        params = CostAnalysisParams(
            home_price=500000,
            down_payment_pct=0.0,
        )
        results = run_analysis(params, years=5)

        assert params.down_payment == 0
        assert params.initial_loan == 500000
        assert results[0].total_cash_invested == params.purchase_fees

    def test_full_down_payment(self):
        """Test analysis with 100% down payment (cash purchase)."""
        params = CostAnalysisParams(
            home_price=500000,
            down_payment_pct=1.0,
        )
        results = run_analysis(params, years=5)

        assert params.down_payment == 500000
        assert params.initial_loan == 0
        assert params.monthly_payment == 0

        # With no loan, equity equals home value from day 1
        assert results[0].equity == 500000
        assert results[0].loan_balance == 0

    def test_very_high_interest_rate(self):
        """Test analysis with very high interest rate (15%)."""
        params = CostAnalysisParams(
            home_price=500000,
            down_payment_pct=0.20,
            interest_rate=0.15,
            loan_term_years=30,
        )
        results = run_analysis(params, years=30)

        # With 15% interest, monthly payment should be much higher
        assert params.monthly_payment > 4000  # Much higher than normal

        # Loan should still be paid off by end of term
        assert results[30].loan_balance == 0

    def test_very_low_interest_rate(self):
        """Test analysis with very low interest rate (1%)."""
        params = CostAnalysisParams(
            home_price=500000,
            down_payment_pct=0.20,
            interest_rate=0.01,
            loan_term_years=30,
        )
        results = run_analysis(params, years=30)

        # With 1% interest, monthly payment should be lower
        assert params.monthly_payment < 1500

    def test_short_loan_term(self):
        """Test analysis with short loan term (10 years)."""
        params = CostAnalysisParams(
            home_price=500000,
            down_payment_pct=0.20,
            loan_term_years=10,
        )
        results = run_analysis(params, years=15)

        # Loan should be paid off by year 10
        assert results[10].loan_balance == 0
        assert results[15].loan_balance == 0

    def test_long_analysis_period(self):
        """Test analysis over very long period."""
        params = CostAnalysisParams(
            home_price=500000,
            annual_growth_rate=0.03,
        )
        results = run_analysis(params, years=50)

        assert len(results) == 51

        # After 50 years of 3% growth, home value should be substantial
        expected_value = 500000 * (1.03 ** 50)
        assert abs(results[50].home_value - expected_value) < 1

    def test_negative_growth_rate(self):
        """Test analysis with negative growth rate (depreciation)."""
        params = CostAnalysisParams(
            home_price=500000,
            annual_growth_rate=-0.02,
        )
        results = run_analysis(params, years=5)

        # Home value should decrease
        for i in range(1, len(results)):
            assert results[i].home_value < results[i - 1].home_value

    def test_high_hoa_fees(self):
        """Test analysis with high HOA fees."""
        params = CostAnalysisParams(
            home_price=500000,
            hoa_monthly=2000,
        )
        results = run_analysis(params, years=5)

        assert params.annual_maintenance == 24000
        assert results[1].annual_maintenance > 0

    def test_zero_hoa_fees(self):
        """Test analysis with zero HOA fees."""
        params = CostAnalysisParams(
            home_price=500000,
            hoa_monthly=0,
            maintenance_inflation=0.02,
        )
        results = run_analysis(params, years=5)

        # With zero HOA, maintenance should remain zero even with inflation
        for result in results:
            assert result.annual_maintenance == 0

    def test_very_small_home_price(self):
        """Test analysis with very small home price."""
        params = CostAnalysisParams(home_price=50000)
        results = run_analysis(params, years=5)

        assert results[0].home_value == 50000
        assert params.down_payment == 10000
        assert params.initial_loan == 40000

    def test_very_large_home_price(self):
        """Test analysis with very large home price."""
        params = CostAnalysisParams(home_price=10000000)  # $10M
        results = run_analysis(params, years=5)

        assert results[0].home_value == 10000000
        assert params.down_payment == 2000000
        assert params.initial_loan == 8000000


class TestFinancialAccuracy:
    """Tests to verify financial calculation accuracy."""

    def test_mortgage_payment_formula(self):
        """Verify mortgage payment matches known calculation."""
        # Standard mortgage: $200k, 6%, 30 years = $1199.10/month
        params = CostAnalysisParams(
            home_price=250000,
            down_payment_pct=0.20,
            interest_rate=0.06,
            loan_term_years=30,
        )
        # Known value for this scenario is approximately $1199.10
        assert abs(params.monthly_payment - 1199.10) < 1

    def test_total_interest_paid(self):
        """Test that total interest paid can be calculated from analysis."""
        params = CostAnalysisParams(
            home_price=500000,
            down_payment_pct=0.20,
            interest_rate=0.0479,
            loan_term_years=30,
        )
        results = run_analysis(params, years=30)

        # Total mortgage payments over 30 years
        total_payments = sum(r.annual_mortgage_payment for r in results)

        # Interest paid = total payments - principal
        interest_paid = total_payments - params.initial_loan

        # With 4.79% over 30 years, interest should be substantial
        assert interest_paid > 200000

    def test_equity_equals_value_minus_loan(self):
        """Test that equity always equals home value minus loan balance."""
        params = CostAnalysisParams(home_price=500000)
        results = run_analysis(params, years=30)

        for result in results:
            calculated_equity = result.home_value - result.loan_balance
            assert abs(result.equity - calculated_equity) < 0.01

    def test_roi_formula(self):
        """Test ROI calculation formula."""
        params = CostAnalysisParams(home_price=500000)
        results = run_analysis(params, years=10)

        for result in results:
            if result.total_cash_invested > 0:
                expected_roi = result.equity / result.total_cash_invested
                assert abs(result.roi - expected_roi) < 0.0001
