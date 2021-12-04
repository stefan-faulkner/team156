## Import Libraries

import datetime as dt
import pandas as pd
import numpy as np
from urllib.request import urlopen
import json
import requests 

## plotly
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

## dash libraries
#from jupyter_dash import JupyterDash 
import dash
#import dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
#from dash.dependencies import Output, Input
from dash import dcc
from dash import html


#tabtitle = 'app'

# Set up application and server 

app = dash.Dash(__name__)
server = app.server


## read in csv as df
url_1 = 'https://github.com/stefan-faulkner/team156data/blob/master/all_zips_forecast_method1.csv?raw=true'

df = pd.read_csv(url_1,dtype = {'Zipcode': str}).rename(columns={"1Yr-ROI":"1 Year ROI","3Yr-ROI":"3 Year ROI","5Yr-ROI":"5 Year ROI"})


## zip code & county data, from https://simplemaps.com/data/us-zips
url_2 = 'https://github.com/stefan-faulkner/team156data/blob/master/uszips.csv?raw=true'

counties_df = pd.read_csv(url_2, dtype = {'zip': str})

#Read in Json File
url_3 = 'https://github.com/stefan-faulkner/team156data/blob/master/ZCTA510_simplified.json?raw=true'
resp = requests.get(url_3)
zipCodes = json.loads(resp.text)


## merge county df columns of interest with df
df = df.merge(counties_df[['zip','lat','lng','city','state_id','state_name','county_name','county_fips']], left_on = 'Zipcode', right_on='zip', how='inner')


## counties-fips json data
## used the same counties source as in this reference: https://plotly.com/python/choropleth-maps/
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

## any of the FIPS in the df that should have a leading 0 don't have it there 
## it was easier to truncate a leading zero from the FIPS json than add one to the df FIPS data

adj_features = []
for feature in counties['features']:
    if feature['id'][0] == '0':
        feature['id'] = feature['id'][1:]
    adj_features.append(feature)

adj_counties = {'type': 'FeatureCollection', 'features': adj_features}

####FIRST FIGURE

## choropleth reference: https://plotly.com/python/choropleth-maps/
## more choropleth help: https://plotly.com/python/reference/choropleth/
## slider reference: https://support.sisense.com/kb/en/article/plotly-choropleth-with-slider-map-charts-over-time

data_slider = []
steps = []
years = ['1 Year ROI','3 Year ROI','5 Year ROI']

df['text'] = '1 Year ROI' + df['1 Year ROI'].astype(str) + '<br>' + '3 Year ROI' + df['3 Year ROI'].astype(str) + '<br>' + '5 Year ROI' + df['5 Year ROI'].astype(str)

# Create Buttons
# Style Buttons
def createColorButton(color):
    returnThis = dict(
                    args=["colorscale", color],
                    label=color,
                    method="restyle"
                )
    return returnThis

colorList = ["RdBu", "Blues", "Greens", "Cividis", "Viridis", "spectral", "thermal"]

## create data slider
for i,year in enumerate(years):
    ##  create working df for each year
    df_segmented_county = df[['county_fips',year, 'text']]
    df_segmented =  df[['Zipcode',year, 'text']]

    data_county = dict(
                        type='choropleth',
                        name = year + ' County Level',
                        text = df_segmented_county['text'],
                        geojson=adj_counties,
                        locations = df_segmented_county['county_fips'],
                        z=df_segmented_county[year].astype(float),
                        zmin = -1,
                        zmax = 1,
                        colorscale = "RdBu",
                        colorbar= {'title':'Forecasted ROI'})

    ## append each year's dict to slider list
    data_slider.append(data_county)

    ## add zip code here
    data_zip = dict(
                        type='choropleth',
                        name = year + ' ZIP Code Level',
                        text = df_segmented['text'],
                        geojson=zipCodes,
                        featureidkey='properties.ZCTA5CE10',
                        colorscale="RdBu",
                        zmin = -1,
                        zmax = 1,
                        locations = df_segmented['Zipcode'],
                        z = df_segmented[year].astype(float),
                        colorbar= {'title':'Forecasted ROI'}
    )

    data_slider.append(data_zip)
    
    ## create the slider steps
    step = dict(method='restyle',args=['visible', [False] * (2*len(years))], label='ROI: {} - County Level'.format(year))
    step['args'][1][2*i] = True # The first slot of each step has the normal choropleth
    steps.append(step)

    step2 = dict(method='restyle',args=['visible', [False] * (2*len(years))], label='ROI: {} - ZIP Code Level'.format(year))
    step2['args'][1][2*i + 1] = True # The second slot of each step has the mapbox 
    steps.append(step2)



## create slider
sliders = [dict(active=0, pad={"t": 0}, steps=steps)]

buttonLoc= 1.1

## graph layout details
layout1 = dict(title ='Projected ROI Over Time By County and ZIP Code', geo=dict(scope='usa',
                       projection={'type': 'albers usa'}),
              sliders=sliders, 
              height = 800,
              width = 1400,
              margin = dict(l=100),
              updatemenus = [dict(y=1.1,
                                    x=buttonLoc,
                                    xanchor='right',
                                    yanchor='top',
                                    buttons=[createColorButton(color) for color in colorList])],
              annotations = [dict(text="Colorscale", x=buttonLoc-0.1, y=1.09, align="left", showarrow=False)]
              )

## create figure
fig1 = dict(data=data_slider, layout=layout1)



#RGB COLOURS --> https://htmlcolorcodes.com/

app.layout = html.Div([
html.Div([
        html.Div([    # Feel free to make any changes to the colour or title as the team sees fit 
                html.H1('Automated Real Estate Appraisal Visualization Tool', style = {'textAlign': 'center',
                                                                                 'color': 'black',
                                                                                 'fontSize': '34px',
                                                                                 'padding-top': '2px'},
                        ),
                html.P('By team156', style = {'textAlign': 'center',
                                                      'color': 'black',
                                                      'fontSize': '22px'},
                    )
                ],
            style = {'backgroundColor': '#85929E',
                     'height': '150px',
                     'display': 'flex',
                     'flexDirection': 'column',
                     'justifyContent': 'center'}
            ) ])
    , html.Div([dcc.Graph(figure=fig1,style={'justifyContent': 'center'})]) #wanted to be fully centered but not working 
])





if __name__ == '__main__':
    app.run_server()
    
    
    
    