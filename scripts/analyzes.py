import pandas as pd
import os

def load_data(filename="KPI_Report.csv"):
    """
    Load KPI data from CSV file.
    """
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', filename)
    return pd.read_csv(data_path)

def clean_and_process_kpi(df):
    """
    Clean and preprocess the KPI dataframe.
    """
    # Convert date column
    df['WeekEndingCY'] = pd.to_datetime(df['WeekEndingCY'], errors='coerce')

    # Filter invalid Sales / Day
    df = df[df['Sales / Day'].notna()]
    df = df[df['Sales / Day'] != 0]
    df = df[df['Sales / Day'] != '']

    # Clean Sales / Day column
    df['Sales / Day'] = df['Sales / Day'].astype(str).str.replace(r'[$,\s]', '', regex=True)
    df['Sales / Day'] = pd.to_numeric(df['Sales / Day'], errors='coerce')

    # Filter rows with valid CPD - PY and Customers Repeat % - CY
    df = df[(df['CPD - PY'] != 0) & (df['CPD - PY'] != 0) & (df['Customers Repeat % - CY'] != 0)]

    # Drop unwanted columns if they exist
    columns_to_drop = [
        'High.Mileage.Opportunity...CY', 'Emission.Tickets...CY',
        'Emission.Gross.ARO...CY', 'Emissions.Penetration..',
        'Emissions.with.Big.5.....CY'
    ]
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')

    # Clean Net Sales - YoY % column if exists
    if 'Net Sales - YoY %' in df.columns:
        df['Net Sales - YoY %'] = df['Net Sales - YoY %'].astype(str).str.replace(r'[\s,%]', '', regex=True)
        df['Net Sales - YoY %'] = pd.to_numeric(df['Net Sales - YoY %'], errors='coerce')

    return df

def analyze_highest_revenue(df):
    """
    Calculate mean daily sales by Shop, descending order.
    """
    highest_revenue = (
        df.groupby('Shop')['Sales / Day']
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={'Sales / Day': 'Highest Sales'})
        .sort_values(by='Highest Sales', ascending=False)
    )
    return highest_revenue

def analyze_lowest_baytime(df):
    """
    Calculate mean BayTime by Shop, ascending order.
    """
    if 'BayTime' not in df.columns:
        return pd.DataFrame()
    lowest_baytime = (
        df.groupby('Shop')['BayTime']
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={'BayTime': 'Lowest BayTime'})
        .sort_values(by='Lowest BayTime')
    )
    return lowest_baytime

def analyze_highest_cpd(df):
    """
    Calculate mean CPD by Shop, descending order.
    """
    if 'CPD' not in df.columns:
        return pd.DataFrame()
    highest_cpd = (
        df.groupby('Shop')['CPD']
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={'CPD': 'Highest Number of CPD'})
        .sort_values(by='Highest Number of CPD', ascending=False)
    )
    return highest_cpd

def analyze_highest_growth(df):
    """
    Calculate mean Net Sales YoY % by Shop, descending order.
    """
    if 'Net Sales - YoY %' not in df.columns:
        return pd.DataFrame()
    highest_growth = (
        df.groupby('Shop')['Net Sales - YoY %']
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={'Net Sales - YoY %': 'Highest Yearly Sales Growth'})
        .sort_values(by='Highest Yearly Sales Growth', ascending=False)
    )
    highest_growth['Growth.Label'] = highest_growth['Highest Yearly Sales Growth'].astype(str) + '%'
    return highest_growth[['Shop', 'Growth.Label']]

def count_top(df_metric, top_n):
    """
    Helper to get top N shops from a metric dataframe.
    """
    return df_metric.head(top_n).reset_index()[['Shop']].assign(Appearance=1)

def build_leaderboard(highest_revenue, lowest_baytime, highest_cpd, highest_growth):
    """
    Build combined leaderboard DataFrame from different metrics.
    """
    top_1 = pd.concat([
        count_top(highest_revenue, 1),
        count_top(lowest_baytime, 1),
        count_top(highest_cpd, 1),
        count_top(highest_growth, 1)
    ])

    top_3 = pd.concat([
        count_top(highest_revenue, 3),
        count_top(lowest_baytime, 3),
        count_top(highest_cpd, 3),
        count_top(highest_growth, 3)
    ])

    top_5 = pd.concat([
        count_top(highest_revenue, 5),
        count_top(lowest_baytime, 5),
        count_top(highest_cpd, 5),
        count_top(highest_growth, 5)
    ])

    leaderboard = (
        top_1.groupby('Shop').sum().rename(columns={'Appearance': 'Top1'})
        .join(top_3.groupby('Shop').sum().rename(columns={'Appearance': 'Top3'}), how='outer')
        .join(top_5.groupby('Shop').sum().rename(columns={'Appearance': 'Top5'}), how='outer')
        .fillna(0).astype(int)
        .sort_values(by=['Top1', 'Top3', 'Top5'], ascending=[False, False, False])
    )
    return leaderboard

# Optional: if run as script, demo output
if __name__ == "__main__":
    df = load_data()
    df = clean_and_process_kpi(df)

    highest_revenue = analyze_highest_revenue(df)
    lowest_baytime = analyze_lowest_baytime(df)
    highest_cpd = analyze_highest_cpd(df)
    highest_growth = analyze_highest_growth(df)

    print("Highest Revenue:")
    print(highest_revenue.head())

    print("\nLowest BayTime:")
    print(lowest_baytime.head())

    print("\nHighest CPD:")
    print(highest_cpd.head())

    print("\nHighest Yearly Sales Growth:")
    print(highest_growth.head())

    leaderboard = build_leaderboard(highest_revenue, lowest_baytime, highest_cpd, highest_growth)
    print("\n🏆 Leaderboard:")
    print(leaderboard)
