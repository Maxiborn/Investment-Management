import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

# Suppress the warning
warnings.filterwarnings("ignore", category=FutureWarning)
pd.options.mode.chained_assignment = None


################# GDP ###################
# Dateipfad zur Excel-Datei
IM_Data = "/Users/maximilianborn/Desktop/St Andrews lectures/Investment Management/Project/IM_Data.xlsx"  # Passe den Dateinamen an

# Mit pandas die Excel-Datei einlesen
df_stocks = pd.read_excel(IM_Data, sheet_name="Stocks")
df_fund = pd.read_excel(IM_Data, sheet_name="Fund")

# DataFrame anzeigen
#print(df_stocks)
#print(df_fund)

# DataFrames mergen 
df_stocks["Jahr"] = pd.to_datetime(df_stocks['Date'], format='%y.%m.%d').dt.year
df_fund["Jahr"] = pd.to_datetime(df_fund['FYR'], format='%y.%m.%d').dt.year
merge_df = df_stocks.merge(df_fund, on=['Firm Identifier', 'Jahr'], how='left')

# Kennzahlen hinzufügen 
merge_df["EV"] = merge_df["Size"] + merge_df["Total debt "] - merge_df["Cash & Cash Equivalents"]
merge_df["EBIT I"] = merge_df["Total Assets"] * merge_df["Profitability"]
merge_df["EBIT II"] = merge_df["Total Assets"] * merge_df["ROA"]
merge_df["EBIT I / EV"] = merge_df["EBIT II"] / merge_df["EV"]
merge_df["EBIT II / EV"] = merge_df["EBIT I"] / merge_df["EV"]
merge_df["BV / EV"] = merge_df["BE"] / merge_df["EV"]
print(merge_df)

merge_df.to_excel('IM.xlsx', index=False)

# Halbjahre erstellen
min_date = merge_df['Date'].min()
max_date = merge_df['Date'].max()

# Erstelle eine leere Liste, um die Halbjahresschritte zu speichern
monthly_steps = []

# Setze das Startdatum auf das kleinste Datum und gehe Monat für Monat vor
current_date = min_date
while current_date <= max_date:
    monthly_steps.append(current_date)
    # Gehe einen Monat vorwärts und setze das Datum auf den ersten Tag des nächsten Monats
    current_date = (current_date + pd.DateOffset(months=1)).replace(day=1)

# Die Liste monthly_steps enthält nun Monatsschritte mit dem ersten Tag jedes Monats

# Du kannst die Liste ausdrucken oder weiter verwenden
#print(monthly_steps)



# Step 1: Calculate average values of the last 6 month per month and ID 
average_df = pd.DataFrame(columns=['Firm Identifier', 'EBIT I / EV', 'EBIT II / EV', 'BV / EV', "Date"])

for j in range(len(monthly_steps) - 6):
    start_date = monthly_steps[j]
    end_date = monthly_steps[j + 6]

    # Filter rows within the 6-month window
    mask = (merge_df['Date'] >= start_date) & (merge_df['Date'] < end_date)
    filtered_df = merge_df[mask]

    if not filtered_df.empty:
        # Group by 'Firm Identifier' and calculate means
        average_clean_df = filtered_df.groupby('Firm Identifier', as_index=False)[['EBIT I / EV', 'EBIT II / EV', 'BV / EV']].mean()
        average_clean_df['Date'] = monthly_steps[j + 5].strftime('%Y-%m')
        average_df = pd.concat([average_df, average_clean_df], ignore_index=True)


print(average_df)
average_df.to_excel('Average_.xlsx', index=False)


# Step 2: Create Portfolios per month 

grouped = average_df.groupby('Date')

# Berechne die Quantile für die Spalten "Werte 1" und "Werte 2" in jeder Gruppe
quantiles = grouped[['EBIT I / EV',  'EBIT II / EV',   'BV / EV']].quantile([0.25, 0.75])

# Die Variable 'quantiles' enthält nun die Quantile für jede Gruppe (Datum)
print(quantiles)
quantiles = quantiles.reset_index()

