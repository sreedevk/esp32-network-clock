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
UNIX_EPOCH_DIFF = 946684800
AP_ESSID = 'devstation-2.4g'
AP_SECURITY_KEY = 'sreedev@3232712'
TIMEZONE = "America/New_York"
TIME_API_URL = "http://worldtimeapi.org/api/timezone/{}".format(TIMEZONE)

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

# API Call for Fetching Time
def world_time_api():
    """ Fetch & Parse WorldTimeApi """
    request_raw_response = requests.get(TIME_API_URL)
    return request_raw_response.json()

def parse_time_response(response):
    """ Parses the API EPOCH Time Response & Adjusts the UNIX EPOCH Diff """
    unix_time = response["unixtime"]
    return unix_time - UNIX_EPOCH_DIFF

def set_rtc_time(time_data, rtc_inst):
    """ Sets the Parsed Time onto the Machine RTC """
    rtc_inst.init(time_data)

def format_rtc_time(rtc_inst):
    """Formats Time Tuple to string"""
    # (year, month, mday, hour, minute, second, weekday, yearday)
    timeset = rtc_inst.datetime()
    return {
        "date": "{}/{}/{}".format(timeset[2], timeset[1], timeset[0]),
        "time": "{}:{}:{}".format(timeset[3], timeset[4], timeset[5])
    }

def prep_display_data(rtc_formatted_time):
    """ prepares the data to be printed / displayed"""
    return [
        ure.sub('_', ' ', TIMEZONE.split('/')[1]),
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

def start_clock():
    """ Initialize the clock, call apis, set time & update display"""
    display = init_display()
    wlan_adapter = init_network()
    while not wlan_adapter.isconnected():
        time.sleep(1)
    api_response = world_time_api()
    epoch_adjusted_time = parse_time_response(api_response)
    rtc_instance = RTC()
    set_rtc_time(utime.localtime(epoch_adjusted_time), rtc_instance)
    wlan_adapter.active(False)
    while True:
        formatted_rtc_timedata = format_rtc_time(rtc_instance)
        display_data = prep_display_data(formatted_rtc_timedata)
        print_data(display, display_data)
        time.sleep(1)
        gc.collect()

start_clock()
