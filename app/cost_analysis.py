"""Cost analysis calculations for home purchases.

This module implements the financial calculations from the Home Purchase Calculations
spreadsheet, computing projected costs, equity, and returns over time.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np

# Default values from the spreadsheet
DEFAULTS = {
    "down_payment_pct": 0.20,  # 20% down payment
    "purchase_fees": 35000.0,  # Closing costs, inspections, etc.
    "property_tax_rate": 0.012,  # 1.2% annual property tax
    "monthly_repair_pct": 0.0003,  # 0.03% of home value per month
    "hoa_monthly": 0.0,  # Monthly HOA/maintenance (varies by property)
    "annual_growth_rate": 0.03,  # 3% expected annual appreciation
    "interest_rate": 0.0479,  # 4.79% mortgage interest rate
    "loan_term_years": 30,  # 30-year mortgage
    "maintenance_inflation": 0.02,  # 2% annual increase in maintenance costs
}


@dataclass
class CostAnalysisParams:
    """Parameters for cost analysis calculations."""

    home_price: float
    down_payment_pct: float = DEFAULTS["down_payment_pct"]
    purchase_fees: float = DEFAULTS["purchase_fees"]
    property_tax_rate: float = DEFAULTS["property_tax_rate"]
    monthly_repair_pct: float = DEFAULTS["monthly_repair_pct"]
    hoa_monthly: float = DEFAULTS["hoa_monthly"]
    annual_growth_rate: float = DEFAULTS["annual_growth_rate"]
    interest_rate: float = DEFAULTS["interest_rate"]
    loan_term_years: int = DEFAULTS["loan_term_years"]
    maintenance_inflation: float = DEFAULTS["maintenance_inflation"]

    @property
    def down_payment(self) -> float:
        """Calculate the down payment amount."""
        return self.home_price * self.down_payment_pct

    @property
    def initial_loan(self) -> float:
        """Calculate the initial loan amount."""
        return self.home_price * (1 - self.down_payment_pct)

    @property
    def monthly_payment(self) -> float:
        """Calculate the monthly mortgage payment using PMT formula."""
        if self.initial_loan <= 0:
            return 0.0
        monthly_rate = self.interest_rate / 12
        num_payments = self.loan_term_years * 12
        if monthly_rate == 0:
            return self.initial_loan / num_payments
        return self.initial_loan * (
            monthly_rate * (1 + monthly_rate) ** num_payments
        ) / ((1 + monthly_rate) ** num_payments - 1)

    @property
    def annual_maintenance(self) -> float:
        """Calculate the base annual maintenance (HOA * 12)."""
        return self.hoa_monthly * 12


@dataclass
class YearlyAnalysis:
    """Analysis results for a single year."""

    year: int
    home_value: float
    loan_balance: float
    equity: float
    annual_taxes: float
    annual_repair: float
    annual_maintenance: float
    annual_cash_outflow: float
    total_cash_invested: float
    annual_mortgage_payment: float

    @property
    def roi(self) -> Optional[float]:
        """Calculate return on investment (equity / total cash invested)."""
        if self.total_cash_invested <= 0:
            return None
        return self.equity / self.total_cash_invested


def calculate_loan_balance(
    principal: float, annual_rate: float, term_years: int, years_elapsed: int
) -> float:
    """Calculate remaining loan balance after a given number of years.

    Uses the present value formula: PV = PMT * [1 - (1+r)^-n] / r
    """
    if principal <= 0 or years_elapsed >= term_years:
        return 0.0

    monthly_rate = annual_rate / 12
    total_payments = term_years * 12
    remaining_payments = (term_years - years_elapsed) * 12

    if monthly_rate == 0:
        return principal * (remaining_payments / total_payments)

    # Calculate monthly payment
    monthly_payment = principal * (
        monthly_rate * (1 + monthly_rate) ** total_payments
    ) / ((1 + monthly_rate) ** total_payments - 1)

    # Calculate present value of remaining payments (loan balance)
    loan_balance = monthly_payment * (
        1 - (1 + monthly_rate) ** (-remaining_payments)
    ) / monthly_rate

    return max(0.0, loan_balance)


def run_analysis(params: CostAnalysisParams, years: int = 30) -> list[YearlyAnalysis]:
    """Run cost analysis over specified number of years.

    Args:
        params: The cost analysis parameters
        years: Number of years to analyze (default 30)

    Returns:
        List of YearlyAnalysis objects, one per year (including year 0)
    """
    results = []
    annual_mortgage = params.monthly_payment * 12

    for year in range(years + 1):
        # Home value appreciates annually
        home_value = params.home_price * ((1 + params.annual_growth_rate) ** year)

        # Calculate remaining loan balance
        loan_balance = calculate_loan_balance(
            params.initial_loan, params.interest_rate, params.loan_term_years, year
        )

        # Equity is home value minus remaining loan
        equity = home_value - loan_balance

        # Annual costs based on current home value
        annual_taxes = home_value * params.property_tax_rate
        annual_repair = home_value * params.monthly_repair_pct * 12

        # Maintenance inflates over time
        annual_maintenance = params.annual_maintenance * (
            (1 + params.maintenance_inflation) ** year
        )

        # Cash outflow for the year (excluding mortgage principal which builds equity)
        annual_cash_outflow = annual_taxes + annual_repair + annual_maintenance

        # Total cash invested calculation
        if year == 0:
            # Year 0: down payment + purchase fees
            total_cash_invested = params.down_payment + params.purchase_fees
        else:
            # Subsequent years: previous total + annual costs + mortgage payments
            prev_total = results[year - 1].total_cash_invested
            total_cash_invested = (
                prev_total
                + annual_maintenance
                + annual_mortgage
                + annual_taxes
                + annual_repair
            )

        results.append(
            YearlyAnalysis(
                year=year,
                home_value=home_value,
                loan_balance=loan_balance,
                equity=equity,
                annual_taxes=annual_taxes,
                annual_repair=annual_repair,
                annual_maintenance=annual_maintenance,
                annual_cash_outflow=annual_cash_outflow,
                total_cash_invested=total_cash_invested,
                annual_mortgage_payment=annual_mortgage if year > 0 else 0,
            )
        )

    return results


def compare_homes(
    homes_params: list[tuple[str, CostAnalysisParams]], years: int = 30
) -> dict[str, list[YearlyAnalysis]]:
    """Run analysis for multiple homes for comparison.

    Args:
        homes_params: List of (home_name, params) tuples
        years: Number of years to analyze

    Returns:
        Dictionary mapping home names to their analysis results
    """
    return {name: run_analysis(params, years) for name, params in homes_params}


def get_analysis_summary(results: list[YearlyAnalysis]) -> dict:
    """Get summary statistics from analysis results.

    Args:
        results: List of YearlyAnalysis objects

    Returns:
        Dictionary with summary statistics
    """
    if not results:
        return {}

    final = results[-1]
    initial = results[0]

    return {
        "years_analyzed": len(results) - 1,
        "initial_investment": initial.total_cash_invested,
        "final_home_value": final.home_value,
        "final_equity": final.equity,
        "total_cash_invested": final.total_cash_invested,
        "total_appreciation": final.home_value - initial.home_value,
        "appreciation_pct": (final.home_value - initial.home_value) / initial.home_value,
        "final_roi": final.roi,
        "total_taxes_paid": sum(r.annual_taxes for r in results[1:]),
        "total_repair_costs": sum(r.annual_repair for r in results[1:]),
        "total_maintenance": sum(r.annual_maintenance for r in results[1:]),
    }