# Benennen Sie die Multiindex-Spalten um, um die Quantile anzugeben
quantiles.columns = ['Date', 'Quantile', 'EBIT I / EV', 'EBIT II / EV', 'BV / EV']

# Jetzt haben Sie die Quantile als separate Spalten
print(quantiles)

# Zeigen Sie das aktualisierte DataFrame an
#print(average_df)

# Create portfolios 1 and 4 per Strategy
portfolio_df = pd.merge(quantiles, average_df, how='outer', left_on='Date', right_on='Date')

portfolio_df['Strategy 1: Portfolio 1'] = np.where((portfolio_df['Quantile'] == 0.25) & (portfolio_df['EBIT I / EV_y'] <= portfolio_df['EBIT I / EV_x']), portfolio_df['Firm Identifier'], np.nan)
portfolio_df['Strategy 1: Portfolio 4'] = np.where((portfolio_df['Quantile'] == 0.75) & (portfolio_df['EBIT I / EV_y'] > portfolio_df['EBIT I / EV_x']), portfolio_df['Firm Identifier'], np.nan)
portfolio_df['Strategy 2: Portfolio 1'] = np.where((portfolio_df['Quantile'] == 0.25) & (portfolio_df['EBIT II / EV_y'] <= portfolio_df['EBIT II / EV_x']), portfolio_df['Firm Identifier'], np.nan)
portfolio_df['Strategy 2: Portfolio 4'] = np.where((portfolio_df['Quantile'] == 0.75) & (portfolio_df['EBIT II / EV_y'] > portfolio_df['EBIT II / EV_x']), portfolio_df['Firm Identifier'], np.nan)
portfolio_df['Strategy 3: Portfolio 1'] = np.where((portfolio_df['Quantile'] == 0.25) & (portfolio_df['BV / EV_y'] <= portfolio_df['BV / EV_x']), portfolio_df['Firm Identifier'], np.nan)
portfolio_df['Strategy 3: Portfolio 4'] = np.where((portfolio_df['Quantile'] == 0.75) & (portfolio_df['BV / EV_y'] > portfolio_df['BV / EV_x']), portfolio_df['Firm Identifier'], np.nan)

print(portfolio_df)



portfolio_clean_df = portfolio_df[['Date', 'Strategy 1: Portfolio 1', 'Strategy 1: Portfolio 4',  'Strategy 2: Portfolio 1',  'Strategy 2: Portfolio 4',  'Strategy 3: Portfolio 1', 'Strategy 3: Portfolio 4']]
portfolio_clean_df = portfolio_clean_df.groupby('Date').agg(lambda x: x.dropna().tolist()).reset_index()
print(portfolio_clean_df)
portfolio_clean_df.to_excel('Portfolio_.xlsx', index=False)

# Strategy 1
portfolio_clean_df_s1 = portfolio_clean_df[['Date', 'Strategy 1: Portfolio 1', 'Strategy 1: Portfolio 4']].dropna(thresh=2)
print(portfolio_clean_df_s1)

# Strategy 2
portfolio_clean_df_s2 = portfolio_clean_df[['Date', 'Strategy 2: Portfolio 1', 'Strategy 2: Portfolio 4']].dropna(thresh=2)
print(portfolio_clean_df_s2)

# Strategy 3
portfolio_clean_df_s3 = portfolio_clean_df[['Date', 'Strategy 3: Portfolio 1', 'Strategy 3: Portfolio 4']].dropna(thresh=2)
print(portfolio_clean_df_s3)




# Step 3: Performance of Portfolios 
merge_df["Date Y/M"] = None
for i in range(len(merge_df["Date"])):
    merge_df["Date Y/M"][i] = merge_df["Date"][i].strftime('%Y-%m')


# Strategy 1

s1perf_df = pd.DataFrame(columns=['Date', 'Portfolio 1', 'Portfolio 4'])

