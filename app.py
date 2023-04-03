import streamlit as st
import pandas as pd
from currency_converter import CurrencyConverter
from datetime import datetime
import plotly.express as px

def usd_to_eur(usd: float, date: str) -> float:
    c.convert(100, 'EUR', 'USD', date=date(2013, 3, 21))
    datetime.strptime(date_str, '%m-%d-%Y').date()


def process_tasty_tax_document(data: pd.DataFrame) -> pd.DataFrame:
    """
    Process Tastytrade Year-to-Date Data Export

    Args:

    Returns:
    """

    # extract the symbol from the description
    data["SYMBOL"] = data["SEC_DESCR"].str.split(" +",  expand=True)[1]

    # remove the dollar sign from price
    data["OPEN_COST"] = data["NO_WS_PROCEEDS"].str.replace("$", "", regex=False)
    data["CLOSE_COST"] = data["NO_WS_COST"].str.replace("$", "", regex=False)

    # long/short
    data["LONG_SHORT"] = data["LONG_SHORT_IND"].map({"S": "Short", "L": "Long"})

    # datetime format
    data["CLOSE_DATE"] = pd.to_datetime(data["CLOSE_DATE"]).dt.date
    data["OPEN_DATE"] = pd.to_datetime(data["CLOSE_DATE"]).dt.date

    # cost format
    data["CLOSE_COST"] = data["CLOSE_COST"].astype(float)
    data["OPEN_COST"] = data["OPEN_COST"].astype(float)
    data["PL"] = data["OPEN_COST"] - data["CLOSE_COST"]     

    # cumsum
    data.sort_values(by="CLOSE_DATE", ascending=True, inplace=True)
    data["CUMULATED_PL"] = data["PL"].cumsum()    

    cols = ["SYMBOL", "SEC_TYPE", "LONG_SHORT", "OPEN_DATE", "OPEN_COST", "CLOSE_DATE", "CLOSE_COST", "PL", "CUMULATED_PL"]
    account = data[cols]
    account.columns = ["SYMBOL", "TYPE", "LONG/SHORT", "OPEN DATE", "OPEN COST", "CLOSE DATE", "CLOSE COST", "P/L", "CUMULATED P/L"]
    
    return account

st.set_page_config(layout="wide")
st.title("Stratton Oakmont Performance Dashboard")

with st.sidebar:
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        account = process_tasty_tax_document(data)    
        
        symbols = st.multiselect(
            'Symbols',
            account["SYMBOL"].sort_values().unique())
        if not symbols:
            symbols = account["SYMBOL"].sort_values().unique()
        
        min_date, max_date = st.slider(
            "Date range",
            value=(account["CLOSE DATE"].min(), account["CLOSE DATE"].max()),
            min_value=account["CLOSE DATE"].min(),
            max_value=account["CLOSE DATE"].max(),
            format="YYYY-MM-DD")
        
        account_filtered = account[
            (account["SYMBOL"].isin(symbols)) & 
            (account["CLOSE DATE"] >= min_date) &
            (account["CLOSE DATE"] <= max_date)]
        
    

if uploaded_file is not None:
    pl_last = int(account_filtered["P/L"].sum())
    pl_max = int(account_filtered["CUMULATED P/L"].max())
    pl_ann = int(pl_last / ((account["CLOSE DATE"].max() - account["CLOSE DATE"].min()).days) * 365)

    col1, col2, col3 = st.columns(3)
    col1.metric("P/L last", f"$ {pl_last}")
    col2.metric("P/L max", f"$ {pl_max}")
    col3.metric("P/L annualized", f"$ {pl_ann}")
    
    st.subheader("Trade Log")
    st.dataframe(account_filtered, use_container_width=True)

    st.subheader("Cumulated P/L")
    df_cpl = account_filtered.groupby("CLOSE DATE")["CUMULATED P/L"].last().reset_index()
    fig = px.line(df_cpl, x="CLOSE DATE", y="CUMULATED P/L")

    df_pl = account_filtered.groupby("CLOSE DATE")["P/L"].sum().reset_index()
    fig.add_bar(x=df_pl["CLOSE DATE"], y=df_pl["P/L"], name="Daily P/L")
    st.plotly_chart(fig, use_container_width=True)