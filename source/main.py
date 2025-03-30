###############################################################################
#
#   Main application for trash container LEDs
#
###############################################################################
#
#   2024 - February - Henk-Johan
#           - first version
#   2025 - March - Henk-Johan
#           - added RD4 support
#           - code cleanup
###############################################################################
import time
import socket
import struct
import requests

import os 

import config # import the config file

print('\n')
print('#'*80)
print('PI pico trash container signal tower')
print('Assuming we run on   : ', config.run_system)
print('Trash company to use : ', config.trash_company)
print('#'*80)

# check if we are running on a computer for debug or on the real hardware
platform = config.run_system

if platform == 'pico':
    from machine import Pin, Timer
    import network



#------------------------------------------------------------------------------
def set_time():
    '''
        Function to get the time from ntp.org and to set the sytem timer correct on the PI pico
    '''
    last_status = ''
    try:
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        last_status = 'NTP : get address'
        addr = socket.getaddrinfo(config.time_host, 123)[0][-1]
        last_status = 'NTP : get socket'
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(5)
            last_status = 'NTP : waiting for response after query'
            res = s.sendto(NTP_QUERY, addr)
            last_status = 'NTP : receiving message'
            msg = s.recv(48)
        finally:
            s.close()
        last_status = 'NTP : unpacking message'
        val = struct.unpack("!I", msg[40:44])[0]
        last_status = 'NTP : calculating time delta'
        t = val - config.time_NTP_DELTA
        last_status = 'NTP : building time tuples'
        tm = time.gmtime(t)
        last_status = 'NTP : setting machine time'
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
        last_status = 'NTP : system time updated OK'
        return 0
    except:
        print('NTP : error :', last_status)
        return -1