for m in range(len(monthly_steps)-12):

    if(len(portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m]) == len(portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m])):
        for p in range(max(len(portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m]), len(portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m]))):
            x = pd.DataFrame(columns=['Date', 'Portfolio 1']) 

            x['Portfolio 1'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 1'] = x['Portfolio 1'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1+month])]['Return']+1).reset_index(drop=True)
    
            x['Portfolio 4'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 4'] = x['Portfolio 4'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1+month])]['Return']+1).reset_index(drop=True)

            x['Date'] = portfolio_clean_df_s1['Date'][m]
            s1perf_df = pd.concat([s1perf_df, x])

    elif(len(portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m]) < len(portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m])):
        diff = len(portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m]) - len(portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m])
        diff = [0] * diff
        portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m].extend(diff)

        for p in range(max(len(portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m]), len(portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m]))):
            x = pd.DataFrame(columns=['Date', 'Portfolio 1']) 

            x['Portfolio 1'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 1'] = x['Portfolio 1'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1+month])]['Return']+1).reset_index(drop=True)
    
            x['Portfolio 4'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 4'] = x['Portfolio 4'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1+month])]['Return']+1).reset_index(drop=True)

            x['Date'] = portfolio_clean_df_s1['Date'][m]
            s1perf_df = pd.concat([s1perf_df, x])

    else:
        diff = len(portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m]) - len(portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m])
        diff = [0] * diff 
        portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m].extend(diff)
    
        for p in range(max(len(portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m]), len(portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m]))):
            x = pd.DataFrame(columns=['Date', 'Portfolio 1']) 

            x['Portfolio 1'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 1'] = x['Portfolio 1'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1+month])]['Return']+1).reset_index(drop=True)
    
            x['Portfolio 4'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 4'] = x['Portfolio 4'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s1['Strategy 1: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s1['Date'][m+1+month])]['Return']+1).reset_index(drop=True)

            x['Date'] = portfolio_clean_df_s1['Date'][m]
            s1perf_df = pd.concat([s1perf_df, x])

s1perf_df = s1perf_df.groupby('Date').agg({'Portfolio 1': 'mean', 'Portfolio 4': 'mean'})

print(s1perf_df)

s1perf_df.to_excel('Performance Strategie 1_.xlsx')




# Strategy 2

s2perf_df = pd.DataFrame(columns=['Date', 'Portfolio 1', 'Portfolio 4'])

for m in range(len(monthly_steps)-12):

    if(len(portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m]) == len(portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m])):
        for p in range(max(len(portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m]), len(portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m]))):
            x = pd.DataFrame(columns=['Date', 'Portfolio 1']) 

            x['Portfolio 1'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 1'] = x['Portfolio 1'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1+month])]['Return']+1).reset_index(drop=True)
    
            x['Portfolio 4'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 4'] = x['Portfolio 4'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1+month])]['Return']+1).reset_index(drop=True)

            x['Date'] = portfolio_clean_df_s2['Date'][m]
            s2perf_df = pd.concat([s2perf_df, x])

    elif(len(portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m]) < len(portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m])):
        diff = len(portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m]) - len(portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m])
        diff = [0] * diff
        portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m].extend(diff)

        for p in range(max(len(portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m]), len(portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m]))):
            x = pd.DataFrame(columns=['Date', 'Portfolio 1']) 

            x['Portfolio 1'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 1'] = x['Portfolio 1'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1+month])]['Return']+1).reset_index(drop=True)
    
            x['Portfolio 4'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 4'] = x['Portfolio 4'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1+month])]['Return']+1).reset_index(drop=True)

            x['Date'] = portfolio_clean_df_s2['Date'][m]
            s2perf_df = pd.concat([s2perf_df, x])

    else:
        diff = len(portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m]) - len(portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m])
        diff = [0] * diff 
        portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m].extend(diff)
    
        for p in range(max(len(portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m]), len(portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m]))):
            x = pd.DataFrame(columns=['Date', 'Portfolio 1']) 

            x['Portfolio 1'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 1'] = x['Portfolio 1'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1+month])]['Return']+1).reset_index(drop=True)
    
            x['Portfolio 4'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 4'] = x['Portfolio 4'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s2['Strategy 2: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s2['Date'][m+1+month])]['Return']+1).reset_index(drop=True)

            x['Date'] = portfolio_clean_df_s2['Date'][m]
            s2perf_df = pd.concat([s2perf_df, x])

