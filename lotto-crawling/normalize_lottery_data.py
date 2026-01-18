import pandas as pd
import re
from korean_cleaner import KoreanCleaner

def normalize_phone_number(phone_number):
    if pd.isna(phone_number):
        return None
    return re.sub(r'\D', '', str(phone_number))

def main():
    file_path = 'all_lottery_stores.csv'
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Normalize '전화번호' column
    df['전화번호'] = df['전화번호'].apply(normalize_phone_number)

    # Save the normalized data back to the same CSV file
    try:
        df.to_csv(file_path, index=False)
        print(f"Successfully normalized '전화번호' in {file_path}")
    except Exception as e:
        print(f"Error writing CSV file: {e}")

if __name__ == "__main__":
    main()
