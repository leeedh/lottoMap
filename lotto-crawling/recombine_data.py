import pandas as pd

def combine_lottery_data():
    lotto_file = 'lotto_all_rounds.csv'
    pension_file = 'pension_all_rounds.csv'
    output_file = 'all_lottery_stores.csv'

    try:
        lotto_df = pd.read_csv(lotto_file)
        pension_df = pd.read_csv(pension_file)
        
        # Assuming the columns are compatible for concatenation
        combined_df = pd.concat([lotto_df, pension_df], ignore_index=True)
        
        combined_df.to_csv(output_file, index=False)
        print(f"Successfully combined {lotto_file} and {pension_file} into {output_file}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    combine_lottery_data()
