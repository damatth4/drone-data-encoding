"""
##---------------------------------------------------------------------------##
| Copyright [2020] Dakota Matthews (damatth@uw.edu)                           |
|                                                                             |
|  Program for running RaspberryPi as input for ESC to drive BLDC motor       |
|  Uses PFM to change audible frequency and PWM to adjust speed of motor      |
|  Baseline PWM: dutycycle - 60%, freq - 400 Hz                               |
|                                                                             |
##---------------------------------------------------------------------------##
"""
"""
##---------------------------------------------------------------------------##
| Further improvements made by Collin Dang (cdang38@uw.edu)                   |
|                                                                             |
##---------------------------------------------------------------------------##
"""
import os     # importing os library to communicate with the system
import time   # importing time library to make Rpi wait
import sched  
os.system ("sudo killall pigpiod") # Make sure instance of pigpio daemon not running
time.sleep(2) # Wait to make sure pigpiod process is not running
os.system ("sudo pigpiod -s 1") # Launching GPIO library and setting sampling rate to 1MHz
#os.system ("sudo pigpiod -t 0") # Change clk periph to PWM(0) from PCM(1:default)
time.sleep(1) # delay prevents timing error
import pigpio # importing GPIO library
import numpy as np

###------------------------------------SETUP------------------------------------###
pi = pigpio.pi()

ESC = 13  # GPIO pin connected to ESC
pi.set_mode(ESC, pigpio.OUTPUT)

# peak when switching quickly
## // 1/3 bit length for Manchester Encoding (210ms/bit)
baseF = 1250 # base freq 1250 Hz
highF = 1600 # high freq 1600 Hz
lowF = 1000 # low freq 1000 Hz

# daemon sampling rate of 5*10^-6 seconds (5 MHz)
freqList = [10, 20, 40, 50, 80, 100, 160, 200, 250, 320, 400, 500, 800, 1000]
#, 1600, 2000, 4000, 8000]  out of ESC input range
#// Might remove returning to base frequency

bitLen = None

while True:
    inp = input('\nPlease enter bit length. This is the amount of time high, low, or base is held. Input must be a positive number: ')
    try:
        bitLen = float(inp)
        if bitLen > 0:
            break
        else:
            print('Error! Please enter a valid bit length.')
    except ValueError:
        print('Error! Please enter a valid bit length.')

###------------------------------------METHODS------------------------------------###

def init(): # initialize PWM settings from a stop
    pi.set_PWM_frequency(ESC,500) # 500 Hz
    time.sleep(1)
    pi.set_PWM_dutycycle(ESC, 60) #60% dut
    time.sleep(1)
    return

def test_PFM():
    input("Press Enter to start")
    print("Starting PFM at 500Hz and 60% Duty Cycle, (5 sec total)")
    print("Changing to 800 Hz for 1 second and back to 500 Hz")
    pi.set_PWM_frequency(ESC,500)
    pi.set_PWM_dutycycle(ESC,60)
    print("500Hz")
    time.sleep(1)
    pi.set_PWM_frequency(ESC,800)
    print("800Hz")
    time.sleep(2)
    pi.set_PWM_frequency(ESC,400)
    print("400Hz")
    time.sleep(2)
    pi.set_PWM_frequency(ESC,500)
    print("500Hz")
    time.sleep(2)
    pi.set_PWM_dutycycle(ESC,60)
    fm1() #210ms per call to fm1()
    fm1()
    fm1()
    fm1()
    time.sleep(2)
    pi.set_PWM_dutycycle(ESC, 0)
    print("Done")


def test_PWM():
    input("Press Enter to start")
    print("Starting PWM at 500 Hz and 60% Duty Cycle, (5 sec total)")
    print("Changing to 80% Duty Cycle for 1 second then back to 60%")
    pi.set_PWM_frequency(ESC,500)
    pi.set_PWM_dutycycle(ESC,60)
    print("60%")
    time.sleep(2)
    pi.set_PWM_dutycycle(ESC,80)
    time.sleep(1)
    pi.set_PWM_dutycycle(ESC,60)
    time.sleep(2)
    pi.set_PWM_dutycycle(ESC, 0)
    print("Done")

## String to UTF-8 encoding
#def toBitsUTF8(str): # Work in progress
#    ba.frombytes(str.encode('utf-8'))
#    return ba.tolist()

## Convert String to bits from ASCII encoding
def ascii_to_bits(str):
    result = []
    for c in str:
        bits = bin(ord(c))[2:]
        bits = '00000000'[len(bits):] + bits
        result.extend([int(b) for b in bits])
    return result
## Convert bits to ASCII chars and a string
def bits_to_ascii(bits):
    chars = []
    for b in range(int(len(bits) / 8)):
        byte = bits[b*8:(b+1)*8]
        chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
    return ''.join(chars)