#------------------------------------------------------------------------------
def get_pickup_dates_twente(company_code, address_id, start_date, end_date):
    '''
        Function to get the pickup dates for the containers for a certain time period in Twente
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


#------------------------------------------------------------------------------
def get_pickup_dates_rd4(year, month, postal_code, house_number):
    '''
        Function to get the pickup dates for the containers for a certain time period in RD4 covered region
        year            : the year for which to get the dates
        month           : the month for which to get the dates
        postal_code     : the postal code of the address
        house_number    : the house number of the address
        https://data.rd4.nl/api/v1/waste-calendar/?year=2025&postal_code=6269NR&house_number=10&month=4
    '''
    try:
        url = f"https://data.rd4.nl/api/v1/waste-calendar/?year={year}&postal_code={postal_code}&house_number={house_number}&month={month}"
        res = requests.get(url, timeout=5)
        return res.json()["data"]
    except:
        return []



#------------------------------------------------------------------------------
def get_bin_color_twente(type_number):
    '''
        mapping of the trash type number to container and LED color
    '''
    bin_color = 'unkown'
    if type_number == 0:    # gray bin
        bin_color = 'GRAY'
    if type_number == 1:    # green bin
        bin_color = 'GREEN'
    if type_number == 2:    # blue bin
        bin_color = 'BLUE'
    if type_number == 6:    # christmas tree
        bin_color = 'RED'
    if type_number == 10:   # orange bin
        bin_color = 'ORANGE'
    return bin_color



#------------------------------------------------------------------------------
def get_bin_color_rd4(type_name):
    '''
        mapping of type name to container and LED color
    '''
    bin_color = 'unkown'
    if type_name == 'residual_waste':   # gray bin
        bin_color = 'GRAY'
    if type_name == 'gft':              # green bin
        bin_color = 'GREEN'
    if type_name == 'paper':            # blue bin
        bin_color = 'BLUE'
    # if type_name == 'pruning_waste':    # spring and autumn cuttings of trees and shrubs
        # bin_color = 'RED'
    if type_name == 'best_bag':         # books / electronics / recycle materials
        bin_color = 'RED'
    if type_name == 'pmd':              # orange bin
        bin_color = 'ORANGE'
    return bin_color



#------------------------------------------------------------------------------
def tick_system(timer):
    '''
        the system LED on the PI pico board
    '''
    global systemled
    systemled.toggle()

#------------------------------------------------------------------------------
def tick_gray(timer):
    '''
        the LED for the gray container
    '''
    global container_gray
    container_gray.toggle()

#------------------------------------------------------------------------------
def tick_green(timer):
    '''
        the LED for the green container
    '''
    global container_green
    container_green.toggle()

#------------------------------------------------------------------------------
def tick_blue(timer):
    '''
        the LED for the blue container
    '''
    global container_blue
    container_blue.toggle()

#------------------------------------------------------------------------------
def tick_orange(timer):
    '''
        the LED for the orange container
    '''
    global container_orange
    container_orange.toggle()

#------------------------------------------------------------------------------
def tick_red(timer):
    '''
        the LED for the christmas tree / best_bag
    '''
    global container_red
    container_red.toggle()



#------------------------------------------------------------------------------
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



#------------------------------------------------------------------------------
def trash_types_to_day_colors_twente(trash_types, date_today, date_tomorrow, debug=False):
    '''
        take the trash type list and break it down into a container color for today and tomorrow
    '''
    lights_today     = []
    lights_tomorrow  = []
    try:
        if len(trash_types) > 0:    
            for type in trash_types:
                if debug == True:
                    print('-'*80)
                type_number = type["pickupType"]
                # type_text = type["_pickupTypeText"]
                datelist = type["pickupDates"]
                # print(type_text, type_number, get_bin_color_twente(type_number) )
                if len(datelist) > 0:
                    for dateitem in datelist:
                        if len(dateitem) < 10:
                            continue
                        rawdate = dateitem.split('T')[0]
                        if debug == True:
                            print('Twente : ', dateitem, rawdate, type_number, get_bin_color_twente(type_number))
                        if str(rawdate) == str(date_today):
                            lights_today.append(get_bin_color_twente(type_number))
                            print('Found for today', type_number, 'light color', get_bin_color_twente(type_number))
                        if str(rawdate) == str(date_tomorrow):
                            lights_tomorrow.append(get_bin_color_twente(type_number))
                            print('Found for tomorrow', type_number, 'light color', get_bin_color_twente(type_number))
    except:
        print('Twente : error while decoding response message')
    return [lights_today, lights_tomorrow]


#------------------------------------------------------------------------------
def trash_types_to_day_colors_rd4(trash_json, date_today, date_tomorrow, debug=False):
    '''
        take the json from rd4 and check if we have bin for today or tomorrow
    '''
    lights_today     = []
    lights_tomorrow  = []    
    try:
        # split the items section out of the json return
        items = trash_json['items'][0]
        #print(items)
        if len(items) > 0:    
            for item in items:
                if debug == True:
                    print('RD4 : ', item)
                if str(item['date']) == str(date_today):
                    lights_today.append(get_bin_color_rd4(item['type']))
                    print('RD4 : Found for today', item, 'light color', get_bin_color_rd4(item['type']))
                if str(item['date']) == str(date_tomorrow):
                    lights_tomorrow.append(get_bin_color_rd4(item['type']))
                    print('RD4 : Found for tomorrow', item, 'light color', get_bin_color_rd4(item['type']))
    except:
        print('RD4 : error while decoding response message')
    return [lights_today, lights_tomorrow]




#------------------------------------------------------------------------------
def disable_all_leds():
    '''
        diable all solid and flashing container leds
    '''
    if platform == 'pico':
        container_gray.value(0)
        container_green.value(0)
        container_blue.value(0)
        container_orange.value(0)
        container_red.value(0)
        tim_gray.deinit()
        tim_green.deinit()
        tim_blue.deinit()
        tim_orange.deinit()
        tim_red.deinit()
    return 0    



#------------------------------------------------------------------------------
def set_led_today(lights_today):
    '''
        the led for today will be solid
    '''
    if len(lights_today) > 0:
        print(lights_today, 'will be on solid for pickup today')
        if platform == 'pico':
            if 'GRAY' in lights_today:
                container_gray.value(1)
            if 'GREEN' in lights_today:
                container_green.value(1)
            if 'BLUE' in lights_today:
                container_blue.value(1)
            if 'ORANGE' in lights_today:
                container_orange.value(1)
            if 'RED' in lights_today:
                container_red.value(1)
    return 0



#------------------------------------------------------------------------------
def set_led_tomorrow(lights_tomorrow):
    '''
        the led for tomorrow will be flashing
    '''
    if len(lights_tomorrow) > 0:
        print(lights_tomorrow, 'will be flashing for pickup tomorrow')
        if platform == 'pico':
            if 'GRAY' in lights_tomorrow:
                tim_gray.init(freq=1, mode=Timer.PERIODIC, callback=tick_gray)
            if 'GREEN' in lights_tomorrow:
                tim_green.init(freq=1, mode=Timer.PERIODIC, callback=tick_green)
            if 'BLUE' in lights_tomorrow:
                tim_blue.init(freq=1, mode=Timer.PERIODIC, callback=tick_blue)
            if 'ORANGE' in lights_tomorrow:
                tim_orange.init(freq=1, mode=Timer.PERIODIC, callback=tick_orange)
            if 'RED' in lights_tomorrow:
                tim_red.init(freq=1, mode=Timer.PERIODIC, callback=tick_red)
    return 0    


#------------------------------------------------------------------------------
def is_last_day_of_month(month, day):
    '''
        function to check if a certain month, day combination is the last of the month
    '''
    result = False
    # check months with 31 days
    if (day == 31) and (month in [1,3,5,7,8,10,12]):
        result = True
    # check months with 30 days
    if (day == 30) and (month in [4,6,9,11]):
        result = True
    # check February
    if (day in [28,29]) and (month == 2):
        result = True
    return result


###############################################################################
###############################################################################
###############################################################################

# MAIN SCRIPT

#------------------------------------------------------------------------------
# prepare LEDs
if platform == 'pico':
    systemled        = Pin("LED", Pin.OUT)
    container_gray   = Pin(20, Pin.OUT)
    container_green  = Pin(19, Pin.OUT)
    container_blue   = Pin(18, Pin.OUT)
    container_orange = Pin(17, Pin.OUT)
    container_red    = Pin(16, Pin.OUT)
    # prepare timers
    tim_system = Timer()
    tim_gray   = Timer()
    tim_green  = Timer()
    tim_blue   = Timer()
    tim_orange = Timer()
    tim_red    = Timer()


#------------------------------------------------------------------------------
# indicate fast blinking as booting
if platform == 'pico':
    tim_system.init(freq=10, mode=Timer.PERIODIC, callback=tick_system)


#------------------------------------------------------------------------------
# connect wifi
wifi_status = True
if platform == 'pico':
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.wifi_ssid, config.wifi_password)
    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('WIFI : waiting for connection...')
        time.sleep(1)
    # Handle connection error
    if wlan.status() != 3:
        tim_system.init(freq=10, mode=Timer.PERIODIC, callback=tick_system)
        wifi_status = False
        raise RuntimeError('WIFI : network connection failed')
    else:
        print('WIFI : connected')
        status = wlan.ifconfig()
        print( 'WIFI : ip = ' + status[0] )



###############################################################################
light_today     = ''
light_tomorrow  = ''
first_start     = True
# main script    
while True:    
    print('-'*80)

    print(machine.RTC().datetime())

    #--------------------------------------------------------------------------
    # build date strings for today and tomorrow
    if platform == 'pico':
        date_today      = make_date_string(machine.RTC().datetime()) # localtime is in tuples
        date_tomorrow   = make_date_string(time.gmtime(time.time() + 60*60*24)) # timetime needed as number convert with gmtime to tuples
        date_year       = machine.RTC().datetime()[0]
        date_month      = machine.RTC().datetime()[1]
        date_day        = machine.RTC().datetime()[2]
        date_hour       = machine.RTC().datetime()[4]
        date_minute     = machine.RTC().datetime()[5]
    else:
        date_today      = make_date_string(time.localtime()) # localtime is in tuples
        date_tomorrow   = make_date_string(time.gmtime(time.time() + 60*60*24)) # timetime needed as number convert with gmtime to tuples
        date_year       = time.localtime()[0]
        date_month      = time.localtime()[1]
        date_day        = time.localtime()[2]
        date_hour       = time.localtime()[3]
        date_minute     = time.localtime()[4]
    #--------------------------------------------------------------------------
    #date_today      = '2025-11-05'  # for debug
    #date_tomorrow   = '2025-11-06'  # for debug
    #date_year       = 2025          # for debug
    #date_month      = 11            # for debug
    #date_day        = 5             # for debug
    #--------------------------------------------------------------------------
    #date_today      = '2025-06-30'  # for debug
    #date_tomorrow   = '2025-07-01'  # for debug
    #date_year       = 2025          # for debug
    #date_month      = 6             # for debug
    #date_day        = 30            # for debug
    #--------------------------------------------------------------------------
    print('date today', date_today, '| date tomorrow', date_tomorrow, '| hour', date_hour, 'minute', date_minute)


    #--------------------------------------------------------------------------
    # check the wifi status every hour and reconnect if needed
    if platform == 'pico':
        if wlan.status() != 3:
            print('WIFI : trying to reconnect...')
            wlan.disconnect()
            wlan.connect(config.wifi_ssid, config.wifi_password)
            # Wait for connect or fail
            max_wait = 10
            while max_wait > 0:
                if wlan.status() < 0 or wlan.status() >= 3:
                    break
                max_wait -= 1
                print('WIFI : waiting for connection...')
                time.sleep(1)
            # report back reconnect status
            if wlan.status() == 3:
                print('WIFI : wifi reconnected')
                wifi_status = True
            else:
                print('WIFI : wifi reconnect failed')
                wifi_status = False

    #--------------------------------------------------------------------------
    # only on the 0 hour or on the first startup and with working wifi
    if ((date_hour == 0) or (first_start == True)) and (wifi_status == True):
        # set the system time
        if platform == 'pico':
            if first_start:
                print('NTP : first start set time, going to contact time server')
            else:
                print('NTP : hour is 0, so going to update time')
            if set_time() < 0:
                # fast blinking system led indicates that the time could not be updated
                tim_system.init(freq=5, mode=Timer.PERIODIC, callback=tick_system)
                print('NTP : something did not go well when updating the system time')
            else:        
                # slow blinking indicates that the time was set correctly
                tim_system.init(freq=1, mode=Timer.PERIODIC, callback=tick_system)
                print('NTP : system time updated correctly from time server')

        # get the light codes for Twente
        if config.trash_company == 'twente':
            # get the trash_types from the API for this timeframe
            trash_types = get_pickup_dates_twente(config.trash_company_code, config.trash_address_id, date_today, date_tomorrow)
            if trash_types != None:
                [lights_today, lights_tomorrow] = trash_types_to_day_colors_twente(trash_types, date_today, date_tomorrow, config.run_debug)

        # get the light codes for RD4
        if config.trash_company == 'rd4':
            # get the pickups for the current month
            trash_types = get_pickup_dates_rd4(date_year, date_month, config.trash_postal_code, config.trash_house_number)
            if trash_types != None:
                [lights_today, lights_tomorrow] = trash_types_to_day_colors_rd4(trash_types, date_today, date_tomorrow, config.run_debug)
            # check if we are on the last day of the month            
            if is_last_day_of_month(date_month, date_day):                
                # check if we are in the last month
                if date_month == 12:
                    date_month = 1    # reset to month 1
                    date_year += 1    # then also up the year
                else:
                    date_month += 1   # in case of normal, just up the month
                print('RD4 : last day of month detected, checking also for', date_month, date_year)
                # now get the pickups for the next month, but only for the tomorrow light
                time.sleep(1)
                trash_types = get_pickup_dates_rd4(date_year, date_month, config.trash_postal_code, config.trash_house_number)
                if trash_types != None:
                    [lights_fake, lights_tomorrow] = trash_types_to_day_colors_rd4(trash_types, date_today, date_tomorrow, config.run_debug)
                

        #----------------------------------------------------------------------
        # disable all leds, then set them for today and tomorrow
        disable_all_leds()
        set_led_today(lights_today)
        set_led_tomorrow(lights_tomorrow)
    
    #--------------------------------------------------------------------------
    # disable the first start
    first_start = False
    
    # smart sleep so we are awake at minute 2 past the hour
    date_minute = time.localtime()[4]
    sleep_time = 60 - (date_minute - 2) 
    if sleep_time < 1:
        sleep_time = 2
    print('current date minute is', date_minute, ', going to sleep', sleep_time, 'minutes to get back to 2 past the hour')
    time.sleep(60*sleep_time)
    
