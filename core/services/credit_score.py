from datetime import date
from decimal import Decimal
from core.models import Customer

def calculate_credit_score(customer):
    #  score based on payment history and loan activity
    # TODO: Add more sophisticated payment tracking
    
    loans = customer.loans.all()
    
    # heck if limit - instant rejection 
    current_debt = sum(l.remaining_principal() for l in loans if l.is_active())
    if current_debt > Decimal(str(customer.approved_limit)):
        return 0

    if not loans.exists():
        return 50  # new customer baseline

    score = 50
    
    # check payment performance 
    completed = 0
    total_paid = 0
    tenure_sum = 0
    
    for loan in loans:
        total_paid += loan.emis_paid_on_time
        tenure_sum += loan.tenure
        if not loan.is_active():
            completed += 1
    
    # FIXME:  might not be accurate for customers with short loans
    if tenure_sum > 0:
         perf_ratio = total_paid / tenure_sum
         if perf_ratio > 0.9:
             score += 10  # good payment history
         elif perf_ratio > 0.7:
             score += 5
         elif perf_ratio < 0.5:
             score -= 10  # risky customer

    # reward customers with completed loans
    if completed > 3:
        score += 10
    elif completed >= 1:
        score += 5
        
    # recent activity - too many new loans 
    current_year = date.today().year
    recent_loans = loans.filter(start_date__year=current_year).count()
    
    if recent_loans > 3:
        score -= 10  # potential debt
    elif recent_loans >= 1:
        score += 5

    # Higher volume customers
    total_vol = sum(Decimal(str(l.loan_amount)) for l in loans)
    if total_vol > 1000000:
        score += 10
    elif total_vol > 500000:
        score += 5
        
    return max(0, min(100, score))