s2perf_df = s2perf_df.groupby('Date').agg({'Portfolio 1': 'mean', 'Portfolio 4': 'mean'})

print(s2perf_df)

s2perf_df.to_excel('Performance Strategie 2_.xlsx')

# Strategy 3

s3perf_df = pd.DataFrame(columns=['Date', 'Portfolio 1', 'Portfolio 4'])

for m in range(len(monthly_steps)-12):

    if(len(portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m]) == len(portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m])):
        for p in range(max(len(portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m]), len(portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m]))):
            x = pd.DataFrame(columns=['Date', 'Portfolio 1']) 

            x['Portfolio 1'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 1'] = x['Portfolio 1'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1+month])]['Return']+1).reset_index(drop=True)
    
            x['Portfolio 4'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 4'] = x['Portfolio 4'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1+month])]['Return']+1).reset_index(drop=True)

            x['Date'] = portfolio_clean_df_s3['Date'][m]
            s3perf_df = pd.concat([s3perf_df, x])

    elif(len(portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m]) < len(portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m])):
        diff = len(portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m]) - len(portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m])
        diff = [0] * diff
        portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m].extend(diff)

        for p in range(max(len(portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m]), len(portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m]))):
            x = pd.DataFrame(columns=['Date', 'Portfolio 1']) 

            x['Portfolio 1'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 1'] = x['Portfolio 1'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1+month])]['Return']+1).reset_index(drop=True)
    
            x['Portfolio 4'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 4'] = x['Portfolio 4'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1+month])]['Return']+1).reset_index(drop=True)

            x['Date'] = portfolio_clean_df_s3['Date'][m]
            s3perf_df = pd.concat([s3perf_df, x])

    else:
        diff = len(portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m]) - len(portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m])
        diff = [0] * diff 
        portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m].extend(diff)
    
        for p in range(max(len(portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m]), len(portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m]))):
            x = pd.DataFrame(columns=['Date', 'Portfolio 1']) 

            x['Portfolio 1'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 1'] = x['Portfolio 1'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 1'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1+month])]['Return']+1).reset_index(drop=True)
    
            x['Portfolio 4'] = (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1])]['Return']+1).reset_index(drop=True)
            for month in [1,2,3,4,5]:
                x['Portfolio 4'] = x['Portfolio 4'] * (merge_df[(merge_df['Firm Identifier'] == portfolio_clean_df_s3['Strategy 3: Portfolio 4'][m][p]) & (merge_df['Date Y/M'] == portfolio_clean_df_s3['Date'][m+1+month])]['Return']+1).reset_index(drop=True)

            x['Date'] = portfolio_clean_df_s3['Date'][m]
            s3perf_df = pd.concat([s3perf_df, x])

s3perf_df = s3perf_df.groupby('Date').agg({'Portfolio 1': 'mean', 'Portfolio 4': 'mean'})

print(s3perf_df)

s3perf_df.to_excel('Performance Strategie 3_.xlsx')


performance_dt = s1perf_df.merge(s2perf_df, on='Date', how='inner').merge(s3perf_df, on='Date', how='inner')

# Change names
performance_dt = performance_dt.rename(columns={'Portfolio 1_x':'Strategie 1 : Portfolio 1',
                                                'Portfolio 4_x':'Strategie 1 : Portfolio 4',  
                                                'Portfolio 1_y':'Strategie 2 : Portfolio 1',
                                                'Portfolio 4_y':'Strategie 2 : Portfolio 4',
                                                'Portfolio 1':'Strategie 3 : Portfolio 1',
                                                'Portfolio 4':'Strategie 3 : Portfolio 4',})

print(performance_dt)

performance_dt.to_excel('Performance_.xlsx')