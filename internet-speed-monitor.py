  
"""
Name:           internet_speed_monitor.py
Author:         Matthew Fenlon
Description:    Monitor Internet connectivity and speed using speedtest-cli
                and record uploand and download speed (bit/s), downtime time and duration to csv files.

How to run:		To run this program from the Console/Terminal, type:
					python internet_speed_monitor.py

Date:           2020.11.11
Version:        1.0

Requires speedtest-cli https://github.com/sivel/speedtest-cli
Contains modified code from https://github.com/kennethmitra/monitor-internet-connection
"""
import asyncio
import os
import re
import subprocess
import time
import json
import shlex
import time
import datetime
import socket
import signal
import sys
import pandas as pd


""" Constants """
speed_polling_freq = 900 #Seconds to check for internet speed
downtime_polling_freq = 1 #Seconds to check for internet connection
server_id = "20229" #Id of server to test against. Get server id by running speedtest-cli --list
verbose = False #Set true for verbose output
live_data = True #Set true to run live speedtest. Set false to use static string.
speed_test_data_file = "speed_data.csv" #Use literal path
down_time_data_file = "downtime_data.csv" #Use literal path

def verify_install(verbose=False):
    """ Check if speedtest-cli is installed and accessable.
    Input Parameters:
        
    Returns:
        True (Boolean) if speedtest-cli is accessable.
        False (Boolean) if speedtest-cli in not accessable.
    """
    try:
        cmd = "speedtest-cli --version"
        version = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE).stdout.read().decode('utf-8')
        if verbose:
            print("speedtest-cli installed\nVersion Information:\n",version)
        return True
    except OSError:
        #speedtest-cli not available, print error message
        print("Error: speedtest-cli not found or not installed.")
        print("If you have pip installed try the command:\n pip install speedtest-cli")
        print("For other install options, visit https://github.com/sivel/speedtest-cli")
        exit(1)

async def speedtest_json(server=False, live_data=True, verbose=False):
    """ Returns a json dataset of speed test paremeters. 
        Performs a speedtest using speedtest-cli or
        test data can be returned to save time for testing.

    Input Parameters:
        verbose: (Boolean) Output json string.
        server: (string) ID of the server to run the test on.
        test_data: (Boolean) return simulated data.
    Returns:
        json data object
    """

    #Return test data
    if live_data == False:
        #"timestamp": "2020-10-19T23:28:34.596717Z",
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        return json.loads('{"download": 275293375.450059, "upload": 86721370.01467983, "ping": 4.749, "server": {"url": "http://speedtest.washington-dc.xiber.net:8080/speedtest/upload.php", "lat": "38.8904", "lon": "-77.0320", "name": "Washington, DC", "country": "United States", "cc": "US", "sponsor": "Xiber LLC", "id": "20229", "host": "speedtest.washington-dc.xiber.net:8080", "d": 14.526529376114068, "latency": 4.749}, "timestamp": "'+timestamp+'", "bytes_sent": 108486656, "bytes_received": 344414872, "share": null, "client": {"ip": "129.2.124.17", "lat": "38.9965", "lon": "-76.934", "isp": "University of Maryland", "isprating": "3.7", "rating": "0", "ispdlavg": "0", "ispulavg": "0", "loggedin": "0", "country": "US"}}')
    else:    
        try:
            #Perform speed test
            test_cmd= "speedtest-cli --json"
            #If server id is supplied, use specified server
            if server:
                test_cmd += " --server "+server
            if verbose:
                print("Command: "+test_cmd)
            response = subprocess.Popen(shlex.split(test_cmd), stdout=subprocess.PIPE).stdout.read().decode('utf-8')

            if is_valid_json(response):
                json_response = json.loads(response)
                if verbose:
                    print(json.dumps(json_response, sort_keys=True, indent=4))

                return json_response
            else:
                print("speedtest-cli response was not a valid json format")
                return None
        except OSError:
            #speedtest-cli command failed, print error message
            print("Error: running speedtest-cli.")
            exit(1)

def is_internet_alive(host="8.8.8.8", port=53, timeout=3):
    """ Source: https://github.com/kennethmitra/monitor-internet-connection
        Check if Internet Connection is alive and external IP address is reachable.
    Input Parameters:
        host: (string) 8.8.8.8 (google-public-dns-a.google.com)
        port: (integer) (53/tcp DNS Service).
        timeout: (float) timeout in seconds.
    Returns:
        True (Boolean) if external IP address is reachable.
        False (Boolean) if external IP address is unreachable.
    """

    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
    except OSError as error:
        # print(error.strerror)
        return False
    else:
        s.close()
        return True

def calc_time_diff(start, end):
    """ Source: https://github.com/kennethmitra/monitor-internet-connection
        Calculate duration between two times and return as HH:MM:SS
    Input Params:
        start and end times
        both datetime objects created from datetime.datetime.now()
    Returns:
        The duration (string) in the form HH:MM:SS
    """

    time_difference = end - start
    secs = str(time_difference.total_seconds())
    return str(datetime.timedelta(seconds=float(secs))).split(".")[0]

