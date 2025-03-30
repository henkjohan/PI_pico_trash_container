###############################################################################
#
#   Config file for trash container
#
###############################################################################
#
#   2024 - February - Henk-Johan
#           - first version
#   2025 - March - Henk-Johan
#           - added RD4 support
###############################################################################

''' Define if we are in debug mode or run mode '''
#run_debug = True
run_debug = False


''' Define on which system we are running the code '''
#run_system          = 'pc'
run_system          = 'pico'


''' The wifi network to make the connection with '''
wifi_ssid           = ''
wifi_password       = ''


''' Time synchronization settings '''
time_NTP_DELTA      = 2208988800
time_host           = "pool.ntp.org"


###############################################################################


''' In case of twente enable the next lines '''
trash_company       = 'twente'
trash_company_code  = ''
trash_address_id    = ''


''' In case of RD4 enable the next lines'''
#trash_company       = 'rd4'
#trash_postal_code   = ''
#trash_house_number  = ''

