import os
import requests
import pandas as pd
# from io import StringIO # StringIO is not used

# Configuration
DATA_DIR = "data"
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# Resale Flat Prices Datasets
RESALE_PRICES_RESOURCES = [
    {"id": "d_ebc5ab87086db484f88045b47411ebc5", "name": "resale-flat-prices-1990-1999.csv", "has_remaining_lease_str": False},
    {"id": "d_43f493c6c50d54243cc1eab0df142d6a", "name": "resale-flat-prices-2000-feb2012.csv", "has_remaining_lease_str": False},
    {"id": "d_2d5ff9ea31397b66239f245f57751537", "name": "resale-flat-prices-mar2012-dec2014.csv", "has_remaining_lease_str": False},
    {"id": "d_ea9ed51da2787afaf8e51f827c304208", "name": "resale-flat-prices-jan2015-dec2016.csv", "has_remaining_lease_str": True},
    {"id": "d_8b84c4ee58e3cfc0ece0d773c8ca6abc", "name": "resale-flat-prices-jan2017-onwards.csv", "has_remaining_lease_str": True}
]
COMBINED_RESALE_PRICES_PROCESSED_FILENAME = "resale_prices_all_combined_cleaned.csv"

# Completion Status Dataset (remains the same)
COMPLETION_STATUS_RESOURCE_ID = "d_9bbcd0c9b0351c7f41c9bfdcdc746668"
COMPLETION_STATUS_RAW_FILENAME = "completion-status-hdb-units.csv"
COMPLETION_STATUS_PROCESSED_FILENAME = "completion_status_cleaned.csv"

# API Endpoints for data.gov.sg
DATA_GOV_INITIATE_DOWNLOAD_URL_TEMPLATE = "https://api-open.data.gov.sg/v1/public/api/datasets/{resource_id}/initiate-download"

def download_csv(resource_id, filename):
    """Downloads a CSV file from data.gov.sg using the initiate-download API."""
    filepath = os.path.join(RAW_DATA_DIR, filename)
    if os.path.exists(filepath):
        print(f"Raw data file {filename} already exists. Skipping download.")
        return filepath

    initiate_url = DATA_GOV_INITIATE_DOWNLOAD_URL_TEMPLATE.format(resource_id=resource_id)
    headers = {'Accept': 'application/json'}

    try:
        print(f"Initiating download for {filename} (Resource ID: {resource_id}) from {initiate_url}...")
        # Send GET with empty JSON body and appropriate headers
        initiate_response = requests.get(initiate_url, json={}, headers=headers)
        initiate_response.raise_for_status()
        initiate_data = initiate_response.json()
        
        # Check if the initiate response includes the download URL
        if initiate_data.get("code") == 0 and "url" in initiate_data.get("data", {}):
            csv_url = initiate_data.get("data", {}).get("url")
            print(f"URL available in response for {filename}: {csv_url}")
            print(f"Downloading {filename} from {csv_url}...")
            csv_data_response = requests.get(csv_url) 
            csv_data_response.raise_for_status()
            
            # Try UTF-8 first, fallback to ISO-8859-1 if needed
            try:
                content = csv_data_response.content.decode('utf-8')
            except UnicodeDecodeError as e:
                print(f"Error decoding content for {filename} with UTF-8: {e}. Trying with ISO-8859-1.")
                content = csv_data_response.content.decode('iso-8859-1')
                print(f"Successfully decoded with ISO-8859-1 fallback.")
            
            # Write content to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Successfully downloaded and saved to {filepath}")
            return filepath
        else:
            print(f"Failed to get download URL for {filename}. Code: {initiate_data.get('code')}, Message: {initiate_data.get('data', {}).get('message')}, Error: {initiate_data.get('errorMsg')}. Full Response: {initiate_data}")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error during download process for {filename} (Resource ID: {resource_id}): {http_err}")
        if http_err.response is not None:
            print(f"Response status code: {http_err.response.status_code}")
            print(f"Response content: {http_err.response.content.decode(errors='ignore')}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error during download process for {filename} (Resource ID: {resource_id}): {e}")
        return None
    except (ValueError, KeyError) as e: # Includes JSONDecodeError or unexpected JSON structure
        print(f"Error parsing JSON response for {filename} (Resource ID: {resource_id}): {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during download process for {filename}: {e}")
        import traceback
        traceback.print_exc()
        return None

