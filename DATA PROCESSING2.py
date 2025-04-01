import pandas as pd
import re
import glob

import warnings
from warnings import filterwarnings
filterwarnings('ignore')

#Data_GD
files = glob.glob(r'Data_GD/*.xlsx')
dfs = []

for file in files:
    try:
        df = pd.read_excel(file, skiprows=7,nrows=20, engine="openpyxl")
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()

        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=df.columns[1:], how='any')

        df.dropna(how='all', inplace=True)

        match = re.search(r'(\d{8})', file)
        if match:
            df['ngày'] = pd.to_datetime(match.group(1), format='%Y%m%d')
        else:
            df['ngày'] = pd.NaT
        dfs.append(df)
    except Exception:
        pass
df_all = pd.concat(dfs, ignore_index=True)
df_all.columns = df_all.columns.str.strip().str.replace(' ', '_').str.lower()
df_all.to_csv("output.csv", index=False)

