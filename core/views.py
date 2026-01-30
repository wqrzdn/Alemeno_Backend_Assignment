from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal
import logging

from core.models import Customer, Loan
from core.serializers import (
    RegisterRequestSerializer,
    RegisterResponseSerializer,
    CheckEligibilityRequestSerializer,
    CreateLoanRequestSerializer,
    ViewLoanResponseSerializer,
    CustomerLoanSerializer,
)
from core.services.loan_service import calc_emi
from core.services.credit_score import calculate_credit_score
from core.services.eligibility import check_loan_eligibility

logger = logging.getLogger(__name__)


# ----------------------------
# Register Customer API
# ----------------------------
class RegisterView(APIView):
    # customer registration endpoint
    
    def post(self, request):
        serializer = RegisterRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Registration failed validation: {serializer.errors}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        # approved limit uses 36x monthly salary formula
        income = data['monthly_income']
        limit = self._calculate_approved_limit(income)
        
        try:
            customer = Customer.objects.create(
                first_name=data['first_name'],
                last_name=data['last_name'],
                age=data['age'],
                phone_number=data['phone_number'],
                monthly_salary=income,
                approved_limit=limit
            )
            
            logger.info(f"Customer {customer.id} registered successfully: {customer.first_name} {customer.last_name}")
            
            response_serializer = RegisterResponseSerializer(customer)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Customer registration failed: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to create customer"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def _calculate_approved_limit(monthly_income: Decimal) -> Decimal:
        """Calculate approved limit"""
        limit = monthly_income * 36
        lakh = Decimal('100000')
        return (limit / lakh).quantize(Decimal('1')) * lakh


# ----------------------------
# Check Loan Eligibility API
# ----------------------------
class CheckEligibilityView(APIView):
    # Check loan eligibility based on customer credit score
    
    def post(self, request):
        serializer = CheckEligibilityRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Eligibility check validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        # Get customer
        try:
            customer = Customer.objects.get(id=validated_data["customer_id"])
        except Customer.DoesNotExist:
            logger.warning(f"Customer not found: {validated_data['customer_id']}")
            return Response(
                {"error": "Customer not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check eligibility
        logger.info(f"Checking eligibility for customer {customer.id}")
        result = check_loan_eligibility(
            customer,
            requested_amount=validated_data["loan_amount"],
            requested_rate=validated_data["interest_rate"],
            tenure=validated_data["tenure"],
        )
        
        # Return response per API specification
        response_data = {
            "customer_id": customer.id,
            "approval": result["approval"],
            "interest_rate": float(validated_data["interest_rate"]),
            "corrected_interest_rate": float(result["corrected_interest_rate"]),
            "tenure": validated_data["tenure"],
            "monthly_installment": float(result["monthly_installment"])
        }
        
        logger.info(f"Eligibility check completed for customer {customer.id}: approval={result['approval']}")
        return Response(response_data)


# ----------------------------
# Create Loan API
# ----------------------------
class CreateLoanView(APIView):
    """
    Process a new loan based on eligibility.
    
    POST /api/create-loan/
    """
    
    def post(self, request):
        # Validate input
        serializer = CreateLoanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Loan creation validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        # Get customer
        try:
            customer = Customer.objects.get(id=validated_data["customer_id"])
        except Customer.DoesNotExist:
            logger.warning(f"Customer not found: {validated_data['customer_id']}")
            return Response(
                {"error": "Customer not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check eligibility
        logger.info(f"Creating loan for customer {customer.id}")
        result = check_loan_eligibility(
            customer,
            requested_amount=validated_data["loan_amount"],
            requested_rate=validated_data["interest_rate"],
            tenure=validated_data["tenure"],
        )
        
        if not result["approval"]:
            logger.info(f"Loan rejected for customer {customer.id}")
            return Response({
                "loan_id": None,
                "customer_id": customer.id,
                "loan_approved": False,
                "message": "Loan not approved based on credit criteria",
                "monthly_installment": float(result["monthly_installment"])
            }, status=status.HTTP_200_OK)
        
        # Create loan
        try:
            loan = Loan.objects.create(
                customer=customer,
                loan_amount=validated_data["loan_amount"],
                interest_rate=result["corrected_interest_rate"],
                tenure=validated_data["tenure"],
                monthly_installment=result["monthly_installment"],
                emis_paid_on_time=0,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30 * validated_data["tenure"])
            )
            
            logger.info(f"Loan {loan.id} created successfully for customer {customer.id}")
            
            return Response({
                "loan_id": loan.id,
                "customer_id": customer.id,
                "loan_approved": True,
                "message": "Loan approved successfully",
                "monthly_installment": float(result["monthly_installment"])
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Loan creation failed: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to create loan"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ----------------------------
# View Loan API
# ----------------------------
class ViewLoanView(APIView):
    """
    View specific loan details.
    
    GET /api/view-loan/<loan_id>/
    """
    
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.select_related('customer').get(id=loan_id)
        except Loan.DoesNotExist:
            logger.warning(f"Loan not found: {loan_id}")
            return Response(
                {"error": "Loan not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Format response per API specification
        response_data = {
            "loan_id": loan.id,
            "customer": {
                "id": loan.customer.id,
                "first_name": loan.customer.first_name,
                "last_name": loan.customer.last_name,
                "phone_number": loan.customer.phone_number,
                "age": loan.customer.age
            },
            "loan_amount": float(loan.loan_amount),
            "interest_rate": float(loan.interest_rate),
            "monthly_installment": float(loan.monthly_installment),
            "tenure": loan.tenure
        }
        
        logger.info(f"Loan {loan_id} details retrieved")
        return Response(response_data)


# ----------------------------
# View All Loans for Customer API
# ----------------------------
class ViewCustomerLoansView(APIView):
    """
    View all loans for a specific customer.
    
    GET /api/view-loans/<customer_id>/
    """
    
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            logger.warning(f"Customer not found: {customer_id}")
            return Response(
                {"error": "Customer not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        loans = customer.loans.all().order_by('-start_date')
        serializer = CustomerLoanSerializer(loans, many=True)
        
        logger.info(f"Retrieved {loans.count()} loans for customer {customer_id}")
        return Response(serializer.data)