def parse_remaining_lease(lease_str):
    """Converts 'X years Y months' or 'X years' or 'X mths' or just 'X' (assumed years) to total years as a float."""
    if pd.isna(lease_str) or lease_str == "" or not isinstance(lease_str, str):
        # Check if it's a number that was misidentified as string
        if isinstance(lease_str, (int, float)) and not pd.isna(lease_str):
            return float(lease_str) # Assume it's already in years
        return None
    
    lease_str = str(lease_str).lower() # Ensure it's a string for processing
    parts = lease_str.split()
    years = 0
    months = 0

    try:
        # Handle cases like "60 years 07 months" or "60 yrs 7 mths" or "60 Yrs" or "60"
        if "year" in lease_str or "yrs" in lease_str:
            # Find the number before "year" or "yrs"
            for i, part in enumerate(parts):
                if "year" in part or "yrs" in part:
                    if i > 0 and parts[i-1].isdigit():
                        years = int(parts[i-1])
                        break
        
        if "month" in lease_str or "mth" in lease_str or "mths" in lease_str:
             # Find the number before "month" or "mth"
            for i, part in enumerate(parts):
                if "month" in part or "mth" in part or "mths" in part:
                    if i > 0 and parts[i-1].isdigit():
                        months = int(parts[i-1])
                        break
        
        # If only a number is provided, assume it's years (e.g. "70" from Jan2015-Dec2016 dataset)
        if years == 0 and months == 0 and len(parts) == 1 and parts[0].replace('.', '', 1).isdigit():
            return float(parts[0])
        
        # If years was found but months was not explicitly set with a keyword,
        # and there's another number after years, it could be months.
        # e.g. "61 years 04 months" -> parts: ["61", "years", "04", "months"]
        # e.g. "61 years 4 months"
        # e.g. "61 years 4" (less likely but to be safe)
        if years > 0 and months == 0:
            try:
                year_keyword_idx = -1
                for i, part in enumerate(parts):
                    if "year" in part or "yrs" in part:
                        year_keyword_idx = i
                        break
                if year_keyword_idx != -1 and year_keyword_idx + 1 < len(parts) and parts[year_keyword_idx+1].isdigit():
                    # Check if the next part is "month" or "mth"
                    if not (year_keyword_idx + 2 < len(parts) and ("month" in parts[year_keyword_idx+2] or "mth" in parts[year_keyword_idx+2])):
                         months = int(parts[year_keyword_idx+1])
            except (ValueError, IndexError):
                pass # months remains 0

        if years == 0 and months == 0: # No keywords found, and not a single number
             # print(f"Could not parse lease string: '{lease_str}'. No keywords or single number.")
             return None

        return years + (months / 12.0)
    except (ValueError, IndexError) as e:
        # print(f"Could not parse lease string: '{lease_str}'. Error: {e}")
        return None

