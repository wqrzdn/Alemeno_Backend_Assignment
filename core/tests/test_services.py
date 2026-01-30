from django.test import TestCase
from core.models import Customer, Loan
from core.services.loan_service import calc_emi
from core.services.credit_score import calculate_credit_score
from core.services.eligibility import check_loan_eligibility
from datetime import date

class ServiceTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="Test",
            last_name="User",
            age=30,
            phone_number="1234567890",
            monthly_salary=50000,
            approved_limit=1800000 # 36 * 50000
        )

    def test_calculate_emi(self):
        
        emi = calc_emi(100000, 12, 12)
        
        print(f"Calculated EMI: {emi}")
        self.assertTrue(8800 < emi < 8900)

    def test_credit_score_new_customer(self):
        
        score = calculate_credit_score(self.customer)
        self.assertEqual(score, 50)

    def test_eligibility_approval(self):
        
        result = check_loan_eligibility(self.customer, 50000, 13, 12)
        self.assertTrue(result['approval'])
        self.assertEqual(result['corrected_interest_rate'], 13)

    def test_eligibility_rejection_salary_cap(self):
        # .object
        # loan.
        Loan.objects.create(
            customer=self.customer,
            loan_amount=200000,
            interest_rate=12,
            tenure=12,
            monthly_installment=20000,
            emis_paid_on_time=0,
            start_date=date.today(),
            end_date=date.today()
        )
        
        result = check_loan_eligibility(self.customer, 100000, 12, 12)
        self.assertFalse(result['approval'])
