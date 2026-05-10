import pandas as pd

def clean_sales_data(df):
    """
    Cleans the input sales dataframe.
    - Handles missing values
    - Normalizes date formats
    - Removes duplicates
    """
    # Required columns
    required_cols = ['product', 'region', 'date', 'sales']
    
    # Drop rows where any required column is missing
    df = df.dropna(subset=required_cols)
    
    # Fill remaining NaNs with appropriate defaults
    df = df.fillna({
        'product': 'Unknown',
        'region': 'Unknown',
        'sales': 0
    })
    
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    return df
