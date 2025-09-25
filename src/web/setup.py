import network
from machine import Pin, reset, WDT
import utime
import socket

from device_config import __DeviceConfig

board_led = Pin('LED', Pin.OUT)

def connect_wifi(wifi_config: dict, reset_after_fail: bool=False, allow_print: bool=False, wdt: WDT|None=None) -> None|tuple:
    ssid = wifi_config["ssid"]
    password = wifi_config["password"]
    
    if allow_print:
        print(f"Connecting to wi-fi: {ssid}")
    
    wifi = network.WLAN(network.STA_IF)
    wifi.active(False)
    utime.sleep(1)
    wifi.active(True)
    wifi.config(pm = 0xa11140)
    utime.sleep(1)
    
    if allow_print:
        print("Available networks (ssid, bssid, channel, RSSI, security, hidden):", wifi.scan())

    if wdt:
        wdt.feed()

    wifi.connect(ssid, password)
    utime.sleep(2)

    max_wait = 10
    while max_wait > 0:
        if wifi.status() < 0 or wifi.status() >= 3:
            break
        max_wait -= 1
            
        board_led.toggle()
        if allow_print:
            print(".", end="")
        if wdt:
            wdt.feed()
        utime.sleep(1)


    wifi_status = wifi.status()


    if wifi_status == 3:
        # Success
        network_info = wifi.ifconfig()
        
        if allow_print:
            print('Connection successful!')
            print('IP address:', network_info[0])

        return network_info

    else:
        if wifi_status == -1:
            msg = "connection failed, try resetting the device"
        elif wifi_status == -2:
            # No access point found
            msg = "no access point found"
        elif wifi_status == -3:
            msg = "wrong password"
        else:
            msg = f"status: {wifi_status}"
            
        if allow_print:
            print(f'Failed to establish a network connection, {msg}')

        if reset_after_fail:
            reset()

        return None
    
    




def open_socket() -> socket.socket:
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(20)
    

    return s