def w_start_message(): # indicates start of message
    pi.set_PWM_dutycycle(ESC,75)
    time.sleep(0.02) # 20ms duration
    pi.set_PWM_dutycycle(ESC,60) # return to baseline
    return

def w_end_message(): # indicates end of message
    pi.set_PWM_dutycycle(ESC,55)
    time.sleep(0.02)
    pi.set_PWM_dutycycle(ESC,60) # return to baseline
    return


# High bit frequency pattern (low,high,base
def fm1(): # 1[high] -> 01
    pi.set_PWM_frequency(ESC,lowF)# 1000 Hz [0]
    time.sleep(bitLen) # allows change in frequency to plateau
    pi.set_PWM_frequency(ESC,highF) # 1600 Hz [1]
    time.sleep(bitLen)
    pi.set_PWM_frequency(ESC,baseF) # 1250 Hz [-]
    time.sleep(bitLen)

# Low bit frequency pattern (high,low,base)
def fm0(): # 0[low] -> 10
    pi.set_PWM_frequency(ESC,highF) # 1000 Hz [1]
    time.sleep(bitLen)
    pi.set_PWM_frequency(ESC,lowF) # 1600 Hz [0]
    time.sleep(bitLen)
    pi.set_PWM_frequency(ESC,baseF) # 1250 Hz [-]
    time.sleep(bitLen)

# Start sequence 1111 -> [01 01 01 01] 1 byte (840ms)
def f_start_message(): # indicates start of message for PFM
    pi.set_PWM_dutycycle(ESC,60)
    fm1() #210ms per call to fm1()
    fm1()
    fm1()
    fm1()
    return
# End sequence 0000 -> [10 10 10 10] 1 byte (1000ms)
def f_end_message(): # indicates end of message (EOM) for PFM
    time.sleep(0.16) # pads EOM call to 1000ms
    fm0() #210ms per call to fm0()
    fm0()
    fm0()
    fm0()
    return

def send_string_f():
    msg = input("Enter Message >> ")
    bitArr = ascii_to_bits(msg) # message bit array
    print('ascii translation: ' + str(bitArr)) # ASCII encoded bit array
    f_start_message()
    time.sleep(0.16)
    for bit in bitArr:
        if int(bit) == 1:
            fm1() #210ms
        else:
            fm0() #210ms

    f_end_message()
    pi.set_PWM_dutycycle(ESC,0)
    time.sleep(0.25)
    print("Encoded Message: ", bits_to_ascii(bitArr)) # encode back to check bits
    print("bit array length: ", len(bitArr), "bits | bit length: ",bitLen)
    print('Done. Returning back to select_options')


def send_string_w():
    print("Current frequency is: " + str(pi.get_PWM_frequency(ESC)))
    msg = input("Enter Message >> ")
    bitArr = ascii_to_bits(msg) # message bit array
    print(bitArr)
    w_start_message()
    time.sleep(0.25)
    for bit in bitArr:
        if int(bit) == 1:
            pi.set_PWM_dutycycle(ESC,63)
            time.sleep(bitLen)
        else:
            pi.set_PWM_dutycycle(ESC,60)
            time.sleep(bitLen)
    w_end_message()
    pi.set_PWM_dutycycle(ESC, 0)
    time.sleep(0.25)
    print("Encoded Message: ", bits_to_ascii(bitArr)) # encode back to check bits
    print("bit array length: ", len(bitArr), "bits | bit length: ",bitLen)
    #input("Done. Press Enter to return to select_options")
    print('Done. Returning back to select_options')



def hold_frequency(freq):
    pi.set_PWM_dutycycle(ESC, 60)
    # time.sleep(1)
    pi.set_PWM_frequency(ESC, freq)
    print("PWM Output: GPIO ",ESC,"| Duty Cycle:", pi.get_PWM_dutycycle(ESC),\
    "| Freq:", pi.get_PWM_frequency(ESC))
    time.sleep(10)
    print("done.")
    pi.set_PWM_dutycycle(ESC, 0)

    
def bit_test():
    pi.set_PWM_dutycycle(ESC,60)
    print("sending a 1 followed by 1 sec rest x3")
    fm1()
    time.sleep(1)
    fm1()
    time.sleep(1)
    fm1()
    time.sleep(1)
    print("sending a 0 followed by 1 sec rest x3")
    fm0()
    time.sleep(1)
    fm0()
    time.sleep(1)
    fm0()
    print("end of test")
    inp = input("To quit, press q. Otherwise, enter a 1 or 0 to transmit: ")
    while(True):
        if str(inp).lower() == "q":
            break
        elif inp.isdigit() and int(inp) == 1:
            fm1()
        elif inp.isdigit() and int(inp) == 0:
            fm0()
        else:
            print("\ninvalid option.")
        inp = input("To quit, press q. Otherwise, enter a 1 or 0 to transmit: ")
    pi.set_PWM_frequency(ESC, 0)
    pi.set_PWM_dutycycle(ESC, 0)

