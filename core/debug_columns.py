import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "data"

def print_columns():
    try:
        loan_path = BASE_DIR / "loan_data.xlsx"
        df = pd.read_excel(loan_path, engine='openpyxl')
        print(f"Loan Data Columns: {df.columns.tolist()}")
        
        customer_path = BASE_DIR / "customer_data.xlsx"
        df_cust = pd.read_excel(customer_path, engine='openpyxl')
        print(f"Customer Data Columns: {df_cust.columns.tolist()}")
        
    except Exception as e:
        print(f"Error reading excel: {e}")

if __name__ == "__main__":
    print_columns()
