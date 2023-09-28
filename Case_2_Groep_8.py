#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Stap 1: Data inladen
Diefstal = pd.read_csv('Diefstal.csv', delimiter=';')
inkomen = pd.read_csv('inkomen.csv', delimiter=';', low_memory=False)
gdf_provincie = gpd.read_file('Provincie.json')
gdf_nederland = gpd.read_file('Nederland.json')
gdf = gpd.read_file('Landsdelen.geojson')


# Stap 2: Gegevens bewerken
# Voor de 'Diefstal' dataset
Diefstal['Perioden'] = Diefstal['Perioden'].str[:-4]
mapping = {
    'T001540': 'diefstallen totaal',
    'A048105': 'diefstallen geweld',
    'A048106': 'diefstallen geen geweld'
}
Diefstal['SoortDiefstal'] = Diefstal['SoortDiefstal'].replace('CRI1121', 'alle diefstallen')
Diefstal['GebruikVanGeweld'] = Diefstal['GebruikVanGeweld'].replace(mapping)

# Voor de 'inkomen' dataset
inkomen['Perioden'] = inkomen['Perioden'].str[:-4]
inkomen['KenmerkenVanHuishoudens'] = inkomen['KenmerkenVanHuishoudens'].replace('1050010', 'inclusief studenten')

# Stap 3: Verwijder dubbele rijen
Diefstal.drop_duplicates(subset=['Perioden', 'RegioS', 'GebruikVanGeweld'], inplace=True)
inkomen.drop_duplicates(subset=['Perioden', 'RegioS'], inplace=True)

# Stap 4: Dataframes samenvoegen
df = pd.merge(inkomen, Diefstal, on=['RegioS', 'Perioden'], how='left')
# Replace missing values with 0 in the 'GeregistreerdeDiefstallenPer1000Inw_3' column of the original DataFrame
df['GeregistreerdeDiefstallenPer1000Inw_3'] = pd.to_numeric(df['GeregistreerdeDiefstallenPer1000Inw_3'], errors='coerce')
df['GeregistreerdeDiefstallenPer1000Inw_3'].fillna(0, inplace=True)
df['Perioden'] = df['Perioden'].astype(int)

# Stap 5: Mapping toevoegen
landsdeel_mapping = {'LD01  ': 'Noord-Nederland',
                 'LD02  ': 'Oost-Nederland',
                 'LD03  ': 'Zuid-Nederland',
                 'LD04  ': 'West-Nederland'}

provincie_mapping = {
    'PV20  ': 'Groningen',
    'PV21  ': 'Friesland',
    'PV22  ': 'Drenthe',
    'PV23  ': 'Overijssel',
    'PV24  ': 'Flevoland',
    'PV25  ': 'Gelderland',
    'PV26  ': 'Utrecht',
    'PV27  ': 'Noord-Holland',
    'PV28  ': 'Zuid-Holland',
    'PV29  ': 'Zeeland',
    'PV30  ': 'Noord-Brabant',
    'PV31  ': 'Limburg'
}

df['Nederland'] = df['RegioS'].map({'NL01  ': 'Nederland'}).fillna('')
df['Landsdeel'] = df['RegioS'].map(landsdeel_mapping).fillna('')
df['Provincie'] = df['RegioS'].map(provincie_mapping).fillna('')

sub_df_nederland = df[df['Nederland'] != '']
sub_df_landsdeel = df[df['Landsdeel'] != '']
sub_df_provincie = df[df['Provincie'] != '']

# Filter de GeoDataFrame om alleen rijen te behouden waarin "NAME_LATN" gelijk is aan "Netherlands" en "LEVL_CODE" gelijk is aan 1
gdf_landsdelen = gdf[(gdf['CNTR_CODE'] == 'NL') & (gdf['LEVL_CODE'] == 1)]

merged_Provinciedf = sub_df_provincie.merge(gdf_provincie[['name_1', 'geometry']], left_on='Provincie', right_on='name_1', how='left')
merged_Nederlandsedf = sub_df_nederland.merge(gdf_nederland[['name_local', 'geometry']], left_on='Nederland', right_on='name_local', how='left')
merged_Landsdeeldf = sub_df_landsdeel.merge(gdf_landsdelen[['NUTS_NAME', 'geometry']], left_on='Landsdeel', right_on='NUTS_NAME', how='left')

gdf_provincie = gpd.GeoDataFrame(merged_Provinciedf, geometry='geometry')
gdf_nederland = gpd.GeoDataFrame(merged_Nederlandsedf, geometry='geometry')
gdf_landsdeel = gpd.GeoDataFrame(merged_Landsdeeldf, geometry='geometry')

