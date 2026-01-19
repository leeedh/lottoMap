import pandas as pd
import re

def normalize_phone_number(phone_number):
    if pd.isna(phone_number):
        return None
    return re.sub(r'\D', '', str(phone_number))

def main():
    # Read the all_lottery_stores.csv file
    try:
        df = pd.read_csv("all_lottery_stores.csv")
    except FileNotFoundError:
        print("Error: The file all_lottery_stores.csv was not found.")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Normalize '전화번호' column
    if '전화번호' in df.columns:
        df['전화번호'] = df['전화번호'].apply(normalize_phone_number)
        print("Successfully normalized '전화번호' in all_lottery_stores.csv")
    else:
        print("Column '전화번호' not found in all_lottery_stores.csv")


    # Save the normalized data back to the same CSV file
    try:
        df.to_csv("all_lottery_stores.csv", index=False)
    except Exception as e:
        print(f"Error writing CSV file: {e}")

if __name__ == "__main__":
    main()
