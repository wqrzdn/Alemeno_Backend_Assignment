from decimal import Decimal


def calc_emi(principal, annual_rate, tenure_months):
    #  EMI formula:
    principal = Decimal(str(principal))
    annual_rate = Decimal(str(annual_rate))
    
    if tenure_months == 0:
        return Decimal('0.00')
    
    monthly_r = annual_rate / Decimal('12') / Decimal('100')
    
    #  zero interest case
    if monthly_r == 0:
        return round(principal / tenure_months, 2)
    
    power = (Decimal('1') + monthly_r) ** tenure_months
    emi = (principal * monthly_r * power) / (power - Decimal('1'))
    
    return round(emi, 2)