gdf_provincie['DI-Index'] = (gdf_provincie['GeregistreerdeDiefstallenPer1000Inw_3'] / gdf_provincie['GemiddeldGestandaardiseerdInkomen_3']) * 100
gdf_landsdeel['DI-Index'] = (gdf_landsdeel['GeregistreerdeDiefstallenPer1000Inw_3'] / gdf_landsdeel['GemiddeldGestandaardiseerdInkomen_3']) * 100
gdf_nederland['DI-Index'] = (gdf_nederland['GeregistreerdeDiefstallenPer1000Inw_3'] / gdf_nederland['GemiddeldGestandaardiseerdInkomen_3']) * 100


# In[4]:


import streamlit as st
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress 
import pandas as pd
import plotly.express as px

# Inhoudsopgave
st.sidebar.title('Inhoudsopgave')
option = st.sidebar.radio('Maak een keuze',['Intro','Diefstal vs Inkomen', 'Het DI-Index'])
custom_palette = sns.color_palette('viridis')  # Pas dit aan aan het gewenste kleurenschema


if option == 'Intro':
    # Pagina-titel en introductie
    st.title("Diefstallen vs. Inkomen in de periode 2011-2020")

    st.write(
        "Welkom bij ons interactieve dashboard waar we visualisaties presenteren "
        "van het aantal diefstallen in Nederland over de periode 2011 tot en met 2020, "
        "vergeleken met het gestandaardiseerde gemiddelde inkomen. Hier vind je inzichten "
        "en trends met betrekking tot criminaliteit en inkomen in Nederland.")

    # Voeg een afbeelding of grafiek toe als visuele aantrekking, bijvoorbeeld een scatterplot of een kaart.

    # Instructies voor gebruik
    st.write("### Instructies voor gebruik:")
    st.write(
        "1. Gebruik de inhoudsopgave om de gewenste visualisatieopties te bekijken."
    )
    st.write(
        "2. Bekijk de grafieken en visualisaties om patronen en trends te ontdekken. Veeg met uw muis over de visualisaties heen om de gewenste data in te zien."
    )
    st.write(
        "3. Gebruik de slidebars, selectieboxen en drop-down menu's om het gewenste jaartal en diefstal-filter toe te passen."
        
        
    )

    
    
    # Bronvermelding
    st.write(
        
        
        "De gegevens zijn verstrekt door CBS Open data StatLine en zijn gebaseerd op rapporten van 2011 t/m 2022."
    )

    # Voetnoot en contactinformatie
    st.write(
        "Dit dashboard is gemaakt door Eric de Jong en Elayza Lo-Ning-Hing en is bedoeld voor informatieve doeleinden."
    )


