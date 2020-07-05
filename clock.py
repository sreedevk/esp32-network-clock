from machine import I2C
from machine import Pin
from machine import RTC
import ssd1306, time, network, gc
import utime
import urequests as requests
import ure

SDA_PIN = 21
SCL_PIN = 23
DISPLAY_WIDTH_PX = 128
DISPLAY_HEIGHT_PX = 32
NEWLINE_OFFSET_PX = 8
INPUT_SIG_PIN = 16
UNIX_EPOCH_DIFF = 946684800
AP_ESSID = 'devstation-2.4g'
AP_SECURITY_KEY = 'XXXXXXXX'
SUPPORTED_TIMEZONES = ["America/New_York", "Asia/Kolkata", "Europe/Rome"]
CURRENT_TIMEZONE_IDX = 0
TIME_API_URL = "http://worldtimeapi.org/api/timezone/{}"

# initialize display
def init_display():
    """ Initialize Display """
    i2c = I2C(sda=Pin(SDA_PIN), scl=Pin(SCL_PIN))
    return ssd1306.SSD1306_I2C(DISPLAY_WIDTH_PX, DISPLAY_HEIGHT_PX, i2c)

# Network Instantiation
def init_network():
    "Initialize Network & Connect to Wifi"
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(AP_ESSID, AP_SECURITY_KEY)
    return wlan

def switch_timezone():
    """ Switch Between Timezones """
    global CURRENT_TIMEZONE_IDX
    if CURRENT_TIMEZONE_IDX >= (len(SUPPORTED_TIMEZONES) - 1):
        CURRENT_TIMEZONE_IDX = 0
    else:
        CURRENT_TIMEZONE_IDX += 1

def fetch_current_timezone():
    """Fetch & Return currrent timezone string"""
    return SUPPORTED_TIMEZONES[CURRENT_TIMEZONE_IDX]

# Initialize Input Mechanism
def initialize_input():
    """ Initializes Input Stream on Pin """
    return Pin(INPUT_SIG_PIN, Pin.IN)


# API Call for Fetching Time
def world_time_api():
    """ Fetch & Parse WorldTimeApi """
    request_raw_response = requests.get(TIME_API_URL.format(fetch_current_timezone()))
    return request_raw_response.json()

def parse_time_string(response):
    """ Parses the Time String Instead of the EPOCH time"""
    date_time_string = response['datetime']
    # (year, month, day[, hour[, minute[, second[, microsecond[, tzinfo]]]]])
    # 2020-07-04T02:01:46.283707-04:00
    date, time_add_zone = date_time_string.split('T')
    year, month, day = date.split('-')
    zone_regex = ure.compile(r'[+-]')
    time_data, _ = zone_regex.split(time_add_zone)
    hour, minute, second = time_data.split(':')
    macrosecond, microsecond = second.split('.')
    time_data_tup = (int(year), int(month), int(day), int(hour), int(minute), int(macrosecond), int(microsecond), 0)
    return time_data_tup[0:3] + (0,) + time_data_tup[3:6] + (0,)

def set_rtc_time(time_data):
    """ Sets the Parsed Time onto the Machine RTC """
    RTC().init(time_data)

def format_rtc_time():
    """Formats Time Tuple to string"""
    # (year, month, mday, hour, minute, second, weekday, yearday)
    timeset = RTC().datetime()
    return {
        "date": "{}/{}/{}".format(timeset[2], timeset[1], timeset[0]),
        "time": "{}:{}:{}".format(timeset[4], timeset[5], timeset[6])
    }

def prep_display_data(rtc_formatted_time):
    """ prepares the data to be printed / displayed"""
    return [
        ure.sub('_', ' ', fetch_current_timezone().split('/')[1]),
        "date: {}".format(rtc_formatted_time['date']),
        "time: {}".format(rtc_formatted_time['time']),
        "memory: {}".format(gc.mem_free())
    ]

def print_data(display, data):
    """ Prints the Formatted RTC time onto connected display"""
    display.fill(0)
    disp_x, disp_y = (1, 1)
    for disp_datum in data:
        display.text(disp_datum, disp_x, disp_y)
        disp_y += NEWLINE_OFFSET_PX
    display.show()

def initialize_clock():
    """ Initialize the clock, call apis, set time """
    display = init_display()
    wlan_adapter = init_network()
    input_stx = initialize_input()
    while not wlan_adapter.isconnected():
        time.sleep(1)
    api_response = world_time_api()
    time_data = parse_time_string(api_response)
    set_rtc_time(time_data)
    wlan_adapter.active(False)
    return display, input_stx


def start_clock():
    """  display time """
    gc.collect()
    display, input_stx = initialize_clock()
    while True:
        if input_stx.value() == 0:
            switch_timezone()
            break
        formatted_rtc_timedata = format_rtc_time()
        display_data = prep_display_data(formatted_rtc_timedata)
        print_data(display, display_data)
        time.sleep(1)
    start_clock()

start_clock()