def bit_test_1():
    init()
    print("testing series of frequencies")
    for i in freqList:
       pi.set_PWM_frequency(ESC, i)
       print("Frequency: ", i)
       time.sleep(1)
    pi.set_PWM_dutycycle(ESC, 0)
    print("End of Test")


def calibrate():
    print("----------------Current PWM settings-----------------")
    print("")
    print("PWM Output: GPIO ",ESC,"| Duty Cycle:", pi.get_PWM_dutycycle(ESC),\
    "| Freq:", pi.get_PWM_frequency(ESC))
    print("")
    print("-----------------------------------------------------")
    print("Setting minimum duty cycle")
    pi.set_PWM_dutycycle(ESC, 10)
    time.sleep(2)
    print("Setting maximum duty cycle")
    pi.set_PWM_dutycycle(ESC, 90)
    time.sleep(2)
    pi.set_PWM_dutycycle(ESC, 0)
    time.sleep(1)
    print("Done.")

def custom_binary():
    inp = input('Please enter a custom string of ones and zeros: ')
    pi.set_PWM_dutycycle(ESC, 60)
    for number in inp:
        if int(number) == 0:
            fm0()
        elif int(number) == 1:
            fm1()
        else:
            print('error. character is not a one or zero')
            break
    pi.set_PWM_dutycycle(ESC, 0)


def main():
    pi.set_PWM_range(ESC,100) # range of pwm (50 is 50% Dut)
    print("Initializing...")
    init()
    pi.set_PWM_dutycycle(ESC, 0)
    inp = input("Enter c to calibrate or press any key to skip: ")
    if inp == 'c':
      print("Calibrating")
      calibrate()
    select_options()

def show_options():
    print("\nSelect from options below:")
    print("--------------------------")
    print("1 | PFM Test")
    print("2 | PWM Test")
    print("3 | Send String (PWM)")
    print("4 | Send String (PFM)")
    print("5 | Bit test ")
    print("6 | hold low frequency")
    print("7 | hold base frequency")
    print("8 | hold high frequency")
    print("9 | custom binary input")
    print("Or enter \"stop\" to stop!")

def select_options():
    show_options()
    while(True):
        inp=input("\nSelect Option (press 0 to see options again): ")
        if inp.isdigit() and int(inp) >= 0 and int(inp) <= 9:
            if int(inp) == 0:
                show_options(),
            elif int(inp) == 1:
                test_PFM(),
            elif int(inp) == 2:
                test_PWM(),
            elif int(inp) == 3: 
                send_string_w(),
            elif int(inp) == 4: 
                send_string_f(),
            elif int(inp) == 5: 
                bit_test(),
            elif int(inp) == 6: 
                hold_frequency(lowF),
            elif int(inp) == 7: 
                hold_frequency(baseF),
            elif int(inp) == 8: 
                hold_frequency(highF),
            elif int(inp) == 9:
                custom_binary()
        elif str(inp).lower() == "stop":
            break
        else:
            print("Please select a valid option.")

    print("Stopping...")
    pi.set_PWM_dutycycle(ESC, 0)
    pi.stop()
    print("End of Program")



###------------------------------------ACTUAL CODE------------------------------------###
try: 
    main()
finally:
    os.system ("sudo killall pigpiod")




##============================================================================##
# The selectable frequencies depend upon the sample rate
# which may be 1, 2, 4, 5, 8, or 10 microseconds (default 5).
# The sample rate is set when the pigpio daemon is started.
#
# The frequencies for each sample rate are:
#
#                        Hertz
#
#        1: 40000 20000 10000 8000 5000 4000 2500 2000 1600 1250  1000   800  500  400  250  200  100   50
#
#        2: 20000 10000  5000 4000 2500 2000 1250 1000  800 625   500   400  250  200  125  100   50   25
#
#        4: 10000  5000  2500 2000 1250 1000  625  500  400 313   250   200  125  100   63   50   25   13
# sample
#  rate
#  (us)  5:  8000  4000  2000 1600 1000  800  500  400  320 250   200   160  100   80   50   40   20   10
#
#        8:  5000  2500  1250 1000  625  500  313  250  200 156   125   100   63   50   31   25   13    6
#
#       10:  4000  2000  1000  800  500  400  250  200  160 125   100    80   50   40   25   20   10    5


#               Example:
#
#           pi.set_PWM_frequency(4,0)
#           print(pi.get_PWM_frequency(4))
#           10
# 
#           pi.set_PWM_frequency(4,100000)
#           print(pi.get_PWM_frequency(4))
#           8000
##============================================================================##
