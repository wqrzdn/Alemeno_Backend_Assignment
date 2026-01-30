from django.core.management.base import BaseCommand
from core.tasks import ingest_customers, ingest_loans
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Ingest customer and loan data from Excel files'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting data ingestion...")
        try:
            # executing tasks synchronously
            ingest_customers()
            self.stdout.write(self.style.SUCCESS("Customer ingestion complete."))
            
            ingest_loans()
            self.stdout.write(self.style.SUCCESS("Loan ingestion complete."))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during ingestion: {str(e)}"))
            logger.error(f"Ingestion failed: {e}")
