import os
import json
import pandas as pd
import gradio as gr
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all your analysis functions
from scripts.analyzes import (
    clean_and_process_kpi,
    analyze_highest_revenue,
    analyze_lowest_baytime,
    analyze_highest_cpd,
    analyze_highest_growth,
    build_leaderboard
)

# --- Folder setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
DATA_FILENAME = "KPI_Report.xlsx"
CHAT_HISTORY_FILE = "chat_history.json"

# --- Load Data ---
def load_data(filename=DATA_FILENAME):
    data_path = os.path.join(DATA_DIR, filename)
    try:
        if filename.lower().endswith('.csv'):
            return pd.read_csv(data_path)
        elif filename.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(data_path)
        else:
            raise ValueError("Unsupported file type")
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

# --- Chat History Functions ---
def save_chat_history(chat_history, filename=CHAT_HISTORY_FILE):
    os.makedirs(LOGS_DIR, exist_ok=True)
    filepath = os.path.join(LOGS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(chat_history, f, indent=2)

def load_chat_history(filename=CHAT_HISTORY_FILE):
    filepath = os.path.join(LOGS_DIR, filename)
    if not os.path.exists(filepath):
        return [{"role": "assistant", "content": "Hi! Ask me anything about company operations."}]
    with open(filepath, "r") as f:
        return json.load(f)

# --- Main Response Function ---
def respond(user_message, chat_history):
    if chat_history is None or not isinstance(chat_history, list):
        chat_history = []

    user_message_clean = user_message.lower().strip().strip('"').strip("'")
    df = load_data()

    show_rows_phrases = [
    "show me the first 5 rows",
    "show first 5 rows",
    "display first 5 rows",
    "show top 5 rows",
    "show first five rows",
    "show me top 5 rows", 
    "show five rows"
    ]

    revenue_phrases = [
    "highest average daily sales",
    "top sales",
    "most sales per day",
    "shop with highest sales",
    "best performing shop",
    "shop with best sales",
    "top revenue",
    "highest revenue"
]

    baytime_phrases = [
    "lowest bay time",
    "least bay time",
    "bay time minimum",
    "minimum bay time",
    "shop with lowest bay time",
    "fastest bay time",
    "quickest bay time",
    "best bay time",
    "top bay time"
    ]

    growth_phrases = [
    "highest growth",
    "yearly sales growth",
    "sales growth",
    "growth rate",
    "best growth",
    "top growth",
    "most growth"
    ]

    cpd_phrases = [
    "highest cpd",
    "count per day",
    "cars per day",
    "car count",
    "top cpd"
    ]   

    leaderboard_phrases = [
    "leaderboard",
    "top shops",
    "top performers",
    "best shops",
    "shop rankings",
    "shop leaderboard",
    "show rankings",
    "top 5 shops",
    "top ranked shops"
    ]

    if df is None:
        bot_message = "❌ Failed to load data."
    else:
        df = clean_and_process_kpi(df)

        if any(phrase in user_message_clean for phrase in show_rows_phrases):
            bot_message = f"Here are the first 5 rows:\n{df.head().to_string(index=False)}"

        elif any(phrase in user_message_clean for phrase in revenue_phrases):
            highest_revenue = analyze_highest_revenue(df)
            top_row = highest_revenue.iloc[0]
            bot_message = f"The shop with the highest average daily sales is **{top_row['Shop']}** with an average of **${top_row['Highest Sales']:,.2f}** per day."

        elif any(phrase in user_message_clean for phrase in baytime_phrases):
            lowest_baytime = analyze_lowest_baytime(df)
            if not lowest_baytime.empty:
                top_row = lowest_baytime.iloc[0]
                bot_message = f"The shop with the lowest average bay time is **{top_row['Shop']}** with **{top_row['Lowest BayTime']} minutes**."

            else:
                bot_message = "BayTime data is not available."

        elif any(phrase in user_message_clean for phrase in cpd_phrases):
            highest_cpd = analyze_highest_cpd(df)
            if not highest_cpd.empty:
                top_row = highest_cpd.iloc[0]
                bot_message = f"**{top_row['Shop']}** has the highest average CPD at **{top_row['Highest Number of CPD']}**."

            else:
                bot_message = "CPD data is not available."

        elif any(phrase in user_message_clean for phrase in growth_phrases):
            highest_growth = analyze_highest_growth(df)
            if not highest_growth.empty:
                top_row = highest_growth.iloc[0]
                bot_message = f"**{top_row['Shop']}** has the highest yearly sales growth at **{top_row['Growth.Label']}**."
            else:
                bot_message = "Sales growth data is not available."

        elif any(phrase in user_message_clean for phrase in leaderboard_phrases):
            leaderboard = build_leaderboard(
                analyze_highest_revenue(df),
                analyze_lowest_baytime(df),
                analyze_highest_cpd(df),
                analyze_highest_growth(df)
            )
            top5 = leaderboard.head().to_string()
            bot_message = f"🏆 Top shops leaderboard:\n{top5}"

        else:
            bot_message = f"✅ Data loaded with {len(df)} rows and {len(df.columns)} columns. Try asking about: 'highest average daily sales', 'lowest bay time', 'leaderboard', etc."

    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": bot_message})
    save_chat_history(chat_history)
    return bot_message

# --- Launch Gradio App ---
gr.Interface(fn=respond, inputs="text", outputs="text").launch()