def download_and_process_all_resale_data(resources, processed_filepath):
    """
    Downloads all specified resale flat price datasets, cleans them individually,
    calculates or parses remaining lease, standardizes columns, combines them,
    and saves the final cleaned DataFrame.
    """
    all_cleaned_dfs = []
    expected_columns = [
        'month', 'town', 'flat_type', 'block', 'street_name', 'storey_range',
        'floor_area_sqm', 'flat_model', 'lease_commence_date', 'resale_price',
        'remaining_lease_years'
    ] # Define a common set of columns

    for resource_info in resources:
        resource_id = resource_info["id"]
        raw_filename = resource_info["name"]
        has_remaining_lease_str = resource_info["has_remaining_lease_str"]

        raw_filepath = download_csv(resource_id, raw_filename)
        if not raw_filepath or not os.path.exists(raw_filepath):
            print(f"Skipping {raw_filename} due to download/file issue.")
            continue

        print(f"Processing {raw_filename}...")
        try:
            df = pd.read_csv(raw_filepath)
            original_columns = df.columns.tolist()
            # Standardize column names
            df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
            
            # Fix common variations like 'floor_area_sqm' vs 'floor_area_(sqm)'
            df.rename(columns={
                'floor_area_(sqm)': 'floor_area_sqm', # Example, adjust if other variations found
                'lease_commence_date': 'lease_commence_date', # ensure consistency
                'remaining_lease': 'remaining_lease_str_original' # keep original if exists before parsing
            }, inplace=True)

            # Convert month to datetime
            if 'month' in df.columns:
                df['month'] = pd.to_datetime(df['month'], format='%Y-%m', errors='coerce')
            else:
                print(f"Column 'month' not found in {raw_filename}. Original columns: {original_columns}")
                df['month'] = pd.NaT # Add if missing, will be NaT

            # Convert numeric columns
            for col in ['floor_area_sqm', 'resale_price', 'lease_commence_date']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                else:
                    print(f"Numeric column '{col}' not found in {raw_filename}. Adding as NaN.")
                    df[col] = pd.NA


            # Calculate or parse remaining_lease
            if has_remaining_lease_str and 'remaining_lease_str_original' in df.columns:
                df['remaining_lease_years'] = df['remaining_lease_str_original'].apply(parse_remaining_lease)
            elif 'lease_commence_date' in df.columns and 'month' in df.columns:
                # Calculate remaining lease if not directly provided
                # Ensure lease_commence_date is int/float and month is datetime
                df['lease_commence_date'] = pd.to_numeric(df['lease_commence_date'], errors='coerce')
                df_valid_dates = df[df['month'].notna() & df['lease_commence_date'].notna()].copy()
                
                if not df_valid_dates.empty:
                    transaction_year = df_valid_dates['month'].dt.year
                    transaction_month_decimal = df_valid_dates['month'].dt.month / 12.0
                    transaction_time_decimal = transaction_year + transaction_month_decimal

                    lease_commence_year = df_valid_dates['lease_commence_date'] # This is already a year

                    # Age of flat at sale in years (more precise)
                    # Example: lease commence 1980, transaction Jan 1990 (1990.083) -> age ~10.083 years
                    # Transaction month is 1-12. If month is YYYY-MM, then (YYYY + (MM-1)/12)
                    # For simplicity, let's use year difference for age, then subtract from 99.
                    # A more precise calculation might consider months.
                    
                    # Age of flat = transaction year - lease_commence_date_year
                    # Add partial year from transaction month
                    age_at_sale = (df_valid_dates['month'].dt.year + (df_valid_dates['month'].dt.month -1)/12) - \
                                  df_valid_dates['lease_commence_date'] # Assuming lease commence date is start of year.

                    df.loc[df_valid_dates.index, 'remaining_lease_years'] = 99.0 - age_at_sale
                else:
                    df['remaining_lease_years'] = pd.NA
            else: # Should not happen if logic is correct
                df['remaining_lease_years'] = pd.NA


            # Select and reorder columns to ensure consistency
            # Add missing expected columns with NaN
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = pd.NA
            df = df[expected_columns]


            all_cleaned_dfs.append(df)
            print(f"Finished processing {raw_filename}. Shape: {df.shape}")

        except FileNotFoundError:
            print(f"File not found during processing: {raw_filepath}")
        except pd.errors.EmptyDataError:
            print(f"No data: {raw_filepath} is empty.")
        except Exception as e:
            print(f"Error processing {raw_filename}: {e}. Original columns: {original_columns if 'original_columns' in locals() else 'unknown'}")
            import traceback
            traceback.print_exc()


    if not all_cleaned_dfs:
        print("No resale dataframes were processed. Exiting resale data processing.")
        return

    print(f"Concatenating {len(all_cleaned_dfs)} resale dataframes...")
    combined_df = pd.concat(all_cleaned_dfs, ignore_index=True)
    print(f"Shape of combined resale data before final cleaning: {combined_df.shape}")

    # Final cleaning on combined data
    combined_df.dropna(subset=['resale_price', 'floor_area_sqm', 'month', 'town', 'flat_type'], inplace=True)
    combined_df = combined_df[combined_df['resale_price'] > 0]
    combined_df = combined_df[combined_df['floor_area_sqm'] > 0]
    
    # Optional: ensure remaining_lease_years is within a reasonable range (e.g., 0 to 99)
    if 'remaining_lease_years' in combined_df.columns:
        combined_df['remaining_lease_years'] = pd.to_numeric(combined_df['remaining_lease_years'], errors='coerce')
        combined_df = combined_df[(combined_df['remaining_lease_years'] >= 0) & (combined_df['remaining_lease_years'] <= 99)]


    combined_df.to_csv(processed_filepath, index=False, encoding='utf-8')
    print(f"Combined and cleaned resale data saved to {processed_filepath}")
    print(f"Final combined resale data shape: {combined_df.shape}")
    print("Sample of final combined resale data:")
    print(combined_df.head())
    print("\nData types of final combined resale data:")
    combined_df.info()

