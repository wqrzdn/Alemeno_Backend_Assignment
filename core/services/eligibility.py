from decimal import Decimal
from core.services.credit_score import calculate_credit_score
from core.services.loan_service import calc_emi
from core.models import Customer


def check_loan_eligibility(customer, requested_amount, requested_rate, tenure):
    # Get customer score - Risk slab
    score = calculate_credit_score(customer)
    
    approved = False
    final_rate = requested_rate
    
    #  rate floors based on risk level
    if score > 50:
        approved = True
        final_rate = requested_rate  # they qualify at requested rate
    elif score > 30:
        approved = True
        final_rate = max(requested_rate, 12.0)  # medium risk - 12% floor
    elif score > 10:
        approved = True
        final_rate = max(requested_rate, 16.0)  # high risk - 16% floor
    else:
        approved = False  # too risky

    # Check EMI affordability - can't exceed 50% of salary
    active_loans = customer.loans.all()
    current_emi_total = Decimal('0')
    for loan in active_loans:
        if loan.is_active():
            current_emi_total += Decimal(str(loan.monthly_installment))
            
    # calculate new EMI
    new_emi = calc_emi(requested_amount, final_rate, tenure)
    
    if (current_emi_total + new_emi) > (Decimal('0.5') * Decimal(str(customer.monthly_salary))):
        approved = False
    
    return {
        "approval": approved,
        "credit_score": score,
        "corrected_interest_rate": final_rate,
        "monthly_installment": new_emi
    }
