from celery import shared_task
from django.db import connection
import pandas as pd
from pathlib import Path
from core.models import Customer, Loan
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent / "data"

def _reset_sequence(model_class):
    """
    Resets the database sequence
    """
    if connection.vendor == 'postgresql':
        try:
            table_name = model_class._meta.db_table
            with connection.cursor() as cursor:
                sql = f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM {table_name};"
                cursor.execute(sql)
            logger.info(f"Sequence reset for table {table_name}.")
        except Exception as e:
            logger.warning(f"Failed to reset sequence for {model_class.__name__}: {e}")

@shared_task
def ingest_customers():
    file_path = BASE_DIR / "customer_data.xlsx"
    if not file_path.exists():
        logger.error(f"Customer data file not found at {file_path}")
        return

    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        for _, row in df.iterrows():
            Customer.objects.update_or_create(
                id=row["Customer ID"],
                defaults={
                    "first_name": row["First Name"],
                    "last_name": row["Last Name"],
                    "age": row["Age"],
                    "phone_number": str(row["Phone Number"]), # Ensure string
                    "monthly_salary": row["Monthly Salary"],
                    "approved_limit": row["Approved Limit"],
                }
            )
        
        
        _reset_sequence(Customer)
        
        logger.info("Customer data ingestion successful.")
    except Exception as e:
        logger.error(f"Failed to ingest customers: {e}")
        raise

@shared_task
def ingest_loans():
    file_path = BASE_DIR / "loan_data.xlsx"
    if not file_path.exists():
        logger.error(f"Loan data file not found at {file_path}")
        return

    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        for _, row in df.iterrows():
            Loan.objects.update_or_create(
                id=row["Loan ID"],
                defaults={
                    "customer_id": row["Customer ID"],
                    "loan_amount": row["Loan Amount"],
                    "interest_rate": row["Interest Rate"],
                    "tenure": row["Tenure"],
                    "monthly_installment": row["Monthly payment"],
                    "emis_paid_on_time": row["EMIs paid on Time"],
                    "start_date": row["Date of Approval"],
                    "end_date": row["End Date"],
                }
            )
            
        
        _reset_sequence(Loan)

        logger.info("Loan data ingestion successful.")
    except Exception as e:
        logger.error(f"Failed to ingest loans: {e}")
        raise