elif option == 'Diefstal vs Inkomen':
    st.title("Diefstal vs Inkomen")
    tabs = st.tabs(["Diefstal Overzicht", "Inkomen Overzicht", "Scatterplot"])

    # Tab voor 'Diefstal Overzicht'
    with tabs[0]:
        st.write("Je bevindt je op het Diefstal overzicht.")

        gdf_nederland['Perioden'] = gdf_nederland['Perioden'].astype(int)
        
        # Streamlit-app voor gdf_nederland
        st.header('Diefstal in Nederland')
        st.write('Ontdek de gegevens over diefstallen per 1000 inwoners in Nederland door de jaren heen.')

        # Voeg een slider toe om het jaartal te selecteren
        selected_year = st.slider('Selecteer een jaartal', min_value=2011, max_value=2020, value=(2011, 2020))


        # Voeg checkboxes toe om de waarden in de "GebruikVanGeweld" kolom te selecteren
        geweld_soorten = st.checkbox('Totaal aantal diefstallen', value=True)
        geweld_geweld = st.checkbox('Diefstallen met geweld', value=True)
        geweld_geen_geweld = st.checkbox('Diefstallen zonder geweld', value=True)

        # Filter de dataset op basis van de geselecteerde jaartallen en geweldsoorten
        selected_gebruik_geweld = []
        if geweld_soorten:
            selected_gebruik_geweld.append('diefstallen totaal')
        if geweld_geweld:
            selected_gebruik_geweld.append('diefstallen geweld')
        if geweld_geen_geweld:
            selected_gebruik_geweld.append('diefstallen geen geweld')

        filtered_df = gdf_nederland[
        (gdf_nederland['Perioden'] >= selected_year[0]) &
        (gdf_nederland['Perioden'] <= selected_year[1]) &
        (gdf_nederland['GebruikVanGeweld'].isin(selected_gebruik_geweld))
        ]

        # Maak een barplot met Plotly
        fig = px.bar(filtered_df, x='Perioden', y='GeregistreerdeDiefstallenPer1000Inw_3',
        color='GebruikVanGeweld', barmode='group', labels={'Perioden': 'Jaar', 'GeregistreerdeDiefstallenPer1000Inw_3': 'Geregistreerde Diefstallen per 1000 Inwoners'},
        title=f'Diefstallen per 1000 Inwoners ({selected_year[0]}-{selected_year[1]})',
        color_discrete_sequence=['forestgreen', 'yellow', 'darkblue'])

        # Toon de plot
        st.plotly_chart(fig)

    
    
    with tabs[1]:
        # Streamlit-app voor gdf_nederland
        st.title('Inkomen')
        st.write('Ontdek de gegevens over gemiddeld gestandaardiseerd inkomen in Nederland door de jaren heen.')

        # Filter de dataset op basis van de geselecteerde jaartallen voor de tweede plot
        filtered_df2 = gdf_nederland[
            (gdf_nederland['Perioden'] >= selected_year[0]) &
            (gdf_nederland['Perioden'] <= selected_year[1])
        ]

        # Maak een barplot met Plotly en gebruik de kleur '#1f77b4'
        fig2 = px.bar(filtered_df2, x='Perioden', y='GemiddeldGestandaardiseerdInkomen_3',
                     labels={'Perioden': 'Jaar', 'GemiddeldGestandaardiseerdInkomen_3': 'Gemiddeld Gestandaardiseerd Inkomen'},
                     title=f'Gemiddeld Gestandaardiseerd Inkomen ({selected_year[0]}-{selected_year[1]})',
                     color_discrete_sequence=['forestgreen'])

        # Toon de tweede plot
        st.plotly_chart(fig2)

    with tabs[2]:
        st.write('Je hebt "Scatterplot" geselecteerd.')
        # Streamlit-applicatie
        st.title('Scatterplot met Trendlijn: Diefstallen vs. Inkomen per Jaar')

        # Radio-buttons voor het selecteren van het type diefstal
        selected_theft_type = st.radio("Selecteer het type diefstal", ["Diefstallen Totaal", "Diefstallen Geweld", "Diefstallen Geen Geweld"])


        # Filter de gegevens op basis van het geselecteerde type diefstal
        filtered_data = merged_Provinciedf[merged_Provinciedf['GebruikVanGeweld'] == selected_theft_type.lower()]

        # Maak een scatterplot met Plotly
        fig = px.scatter(filtered_data, x='Perioden', y='GeregistreerdeDiefstallenPer1000Inw_3',
                         color='GemiddeldGestandaardiseerdInkomen_3',
                         labels={'Perioden': 'Jaar', 'GeregistreerdeDiefstallenPer1000Inw_3': 'Aantal Diefstallen per 1000 Inwoners',
                                 'GemiddeldGestandaardiseerdInkomen_3': 'Gemiddeld Gestandaardiseerd Inkomen'},
                         title=f'Scatterplot: {selected_theft_type} vs. Inkomen per Jaar', 
                         color_continuous_scale=['darkblue', 'forestgreen', 'yellow'])

        # Bereken en toon de trendlijn voor het geselecteerde type diefstal
        x = filtered_data['Perioden'].to_numpy()
        y = filtered_data['GeregistreerdeDiefstallenPer1000Inw_3'].to_numpy()

        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        trendline = intercept + slope * x

        # Voeg de trendlijn toe aan de scatterplot
        fig.add_scatter(x=x, y=trendline, mode='lines', line=dict(dash='dash', color = 'red'), name=f'Trendlijn ({selected_theft_type.lower()})')

        # Toon de scatterplot met trendlijn in Streamlit
        st.plotly_chart(fig)

