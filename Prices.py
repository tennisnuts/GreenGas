# Author: Oliver Nunn
# Date: 02/02/2020
# Project: Green Gas - 4th Year Project

# This is a Python file to get the prices from Octopus Energy for the dates specified

# elec_prices(day) returns the price of electricity for the 24 hrs on a half hour basis. the unit of measurement is in pence per kWh and it is for the year 2020

import requests
import json
import numpy as np
import datetime
import pandas as pd

# method to get the date string from the day in the year
def get_date_wanted(day, year):
    
    start_dt = datetime.datetime(year,1,1)
    change_to_date = datetime.timedelta(days = (day-1))
    date = start_dt + change_to_date
    rand = date.strftime("%d/%m/%Y")
    
    return rand

#  Method to get the half-hourly electricity prices from the start date to the end date
def exact_elec_prices(start_day, start_month, start_year, end_day, end_month, end_year):

    # start point
    start_year = start_year
    start_month = f"{int(start_month):02d}"
    start_day = f"{int(start_day):02d}"
    start_time = '00:30'

    # end point
    end_year = end_year
    end_month = f"{int(end_month):02d}"
    end_day = f"{int(end_day):02d}"
    end_time = '00:30'

    start_point = start_year + '-' + start_month + '-' + start_day +'T' + start_time + 'Z'
    end_point = end_year + '-' + end_month + '-' + end_day +'T' + end_time + 'Z'

    response = requests.get('https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-C/standard-unit-rates/?period_from=' + start_point + '&period_to=' + end_point)

    response = response.json()

    if len(response['results']) == 48:
        elec_price = np.zeros(48)
        for n in range(48):
            elec_price[n] = response['results'][n]['value_inc_vat']
        elec_price = elec_price[::-1]   # reversing the array as thats the format the data is in
#         This data is in pence per kWh
        return elec_price
    else:
        return 'Not enough data for 24 Hours'
    



# simplified version above where only the day is specified     
def elec_prices(day):
    year = 2020
    
    # code to get the start date from the day in the year
    start_date = get_date_wanted(day, year)
    start_day, start_month, start_year = start_date.split('/')
    
    # code to get the end date from the day in the year
    end_date = get_date_wanted(day+1, year)
    end_day, end_month, end_year = end_date.split('/')
    
    prices = exact_elec_prices(start_day, start_month, start_year, end_day, end_month, end_year)
    
    return prices


# the same as elec_prices however this function gets its data from 'Data/' and not from octopus directly
def elec_prices_data(day):
    
    data = pd.read_csv('Data/agileprices2020.csv')
    temp = data.iloc[day-1].values
    temp = temp[1::]
    
    return temp