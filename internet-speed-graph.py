import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import LHD
from matplotlib import cm
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates
import datetime
import json
import math


def bits_to_megabytes(bits):
    """ Validate if a response is a valid json format 
    Input Params:
        bits
    Returns:
        String is in json format (Boolean) 
    """
    
    return bits*0.000000125

#Print script full path for HW submission
print("Script full path: ",os.path.abspath(__file__))

#Define constants
speed_test_data_file = 'speed_data_current.csv'
down_time_data_file = 'downtime_data_current.csv'

#Import the data using pandas
df_speedtest = pd.read_csv(speed_test_data_file,
        delim_whitespace=False,

    )

#Unit conversions
df_speedtest['download_Mbps'] = df_speedtest['download']*0.000001 
df_speedtest['upload_Mbps'] = df_speedtest['upload']*0.000001 
df_speedtest['ping_ms'] = df_speedtest['ping']*0.0001 

downtime_columns_dates=['Start_Time','Fail_Time','Restore_time','Uptime_Duration']
df_downtime = pd.read_csv(down_time_data_file,
        delim_whitespace=False,
        parse_dates=downtime_columns_dates

    )

#Date conversions
df_speedtest['datetime_timestamp'] = pd.to_datetime(df_speedtest['timestamp'])
df_speedtest['date2num'] = mdates.date2num(df_speedtest['datetime_timestamp'])
df_downtime['date2num'] = mdates.date2num(df_downtime['Fail_Time'])
df_downtime['Downtime Minutes'] = pd.to_timedelta(df_downtime['Downtime_Duration']).dt.total_seconds()/60

#Get list of unique months
months = df_speedtest['datetime_timestamp'].dt.strftime("%m/%Y").unique().tolist()
print("The data set contains data from:",  months)

#Max and min values
dictionaryData = {
                    'Max Ping' : [df_speedtest['ping_ms'].max()],
                    'Min Ping' : [df_speedtest['ping_ms'].min()],
                    'Max Download' : [df_speedtest['download_Mbps'].max()],
                    'Min Download' : [df_speedtest['download_Mbps'].min()],
                    'Max Upload' : [df_speedtest['upload_Mbps'].max()],
                    'Min Upload' : [df_speedtest['upload_Mbps'].min()],
                    'Total Downtime' : [df_downtime['Downtime Minutes'].sum()]
                }
print(json.dumps(dictionaryData, indent=4))

y_max_Mbsp = math.ceil(max(df_speedtest['download_Mbps'].max(),df_speedtest['upload_Mbps'].max())*1.10)
y_min_Mbsp = math.floor(min(df_speedtest['download_Mbps'].min(),df_speedtest['upload_Mbps'].min())*.90)
print(y_min_Mbsp, y_max_Mbsp)
#Loop each month found
for month in months:
    print("Processing ", month)
    plt.close("all")

    current_date_time_obj = datetime.datetime.strptime(month, "%m/%Y")
    p = pd.Period(month)
    days_in_month = pd.date_range(
        start=current_date_time_obj.strftime("%Y-%m-%d"), 
        periods=p.days_in_month,
        freq='D')
    
    #Extract speedtest data for month being processed
    mask = (df_speedtest['datetime_timestamp'].dt.year == current_date_time_obj.year) & (df_speedtest['datetime_timestamp'].dt.month == current_date_time_obj.month)
    df_speedtest_month = df_speedtest.loc[mask]
    #print( df_speedtest_month,"\n")

    #Extract downtime data for month being processed
    mask = (df_downtime['Fail_Time'].dt.year == current_date_time_obj.year) & (df_downtime['Fail_Time'].dt.month == current_date_time_obj.month)
    df_downtime_month = df_downtime.loc[mask]
  


    #Monthly max and min values
    dictionaryData = {
                    'Max Ping' : [df_speedtest_month['ping_ms'].max()],
                    'Min Ping' : [df_speedtest_month['ping_ms'].min()],
                    'Max Download' : [df_speedtest_month['download_Mbps'].max()],
                    'Min Download' : [df_speedtest_month['download_Mbps'].min()],
                    'Max Upload' : [df_speedtest_month['upload_Mbps'].max()],
                    'Min Upload' : [df_speedtest_month['upload_Mbps'].min()],
                    'Total Downtime' : [df_downtime_month['Downtime Minutes'].sum()]
                }
    print(json.dumps(dictionaryData, indent=4))


    #fig1 = plt.figure(figsize=[9,9])
    #fig1, (ax_speed,ax_ping,ax_downtime) = plt.subplots(3,1)
    fig1, (ax_speed,ax_ping,ax_downtime) = plt.subplots(3,1, sharex='col',gridspec_kw={'height_ratios': [3, 2, 1]})


    fig1.suptitle('Internet Speed and Downtime for '+ current_date_time_obj.strftime("%B %Y"))

    # we are plotting a 6row 1 column grid
    # ax_speed = plt.subplot2grid((9,1),(0,0), rowspan=3)
    # ax_ping = plt.subplot2grid((9,1),(3,0), rowspan=3)
    # ax_downtime = plt.subplot2grid((9,1),(6,0), rowspan=3)


    ax_downtime.set_xlim(days_in_month[0],days_in_month[-1])
    ax_downtime.xaxis.set( 
    major_locator = mdates.AutoDateLocator(minticks = p.days_in_month, 
                                           maxticks = p.days_in_month), 
    ) 
    locator = mdates.AutoDateLocator() 
    formatter = mdates.ConciseDateFormatter(locator) 
    ax_downtime.xaxis.set_major_locator(locator) 
    ax_downtime.xaxis.set_major_formatter(formatter) 
    #Rotate Labels
    for label in ax_downtime.get_xticklabels():
        label.set_rotation(45)
        label.set_horizontalalignment('right')

    ax_speed.scatter(
        df_speedtest_month['date2num'],
        df_speedtest_month['download_Mbps'], 
        label='Download (Mbps)',
        marker='v',
        alpha=.5,
        vmin=y_min_Mbsp, 
        vmax=y_max_Mbsp,
        c=df_speedtest_month['download_Mbps'], 
        cmap=cm.jet_r,
        s=10,
        
    )

    ax_speed.scatter(
        df_speedtest_month['date2num'],
        df_speedtest_month['upload_Mbps'], 
        label='Upload (Mbps)',
        marker='^',
        alpha=.5,
        vmin=y_min_Mbsp, 
        vmax=y_max_Mbsp,
        c=df_speedtest_month['download_Mbps'], 
        cmap=cm.jet_r,
        s=10,
    )

    ax_speed.set_ylim(y_min_Mbsp, y_max_Mbsp)
    ax_speed.set_ylabel('Megabits per second')
    ax_speed.legend()

    scatter_plot = ax_ping.scatter(
        df_speedtest_month['date2num'],
        df_speedtest_month['ping'],     
        label='Ping (ms)',
        marker='d',
        alpha=.5,
        vmin=0, 
        vmax=100,
        c=df_speedtest_month['ping'], 
        cmap=cm.jet,
        s=10,
    )
    ax_ping.set_ylim(0, 60)
    ax_ping.set_ylabel('milliseconds')
    ax_ping.legend()

    ax_downtime.scatter(
        df_downtime_month['date2num'],
        df_downtime_month['Downtime Minutes'], 
        label='Downtime Duration (minutes)',
        marker='x',
        alpha=.5, 
        c='red',
        s=10,
    )

    ax_downtime.set_ylabel('Minutes')
    ax_downtime.legend()


    plt.show()
    plt.tight_layout()