else:
    st.title('Het DI-Index')
    st.write('Ontdek de verdeling van het DI-Index over verschillende schalen van Nederland en door de jaren heen.')
    # Code voor bepaald jaar
    # Maak een dropdown-menu voor het selecteren van een enkele geweldsoort voor gdf_nederland
    selected_geweld_soort = st.selectbox('Selecteer het type diefstal', 
                                                    ['diefstallen totaal', 'diefstallen geweld', 'diefstallen geen geweld'], 
                                                    index=0)  # Standaard geselecteerde waarde is 'diefstallen totaal'

    # Voeg een enkelvoudige slider toe om het jaar te selecteren voor gdf_nederland
    selected_year_1 = st.selectbox('Selecteer een jaartal', 
                                               list(range(2011, 2021)), 
                                               index=0, key='year_nederland')
    col1, col2, col3 = st.columns(3)
    with col1:

        # Voeg hier de code in voor de andere drie plaatjes
        
    
        # Zet de 'Perioden' kolom om naar een numeriek datatype (int)
        gdf_nederland['Perioden'] = gdf_nederland['Perioden'].astype(int)

        # Streamlit-app voor gdf_nederland


        # Filter de dataset op basis van het geselecteerde jaar en geweldsoort voor gdf_nederland
        gdf_selected_year_diefstal_nederland = gdf_nederland[(gdf_nederland['Perioden'] == selected_year_1) & (gdf_nederland['GebruikVanGeweld'] == selected_geweld_soort)]

        # Bereken de vmin en vmax waarden op basis van alle jaren voor de geselecteerde geweldsoort in gdf_nederland
        vmin_nederland = gdf_nederland[gdf_nederland['GebruikVanGeweld'] == selected_geweld_soort]['DI-Index'].min()
        vmax_nederland = gdf_nederland[gdf_nederland['GebruikVanGeweld'] == selected_geweld_soort]['DI-Index'].max()

        # Plot de provincies op basis van de DI-Index met een aangepaste range
        fig_nederland, ax_nederland = plt.subplots(1, 1, figsize=(15, 12))
        gdf_selected_year_diefstal_nederland.plot(column='DI-Index', linewidth=0.8, ax=ax_nederland, edgecolor='0.8', legend=True, vmin=vmin_nederland, vmax=vmax_nederland)
        ax_nederland.axis('off')  # Optioneel: uitschakelen van de assen
        # Voeg een titel toe aan de colorbar van de heatmap
        colorbar = ax_nederland.get_figure().get_axes()[1]  # Krijg de colorbar van de heatmap
        colorbar.set_title('DI-Index', fontsize=14)  # Voeg een titel toe

        # Toon de plot in Streamlit voor gdf_nederland
        st.pyplot(fig_nederland)
    
    with col2:
        # Streamlit-app voor gdf_landsdeel
        #st.title('DI-Index per Landsdeel in Nederland')

        # Filter de dataset op basis van het geselecteerde jaar en geweldsoort voor gdf_landsdeel
        gdf_selected_year_diefstal_landsdeel = gdf_landsdeel[(gdf_landsdeel['Perioden'] == selected_year_1) & (gdf_landsdeel['GebruikVanGeweld'] == selected_geweld_soort)]

        # Bereken de vmin en vmax waarden op basis van alle jaren voor de geselecteerde geweldsoort in gdf_landsdeel
        vmin_landsdeel = gdf_landsdeel[gdf_landsdeel['GebruikVanGeweld'] == selected_geweld_soort]['DI-Index'].min()
        vmax_landsdeel = gdf_landsdeel[gdf_landsdeel['GebruikVanGeweld'] == selected_geweld_soort]['DI-Index'].max()

        # Plot de landsdelen op basis van de DI-Index met een aangepaste range
        fig_landsdeel, ax_landsdeel = plt.subplots(1, 1, figsize=(15, 12))
        gdf_selected_year_diefstal_landsdeel.plot(column='DI-Index', linewidth=0.8, ax=ax_landsdeel, edgecolor='0.8', legend=True, vmin=vmin_landsdeel, vmax=vmax_landsdeel)
        ax_landsdeel.axis('off')  # Optioneel: uitschakelen van de assen
        # Voeg een titel toe aan de colorbar van de heatmap
        colorbar = ax_landsdeel.get_figure().get_axes()[1]  # Krijg de colorbar van de heatmap
        colorbar.set_title('DI-Index', fontsize=14)  # Voeg een titel toe

        # Toon de plot in Streamlit voor gdf_landsdeel
        st.pyplot(fig_landsdeel)
        
    with col3:
        # Streamlit-app voor gdf_provincie
        #st.title('DI-Index per Provincie in Nederland')

        # Filter de dataset op basis van de geselecteerde geweldsoort voor gdf_provincie
        gdf_selected_year_diefstal_provincie = gdf_provincie[(gdf_provincie['Perioden'] == selected_year_1) & (gdf_provincie['GebruikVanGeweld'] == selected_geweld_soort)]

        # Bereken de vmin en vmax waarden op basis van alle jaren voor de geselecteerde geweldsoort
        vmin_provincie = gdf_provincie[gdf_provincie['GebruikVanGeweld'] == selected_geweld_soort]['DI-Index'].min()
        vmax_provincie = gdf_provincie[gdf_provincie['GebruikVanGeweld'] == selected_geweld_soort]['DI-Index'].max()

        # Plot de provincies op basis van de DI-Index met een aangepaste range
        fig_provincie, ax_provincie = plt.subplots(1, 1, figsize=(15, 12))
        gdf_selected_year_diefstal_provincie.plot(column='DI-Index', linewidth=0.8, ax=ax_provincie, edgecolor='0.8', legend=True, vmin=vmin_provincie, vmax=vmax_provincie)
        ax_provincie.axis('off')  # Optioneel: uitschakelen van de assen
        # Voeg een titel toe aan de colorbar van de heatmap
        colorbar = ax_provincie.get_figure().get_axes()[1]  # Krijg de colorbar van de heatmap
        colorbar.set_title('DI-Index', fontsize=14)  # Voeg een titel toe

        # Toon de plot in Streamlit voor gdf_provincie
        st.pyplot(fig_provincie)


# In[ ]:





# In[ ]:




