#!/usr/bin/env python
# coding: utf-8

# In[52]:


import pandas as pd
import streamlit as st
import plotly.express as px
from sodapy import Socrata
import requests
import folium
import matplotlib.pyplot as plt
from streamlit_folium import folium_static


# In[3]:


# importeren dataset
client = Socrata("opendata.rdw.nl", None)

results = client.get("qyrd-w56j", limit=500000)

results_df = pd.DataFrame.from_records(results)

results_df.head()


# In[4]:


verkoop = results_df[['kenteken', 'merk', 'datum_tenaamstelling']]
verkoop['datum_tenaamstelling'].min()


# In[5]:


verkoop['datum_tenaamstelling'].max()


# In[6]:



verkoop['maand'] = verkoop["datum_tenaamstelling"].astype(str).str[4:6]
aantal_m = verkoop.groupby(['maand'])
aantal_m = pd.DataFrame(aantal_m['datum_tenaamstelling'].count())
print(aantal_m)


# In[7]:



fig = px.line(aantal_m, title="Aantal verkochte personenauto's per maand vanaf 1971-2022")

fig.update_layout({'xaxis': {'title': {'text': 'Maand'}},
                   'yaxis': {'title':{'text': "Aantal verkochte personenauto's"}},
                   'legend': {'title':{'text': 'Verloop van het aantal per maand'}}})

fig.show()

st.plotly_chart(fig)


# In[8]:


verkoop['jaar'] = verkoop["datum_tenaamstelling"].astype(str).str[0:4]
jaren = verkoop.loc[(verkoop['jaar'] >= '2000')]
groep = jaren.groupby(['jaar'])
groep = pd.DataFrame(groep['datum_tenaamstelling'].count())
print(groep)


# In[9]:


fig = px.line(groep, title="Aantal verkochte personenauto's door de jaren 1971-2022")
fig.update_xaxes(rangeslider_visible=True)
fig.update_layout({'xaxis': {'title': {'text': 'Jaar'}},
                   'yaxis': {'title':{'text': "Aantal verkochte personenauto's"}},
                   'legend': {'title':{'text': 'Verloop van het aantal door de jaren heen'}}})    
fig.show()


# In[10]:


response = requests.get("https://api.openchargemap.io/v3/poi/?output=json&countrycode=NL&maxresults=300&compact=true&verbose=false&key=82802732-3808-478a-af53-f3c22ce7561d")


# In[11]:


df = pd.read_csv('laadpaaldata.csv')


# In[12]:


###Dataframe bevat kolom die een list zijn.
#Met json_normalize zet je de eerste kolom om naar losse kolommen
responsejson = response.json()
Laadpalen = pd.json_normalize(responsejson)
#Daarna nog handmatig kijken welke kolommen over zijn in dit geval Connections
#Kijken naar eerst laadpaal op de locatie
#Kan je uitpakken middels:
df4 = pd.json_normalize(Laadpalen.Connections)
df5 = pd.json_normalize(df4[0])
df5.head()
###Bestanden samenvoegen
Laadpalen = pd.concat([Laadpalen, df5], axis=1)
Laadpalen.head()


# In[13]:


Laadpalen.columns
Laadpalen['AddressInfo.Title']


# In[53]:



lat = Laadpalen['AddressInfo.Latitude'].mean()
lng = Laadpalen['AddressInfo.Longitude'].mean()
m = folium.Map(location = [lat, lng], zoom_start=11)

for row in Laadpalen.iterrows():
    row_values = row[1]
    location = [row_values['AddressInfo.Latitude'],row_values['AddressInfo.Longitude']]
    popup = (str(row_values['AddressInfo.Title']))
    marker = folium.Marker(location = location, popup = popup)
    marker.add_to(m)
folium_static(m)


# In[15]:


#informatie voor histogram
df


# In[16]:


df.describe()


# In[17]:


#outliers in kaart brengen
fig, axs = plt.subplots(1, 3, constrained_layout = True)
axs[0].boxplot(df['ConnectedTime'])
axs[1].boxplot(df['MaxPower'])
axs[2].boxplot(df['ChargeTime'])

plt.show()


# In[18]:


#outliers weghalen
Q1 = df['ConnectedTime'].quantile(0.25)
Q3 = df['ConnectedTime'].quantile(0.75)
IQR = Q3 - Q1

chargeQ1 = df['ChargeTime'].quantile(0.25)
chargeQ3 = df['ChargeTime'].quantile(0.75)
chargeIQR = chargeQ3 - chargeQ1

energyQ1 = df['TotalEnergy'].quantile(0.25)
energyQ3 = df['TotalEnergy'].quantile(0.75)
energyIQR = energyQ3 - energyQ1

maxQ1 = df['MaxPower'].quantile(0.25)
maxQ3 = df['MaxPower'].quantile(0.75)
maxIQR = maxQ3 - maxQ1


# In[19]:


#checken of zew weg zijn
df.describe()


# In[20]:


data = df[(df['ConnectedTime']) < (Q3 + 1.5 * IQR)]
data = data[(data['ChargeTime']) <  chargeQ3 + 1.5*chargeIQR]
data = data[(data['ChargeTime']) >  chargeQ1 - 1.5*chargeIQR]
data = data[(data['ChargeTime']) <  chargeQ3 + 1.5*chargeIQR]
data = data[(data['TotalEnergy']) <  energyQ3 + 1.5*energyIQR]
data = data[(data['TotalEnergy']) >  energyQ1 - 1.5*energyIQR]
data = data[(data['MaxPower']) >  maxQ1 - 1.5*maxIQR]
data = data[(data['MaxPower']) <  maxQ1 + 1.5*maxIQR]