def signal_handler(signal_received, frame):
    """ Source: https://github.com/kennethmitra/monitor-internet-connection
        Capture Ctrl-C (or SIGINT) and exit the program gracefully. 
    Input Params:
        signal_received (integer) is the signal number captured and received.
        frame (frame object) is the current stack frame.
    Returns:
        This method exits the program, thus nothing is returned.
    """

    # Display exit message to console and record in log file.
    exit_time = datetime.datetime.now()
    exit_msg = "\nMonitoring Internet Connection stopped at : " + exit_time.strftime("%Y-%m-%d %H:%M:%S")
    print(exit_msg)
    sys.exit()

async def internet_downtime(fail_time):
    """ Source: https://github.com/kennethmitra/monitor-internet-connection
        Calculates the time internet was down
    Input Params:
        fail_time (datetime object) Time internet connection of downtime detected.
    Returns:
    """
    msg = "\tInternet Connection unavailable at : \t" + str(fail_time).split(".")[0]
    print(msg)

    # Check every 1 second to see if internet connectivity restored.
    counter = 0
    while not is_internet_alive():
        await asyncio.sleep(1)
        counter += 1
        # For each minute of downtime, log it.
        # The one-minute logs can be useful as a proxy to indicate whether the computer lost power,
        # or just the internet connection was unavailable.
        if counter >= 60:
            counter = 0
            now = datetime.datetime.now()
            msg = "\tInternet Connection still unavailable at : \t" + str(now).split('.')[0]
            print(msg)                    

    # Record observed time when internet connectivity restored.
    restore_time = datetime.datetime.now()
    restore_msg = "\tInternet Connection restored at    : \t" + str(restore_time).split('.')[0]

    # Calculate the total duration of the downtime
    downtime_duration = calc_time_diff(fail_time, restore_time)
    duration_msg = "\tThe duration of the downtime was   : \t" + downtime_duration

    # Display restoration message to console and record in log file.
    if downtime_duration != "datetime":
        print(restore_msg)
        print(duration_msg)

    return restore_time,downtime_duration


async def write_csv(dataframe, data_file):
    """ Write a pandas datafreme to a csv file 
    Input Params:
        dataframe (dataframe object) Pandas dataframe to write to file.
        data_file (string) Path and name of file to write or append.
    Returns:
        Write success (Boolean) 
    """
    try:
        if os.path.exists(data_file):
            #If file exists, append data
            print('Appending to file: ', data_file )
            dataframe.to_csv(data_file, mode='a', header=False, index=False)
        else:
            #Create a new file and write header
            print('Creating new file: ', data_file )
            dataframe.to_csv(data_file, header=True, index=False)
    except OSError as error:
        return False
    else:
        return True

def is_valid_json(json_response):
    """ Validate if a response is a valid json format 
    Input Params:
        json_response (string)
    Returns:
        String is in json format (Boolean) 
    """
    try:
        json_object = json.loads(json_response)
        if verbose:
            print(json.dumps(json_object, sort_keys=True, indent=4))
    except ValueError as e:
        return False
    return True

async def speed_test(data_file):
    """ Run a speed test every period defined by speed_polling_freq
        Writes data to a csv file
    Input Params:
        data_file (string) Path and name of file to write or append.
    Returns:
    """
    #Speedtest loop
    while True:
        if is_internet_alive():
            json_response = await speedtest_json(live_data=live_data, server=server_id, verbose=verbose)
            if json_response is not None:
                df = pd.json_normalize(json_response)

                if verbose:
                    print(df)
                speed_test_write_task = asyncio.create_task(write_csv(df, data_file))
            
        await asyncio.sleep(speed_polling_freq)


async def down_time(data_file):
    """ Run a internet uptime test every second
        Writes data to a csv file
    Input Params:
        data_file (string) Path and name of file to write or append.
    Returns:
    """
    start_time = datetime.datetime.now()
    print("Monitoring Internet Connection started at : " + start_time.strftime("%Y-%m-%d %H:%M:%S"))

    while True:
        if not is_internet_alive():
            # Record observed time when internet connectivity fails.
            fail_time = datetime.datetime.now()
            uptime_duration = calc_time_diff(start_time, fail_time)

            restore_time,downtime_duration = await internet_downtime(fail_time)
            if downtime_duration != "datetime":

                dictionaryData = {
                    'Start_Time' : [start_time],
                    'Fail_Time' : [fail_time],
                    'Restore_time' : [restore_time],
                    'Downtime_Duration' : [downtime_duration],
                    'Uptime_Duration' : [uptime_duration]
                }
                start_time = restore_time

                df = pd.DataFrame(dictionaryData)
                if verbose:
                    print(df)
                down_time_write_task = asyncio.create_task(write_csv(df, data_file))

        await asyncio.sleep(downtime_polling_freq)

async def main():
    """ Monitor internet Uptime and Speed
    Input Params:
    Returns:
    """
    #Verify if necessary items are available
    verify_install()

    #Capture the Ctrl-C (or SIGINT) signal to permit the program to exit gracefully.
    signal.signal(signal.SIGINT, signal_handler)

    await asyncio.gather(
        down_time(down_time_data_file),
        speed_test(speed_test_data_file)
    )


asyncio.run(main())
