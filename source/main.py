###############################################################################
#
#   Main application for trash container LEDs
#
###############################################################################
#
#   2024 - February - Henk-Johan
#           - first version
#
###############################################################################

import time
import network
import socket
import struct
import requests
from machine import Pin, Timer

import config # import the config file


def set_time():
    '''
        Function to get the time from ntp.org and to set the sytem timer correct
    '''
    try:
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        addr = socket.getaddrinfo(config.time_host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(2)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        finally:
            s.close()
        val = struct.unpack("!I", msg[40:44])[0]
        t = val - config.time_NTP_DELTA    
        tm = time.gmtime(t)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
        return 0
    except:
        return -1


def get_pickup_dates(company_code, address_id, start_date, end_date):
    '''
        Function to get the pickup dates for the containers for a certain time period
        company_code : unique code for the company picking up containers in the region
        address_id   : generated unique id for a certain address
        start_date   : string YYYY-MM-DD
        end_date     : string YYYY-MM-DD
    '''
    try:
        data = f"companyCode={company_code}&uniqueAddressID={address_id}&startDate={start_date}&endDate={end_date}"
        url = "https://twentemilieuapi.ximmio.com/api/GetCalendar"
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        res = requests.post(url, headers=headers, data=data, timeout=5)
        return res.json()["dataList"]
    except:
        return []


def get_bin_color(type_number):
    '''
        based on container typ id return the correct color
    '''
    bin_color = 'unkown'
    if type_number == 0: # gray bin
        bin_color = 'GRAY'
    if type_number == 1: # green bin
        bin_color = 'GREEN'
    if type_number == 2: # blue bin
        bin_color = 'BLUE'
    if type_number == 6: # tree
        bin_color = 'RED'
    if type_number == 10: # orange bin
        bin_color = 'ORANGE'
    return bin_color


def tick_system(timer):
    global systemled
    systemled.toggle()

def tick_gray(timer):
    global container_gray
    container_gray.toggle()

def tick_green(timer):
    global container_green
    container_green.toggle()

def tick_blue(timer):
    global container_blue
    container_blue.toggle()

def tick_orange(timer):
    global container_orange
    container_orange.toggle()

def tick_tree(timer):
    global container_tree
    container_tree.toggle()


def make_date_string(timedata):
    '''
        prepare formatted date string for the API YYYY-MM-DD
    '''
    date_string = str(timedata[0])
    date_string += '-'
    if len(str(timedata[1])) == 1:
        date_string += '0' + str(timedata[1])
    else:
        date_string += str(timedata[1])
    date_string += '-'
    if len(str(timedata[2])) == 1:
        date_string += '0' + str(timedata[2])
    else:
        date_string += str(timedata[2])
    return date_string    


def trash_types_to_day_colors(trash_types):
    '''
        take the trash type list and break it down into a container color for today and tomorrow
    '''
    light_today = ''
    light_tomorrow = ''
    if len(trash_types) > 0:    
        for type in trash_types:
            print('-'*80)
            type_number = type["pickupType"]
            type_text = type["_pickupTypeText"]
            datelist = type["pickupDates"]
            print(type_text, type_number, get_bin_color(type_number) )
            if len(datelist) > 0:
                for dateitem in datelist:
                    if len(dateitem) < 10:
                        continue
                    rawdate = dateitem.split('T')[0]
                    print(dateitem, rawdate)
                    if str(rawdate) == str(start_date):
                        light_today = get_bin_color(type_number)
                    if str(rawdate) == str(end_date):
                        light_tomorrow = get_bin_color(type_number)
    return [light_today, light_tomorrow]


def disable_all_leds():
    '''
        diable all solid and flashing container leds
    '''
    container_gray.value(0)
    container_green.value(0)
    container_blue.value(0)
    container_orange.value(0)
    container_tree.value(0)
    tim_gray.deinit()
    tim_green.deinit()
    tim_blue.deinit()
    tim_orange.deinit()
    tim_tree.deinit()
    return 0    


def set_led_today(light_today):
    '''
        the led for today will be solid
    '''
    if len(light_today) > 0:
        print(light_today, 'will be on solid for pickup today')
        if light_today == 'GRAY':
            container_gray.value(1)
        if light_today == 'GREEN':
            container_green.value(1)
        if light_today == 'BLUE':
            container_blue.value(1)
        if light_today == 'ORANGE':
            container_orange.value(1)
        if light_today == 'RED':
            container_tree.value(1)
    return 0


def set_led_tomorrow(light_tomorrow):
    '''
        the led for tomorrow will be flashing
    '''
    if len(light_tomorrow) > 0:
        print(light_tomorrow, 'will be flashing for pickup tomorrow')
        if light_tomorrow == 'GRAY':
            tim_gray.init(freq=1, mode=Timer.PERIODIC, callback=tick_gray)
        if light_tomorrow == 'GREEN':
            tim_green.init(freq=1, mode=Timer.PERIODIC, callback=tick_green)
        if light_tomorrow == 'BLUE':
            tim_blue.init(freq=1, mode=Timer.PERIODIC, callback=tick_blue)
        if light_tomorrow == 'ORANGE':
            tim_orange.init(freq=1, mode=Timer.PERIODIC, callback=tick_orange)
        if light_tomorrow == 'RED':
            tim_tree.init(freq=1, mode=Timer.PERIODIC, callback=tick_tree)
    return 0    

#-------------------------------------
# prepare LEDs
systemled        = Pin("LED", Pin.OUT)
container_gray   = Pin(20, Pin.OUT)
container_green  = Pin(19, Pin.OUT)
container_blue   = Pin(18, Pin.OUT)
container_orange = Pin(17, Pin.OUT)
container_tree   = Pin(16, Pin.OUT)
# prepare timers
tim_system = Timer()
tim_gray   = Timer()
tim_green  = Timer()
tim_blue   = Timer()
tim_orange = Timer()
tim_tree   = Timer()

#-------------------------------------
# indicate fast blinking as booting
tim_system.init(freq=10, mode=Timer.PERIODIC, callback=tick_system)

#-------------------------------------
# connect wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.wifi_ssid, config.wifi_password)
# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)
    
# Handle connection error
if wlan.status() != 3:
    tim_system.init(freq=10, mode=Timer.PERIODIC, callback=tick_system)
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )
    
    
while True:    
    
    if set_time() < 0:
        tim_system.init(freq=5, mode=Timer.PERIODIC, callback=tick_system)
    else:        
        tim_system.init(freq=1, mode=Timer.PERIODIC, callback=tick_system)
        
    print(time.localtime())
    end_time = time.gmtime(time.time() + 60*60*24)
    print(end_time)

    start_date = make_date_string(time.localtime())
    end_date   = make_date_string(end_time)
    #start_date = '2024-01-08' # for debug
    #end_date = '2024-01-09' # for debug
    
    # print the dates for debug
    print(start_date, end_date)
    # get the trash_types from the API for this timeframe
    trash_types = get_pickup_dates(config.trash_company_code, config.trash_address_id, start_date, end_date)
    # get the 
    [light_today, light_tomorrow] = trash_types_to_day_colors(trash_types)
    
    print('-'*80)
    # disable all leds, then set them for today and tomorrow
    disable_all_leds()
    set_led_today(light_today)
    set_led_tomorrow(light_tomorrow)
    print('-'*80)
    
    # check the wifi status
    if wlan.status() != 3:
        print("trying to reconnect...")
        wlan.disconnect()
        wlan.connect(config.wifi_ssid, config.wifi_password)
        if wlan.status() == 3:
            print('wifi reconnected')
        else:
            print('wifi reconnect failed')
    
    # sleep for an hour            
    time.sleep(60*60) 