# In[21]:


data.describe()


# In[22]:


#check of de outliers weg zijn
fig, axs = plt.subplots(1, 3, constrained_layout = True)
axs[0].boxplot(data['ConnectedTime'])
axs[1].boxplot(data['MaxPower'])
axs[2].boxplot(data['ChargeTime'])
plt.show()


# In[23]:


#nieuwe variabele kolom aanmaken met maand

data["Month"] = data["Started"].astype(str).str[5:7]
data.head(945)


# In[24]:


#aantal laadtijd per maand (uren)

laadtijd_totaal_maand = data.groupby('Month')['ChargeTime'].sum()
print(laadtijd_totaal_maand)


# In[25]:


#aantal laadsessies per maand 

aantal_sessies_maand = data.groupby(['Month'])
aantal_sessies_maand = pd.DataFrame(aantal_sessies_maand['Started'].count())
print(aantal_sessies_maand)


# In[26]:


#laadtijd in minuten

laadtijd_totaal_maand * 60


# In[27]:


#tabel in minuten om straks te kunnen divivden

Table= {
    'Maand' :["01","02","03","04","05","06","07","08","09","10","11","12"],
    'laadduur minuten':[ 98050.2180,84304.0620,88751.8620,81726.0000,73870.9320,81181.6500,68645.0280,83502.1200,85965.8340,85594.0560,90817.3680,94268.7432],
    'laadsessie aantal':[660,588,628,609,539,582,519,597,641,664,678,674]
          }
data_laadduur_minuten = pd.DataFrame(Table)
print(data_laadduur_minuten)


# In[28]:


#gemiddelde laadduur per sessie per maand in minuten

data_laadduur_minuten['Gemiddelde laadtijd minuten'] = data_laadduur_minuten['laadduur minuten']/data_laadduur_minuten['laadsessie aantal']
data_laadduur_minuten


# In[29]:


fig = px.histogram(data_laadduur_minuten, x="Maand", y="Gemiddelde laadtijd minuten")
fig.update_layout({'xaxis': {'title': {'text': 'Maand'}},
                   'yaxis': {'title':{'text': 'Gemiddelde laadtijd in minuten'}}})   


fig.show()
st.plotly_chart(fig)


# In[30]:


#tabel om straks te kunnen divivden in uren

Table= {
   'Maand' :["01","02","03","04","05","06","07","08","09","10","11","12"],
   'laadduur uren':[1634.17030,1405.06770,1479.19770,1362.10000,1231.18220,1353.02750,1144.08380,1391.70200,1432.76390,1426.56760,1513.62280,1571.14572],
   'laadsessie aantal':[660,588,628,609,539,582,519,597,641,664,678,674]
          }
data_laadduur_uren = pd.DataFrame(Table)
print(data_laadduur_uren)


# In[31]:


#gemiddelde laadduur per sessie per maand in minuten

data_laadduur_uren['Gemiddelde laadtijd uren'] = data_laadduur_uren['laadduur uren']/data_laadduur_uren['laadsessie aantal']
data_laadduur_uren


# In[32]:


fig = px.histogram(data_laadduur_uren, x="Maand", y="Gemiddelde laadtijd uren")
fig.update_layout({'xaxis': {'title': {'text': 'Maand'}},
                   'yaxis': {'title':{'text': 'Gemiddelde laadtijd in uren'}}}) 
fig.show()
st.plotly_chart(fig)


# In[33]:


#autoinfo compleet, nan kolommen gedropped

client = Socrata("opendata.rdw.nl", "68rdf4wjBddNMQ4wWpJX8qf1Y",
                  username="bundels.tjilpt0e@icloud.com",
                  password= "Gezeik3!_")


results = client.get("qyrd-w56j", limit=160000)

results_df = pd.DataFrame.from_records(results)

results_df = results_df.drop(results_df.iloc[:, 6:90], axis = 1)

results_df.head()


# In[34]:


#brandstoftabel kenteken, nan kolommen gedropped

results6 = client.get("e3cp-wr87", limit=9000000)


results_df6 = pd.DataFrame.from_records(results6)


results_df6 = results_df6.drop(results_df6.iloc[:, 3:36], axis = 1)

results_df6.head()


# In[35]:


#datsets gemerged nu brandstof type bij auto.

merged = results_df.merge(results_df6, on=['kenteken'], how="left")
merged.head()


# In[36]:


#aantallen per brandstof soort

merged['brandstof_omschrijving'].value_counts()


# In[37]:


#tabel brandstofsoorten uiteenzetten
Table= {
    'brandstof_omschrijving' :["Benzine","Diesel", "LPG", "Elektriciteit", "Alcohol", "CNG"],
    'aantal_brandstofsoort':[145192, 14667, 2795, 2576, 100, 53],
  
          }
merged_brandstof_piechart = pd.DataFrame(Table)
print(merged_brandstof_piechart)


# In[38]:


#brandstofsoorten in de vergelijking
fig = px.pie(merged_brandstof_piechart, values='aantal_brandstofsoort', names='brandstof_omschrijving', title="Brandstofsoorten in de vergelijking")
fig.show()
st.plotly_chart(fig)


# In[39]:


merged=merged.replace(to_replace="Benzine",value="1")
merged=merged.replace(to_replace="Diesel",value="2")
merged=merged.replace(to_replace="LPG",value="3")
merged=merged.replace(to_replace="Elektriciteit",value="4")
merged=merged.replace(to_replace="Alcohol",value="5")
merged=merged.replace(to_replace="CNG",value="6")

merged.head()


# In[40]:


fig = px.scatter(merged, x="merk", y="brandstof_omschrijving")
fig.show()
st.plotly_chart(fig)

