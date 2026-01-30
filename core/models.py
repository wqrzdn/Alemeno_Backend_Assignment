from django.db import models
from decimal import Decimal


class Customer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    age = models.IntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, db_index=True)

    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2)
    approved_limit = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['phone_number']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Loan(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="loans",
        db_index=True
    )

    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tenure = models.IntegerField(help_text="Tenure in months")
    monthly_installment = models.DecimalField(max_digits=10, decimal_places=2)

    emis_paid_on_time = models.IntegerField(default=0)

    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['customer', 'start_date']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def remaining_emis(self):
        return max(0, self.tenure - self.emis_paid_on_time)

    def is_active(self):
        # loan still has payments left
        return self.remaining_emis() > 0

    def remaining_principal(self):
        # TODO: verify this formula
        if not self.is_active():
            return Decimal('0.00')
        
        remaining = self.remaining_emis()
        monthly_r = Decimal(str(self.interest_rate)) / Decimal('12') / Decimal('100')
        monthly_emi = Decimal(str(self.monthly_installment))
        
        # simple case - no interest
        if monthly_r == 0:
            return monthly_emi * remaining
        
        # use compound interest
        power = (Decimal('1') + monthly_r) ** remaining
        rem_principal = monthly_emi * (
            (power - Decimal('1')) / (monthly_r * power)
        )
        return round(rem_principal, 2)

    def __str__(self):
        return f"Loan {self.id} - {self.customer}"
