from django.contrib import admin

# Register your models here.
from .models import Customer, Loan


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "phone_number",
        "monthly_salary",
        "approved_limit",
    )
    search_fields = ("first_name", "last_name", "phone_number")


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "loan_amount",
        "interest_rate",
        "tenure",
        "monthly_installment",
        "emis_paid_on_time",
        "start_date",
        "end_date",
    )
    list_filter = ("interest_rate", "start_date")