def clean_completion_data(raw_filepath, processed_filepath):
    """Cleans the HDB completion status data."""
    if not os.path.exists(raw_filepath):
        print(f"Raw data file not found: {raw_filepath}. Skipping cleaning.")
        return

    print(f"Cleaning {raw_filepath}...")
    try:
        df = pd.read_csv(raw_filepath)

        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
        
        df['financial_year'] = pd.to_numeric(df['financial_year'], errors='coerce')
        df['no_of_units'] = pd.to_numeric(df['no_of_units'], errors='coerce')
        
        # Handle missing values (example: fill 0 for no_of_units if appropriate or drop)
        df['no_of_units'].fillna(0, inplace=True) # Assuming NaN means 0 units
        df.dropna(subset=['financial_year', 'town_or_estate', 'status'], inplace=True) # Critical info

        df.to_csv(processed_filepath, index=False, encoding='utf-8')
        print(f"Cleaned completion data saved to {processed_filepath}")
        print(f"Completion data shape after cleaning: {df.shape}")
        print("Sample of cleaned completion data:")
        print(df.head())
        print("\nData types of cleaned completion data:")
        print(df.info())

    except FileNotFoundError:
        print(f"File not found: {raw_filepath}")
    except pd.errors.EmptyDataError:
        print(f"No data: {raw_filepath} is empty.")
    except Exception as e:
        print(f"Error cleaning completion data {raw_filepath}: {e}")

def main():
    """Main function to download and clean all datasets."""
    # Create directories if they don't exist
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

    # Download and process ALL Resale Flat Prices
    print("--- Starting Resale Flat Prices Processing ---")
    download_and_process_all_resale_data(
        RESALE_PRICES_RESOURCES,
        os.path.join(PROCESSED_DATA_DIR, COMBINED_RESALE_PRICES_PROCESSED_FILENAME)
    )
    print("--- Finished Resale Flat Prices Processing ---\n")

    # Download and process Completion Status
    print("--- Starting Completion Status Processing ---")
    completion_raw_path = download_csv(COMPLETION_STATUS_RESOURCE_ID, COMPLETION_STATUS_RAW_FILENAME)
    if completion_raw_path and os.path.exists(completion_raw_path):
        clean_completion_data(completion_raw_path, os.path.join(PROCESSED_DATA_DIR, COMPLETION_STATUS_PROCESSED_FILENAME))
    else:
        print(f"Skipping cleaning for completion data as raw file was not downloaded/found: {completion_raw_path}")
    print("--- Finished Completion Status Processing ---\n")
    
    print("\nAll data processing tasks finished.")

if __name__ == "__main__":
    main() 