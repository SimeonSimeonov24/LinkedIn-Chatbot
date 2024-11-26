import pandas as pd
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def load_data(data_path):
    """Load data from a CSV file."""
    return pd.read_csv(data_path)

def clean_data(df):
    """Clean the DataFrame by dropping unnecessary columns and formatting zip codes."""
    # Drop rows where the "title" column is missing
    df_cleaned = df.dropna(subset=["title"])
    
    # Specify the columns to remove
    columns_to_remove = [
        "max_salary", "pay_period", "med_salary", "min_salary", "company_id", "views",
        "applies", "original_listed_time", "job_posting_url", "application_url",
        "application_type", "expiry", "closed_time", "listed_time", "posting_domain",
        "sponsored", "fips"
    ]
    
    # Drop the specified columns
    df_cleaned = df_cleaned.drop(columns=columns_to_remove, errors='ignore')
    
    # Convert the zip_code column to string and format it correctly
    df_cleaned['zip_code'] = df_cleaned['zip_code'].apply(
        lambda x: f"{int(float(x)):05}" if pd.notnull(x) else ""
    )
    
    return df_cleaned

def save_cleaned_csv(df, cleaned_csv_path):
    """Save the cleaned DataFrame to a CSV file."""
    df.to_csv(cleaned_csv_path, index=False, quoting=1)  # quoting=1 corresponds to csv.QUOTE_ALL
    print(f"Cleaned CSV saved to: {cleaned_csv_path}")

def group_data_by_title(df):
    """Group the data by 'title' and convert to a dictionary."""
    grouped_data = df.groupby("title", group_keys=False).apply(
        lambda x: x.to_dict(orient="records"), include_groups=False
    ).to_dict()
    return grouped_data

def save_grouped_json(grouped_data, grouped_json_path):
    """Save grouped data to a JSON file."""
    # Convert the grouped data to JSON with null instead of NaN
    json_output = json.dumps(grouped_data, indent=4, default=str)
    json_output = json_output.replace('NaN', 'null')  # Replace NaN with null

    with open(grouped_json_path, "w") as json_file:
        json_file.write(json_output)
    print(f"Grouped JSON saved to: {grouped_json_path}")

def main():
    # Load paths from environment variables
    data_path = os.getenv("DATA_PATH")
    cleaned_csv_path = os.getenv("CLEANED_CSV_PATH")
    grouped_json_path = os.getenv("GROUPED_JSON_PATH")
    
    # Execute the data processing pipeline
    df = load_data(data_path)
    df_cleaned = clean_data(df)
    save_cleaned_csv(df_cleaned, cleaned_csv_path)
    grouped_data = group_data_by_title(df_cleaned)
    save_grouped_json(grouped_data, grouped_json_path)
    print("Data cleaning and grouping complete.")

if __name__ == "__main__":
    main()
