from rest_framework import serializers
from decimal import Decimal
from core.models import Customer, Loan


# ----------------------------
# Register Endpoint Serializers
# ----------------------------
class RegisterRequestSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50, required=True)
    last_name = serializers.CharField(max_length=50, required=True)
    age = serializers.IntegerField(min_value=18, max_value=120, required=True)
    monthly_income = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=Decimal('0.01'),
        required=True
    )
    phone_number = serializers.CharField(max_length=15, required=True)
    
    def validate_phone_number(self, value):
        #  duplicate phone numbers
        if Customer.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already registered")
        return value


class RegisterResponseSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source='id', read_only=True)
    name = serializers.SerializerMethodField()
    monthly_income = serializers.DecimalField(
        source='monthly_salary',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Customer
        fields = ['customer_id', 'name', 'age', 'monthly_income', 'approved_limit', 'phone_number']
    
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


# ----------------------------
# Check Eligibility Endpoint Serializers
# ----------------------------
class CheckEligibilityRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(min_value=1, required=True)
    loan_amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        min_value=Decimal('1000'),
        required=True
    )
    interest_rate = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        min_value=Decimal('0'), 
        max_value=Decimal('100'),
        required=True
    )
    tenure = serializers.IntegerField(min_value=1, max_value=360, required=True)


# ----------------------------
# Create Loan Endpoint Serializers
# ----------------------------
class CreateLoanRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(min_value=1, required=True)
    loan_amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        min_value=Decimal('1000'),
        required=True
    )
    interest_rate = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        min_value=Decimal('0'), 
        max_value=Decimal('100'),
        required=True
    )
    tenure = serializers.IntegerField(min_value=1, max_value=360, required=True)


# ----------------------------
# View Loan Endpoint Serializers
# ----------------------------
class LoanCustomerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField()
    age = serializers.IntegerField()


class ViewLoanResponseSerializer(serializers.Serializer):
    """Format single loan view response per API specification"""
    loan_id = serializers.IntegerField(source='id')
    customer = LoanCustomerSerializer()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    monthly_installment = serializers.DecimalField(max_digits=10, decimal_places=2)
    tenure = serializers.IntegerField()


# ----------------------------
# View Customer Loans Endpoint Serializers
# ----------------------------
class CustomerLoanSerializer(serializers.Serializer):
    """Format customer loans list response per API specification"""
    loan_id = serializers.IntegerField(source='id')
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    monthly_installment = serializers.DecimalField(max_digits=10, decimal_places=2)
    repayments_left = serializers.SerializerMethodField()
    
    def get_repayments_left(self, obj):
        return obj.remaining_emis()


# ----------------------------
# Legacy Serializers (for admin/internal use)
# ----------------------------
class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = [
            "id",
            "customer",
            "loan_amount",
            "interest_rate",
            "tenure",
            "monthly_installment",
            "emis_paid_on_time",
            "start_date",
            "end_date",
        ]
