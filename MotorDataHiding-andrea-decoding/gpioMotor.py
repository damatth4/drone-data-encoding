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
import os     # importing os library to communicate with the system
import time   # importing time library to make Rpi wait
import sched  #
os.system ("sudo killall pigpiod")
time.sleep(2) # Wait to make sure pigpiod process is not running
os.system ("sudo pigpiod") # Launching GPIO library
time.sleep(1) # delay prevents timing error
import pigpio # importing GPIO library
import numpy as np
import bitarray
ba = bitarray.bitarray()
pi = pigpio.pi()

#scheduler = sched.scheduler(time.time, time.sleep) # May be needed for timed calls

ESC = 13  # GPIO pin connected to ESC
pi.set_mode(ESC, pigpio.OUTPUT)

def setDuty(val): # Remove need for ESC value to be entered
    pi.set_PWM_dutycycle(ESC,val)
    return

def stop():
    pi.set_PWM_dutycycle(ESC, 0)
    pi.stop()

def init(): # initialize PWM settings from a stop
    pi.set_PWM_frequency(ESC,500) # 500 Hz
    time.sleep(1)
    pi.set_PWM_dutycycle(ESC, 60) #60% dut
    time.sleep(1)
    return

def testPFM():
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
    stop()
    print("Done")

    print("Enter 'r' to repeat test or press enter to continue")
    opt = input()
    if opt == 'r':
        opt = 0
        testPFM()
    else:
        main1()


def testPWM():
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
    stop()
    print("Done")

    print("Enter 'r' to repeat test or press enter to continue")
    opt = input()
    if opt == 'r':
        opt = 0
        testPWM()
    else:
        main1()

## String to UTF-8 encoding
def toBitsUTF8(str): # Work in progress
    ba.frombytes(str.encode('utf-8'))
    return ba.tolist()

## Convert String to bits from ASCII encoding
def asciiToBits(str):
    result = []
    for c in str:
        bits = bin(ord(c))[2:]
        bits = '00000000'[len(bits):] + bits
        result.extend([int(b) for b in bits])
    return result
## Convert bits to ASCII chars and a string
def bitsToASCII(bits):
    chars = []
    for b in range(int(len(bits) / 8)):
        byte = bits[b*8:(b+1)*8]
        chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
    return ''.join(chars)

def wstartMessage(): # indicates start of message
    pi.set_PWM_dutycycle(ESC,75)
    time.sleep(0.02) # 20ms duration
    pi.set_PWM_dutycycle(ESC,60) # return to baseline
    return

def wendMessage(): # indicates end of message
    pi.set_PWM_dutycycle(ESC,55)
    time.sleep(0.02)
    pi.set_PWM_dutycycle(ESC,60) # return to baseline
    return
### Encoding ------------------------------------------------------------------
#| Takes string as input, converts to bit array and encodes bits as PWM
#| Using Manchester encoding (IEEE 802.3)
#|                               1 = 01      0 = 10
#------------------------------------------------------------------------------
#|  Pulse Frequency Modulation
#|  Current bit length: 210ms
#------------------------------------------------------------------------------
bitLen = 0.07 # in seconds (70 ms) // increased from 50ms to allow freq to reach
# peak when switching quickly
chirpLen = 0.5 # seconds
## // 1/3 bit length for Manchester Encoding (210ms/bit)
baseF = 400 # base freq 400Hz
highF = 500 # high freq 500 Hz
lowF = 320 # low freq 320 Hz

# daemon sampling rate of 5*10^-6 seconds (5 MHz)
freqList = [10, 20, 40, 50, 80, 100, 160, 200, 250, 320, 400, 500, 800, 1000]
#, 1600, 2000, 4000, 8000]  out of ESC input range
bitLen = chirpLen
#// Might remove returning to base frequency

# High bit frequency pattern (low,high,base) // holding each value for 70ms
def fm1(): # 1[high] -> 01
    pi.set_PWM_frequency(ESC,lowF)# 320 Hz [0]
    time.sleep(bitLen) # allows change in frequency to plateu to constant
    pi.set_PWM_frequency(ESC,highF) # 500 Hz [1]
    time.sleep(bitLen)
    pi.set_PWM_frequency(ESC,baseF) # 400 Hz [-]
    time.sleep(bitLen)

# Low bit frequency pattern (high,low,base) // holding each value for 70ms
def fm0(): # 0[low] -> 10
    pi.set_PWM_frequency(ESC,highF) # 500 Hz [1]
    time.sleep(bitLen)
    pi.set_PWM_frequency(ESC,lowF)# 320 Hz [0]
    time.sleep(bitLen)
    pi.set_PWM_frequency(ESC,baseF) # 400 Hz [-]
    time.sleep(bitLen)

# Start sequence 1111 -> [01 01 01 01] 1 byte (840ms)
def fstartMessage(): # indicates start of message for PFM
    pi.set_PWM_dutycycle(ESC,60)
    fm1() #210ms per call to fm1()
    fm1()
    fm1()
    fm1()
    return
# End sequence 0000 -> [10 10 10 10] 1 byte (1000ms)
def fendMessage(): # indicates end of message (EOM) for PFM
    time.sleep(0.16) # pads EOM call to 1000ms
    fm0() #210ms per call to fm0()
    fm0()
    fm0()
    fm0()
    return

def sendStringF(msg):
    bitArr = asciiToBits(msg) # message bit array
    print(bitArr)
    fstartMessage() # 210 * 4 = 840ms
    # 840ms + 160ms = 1000ms => TTM (Time to Message):
    # total time from init sequence to message start (1000ms)
    time.sleep(0.16)
    for bit in bitArr:
        if int(bit) == 1:
            fm1() #210ms
        else:
            fm0() #210ms

    fendMessage()
    pi.set_PWM_dutycycle(ESC,0)
    time.sleep(0.25)
    print("Encoded Message: ", bitsToASCII(bitArr)) # encode back to check bits
    print("bit array length: ", len(bitArr), "bits | bit length: ",bitLen)
    input("Done. Press Enter to return to main()")
    main()
#-----------------------------------------------------------------------------
# | Pulse Width Modulation
#-----------------------------------------------------------------------------
def sendStringW(msg):
    bitArr = asciiToBits(msg) # message bit array
    print(bitArr)
    wstartMessage()
    time.sleep(0.25)
    for bit in bitArr:
        if int(bit) == 1:
            pi.set_PWM_dutycycle(ESC,63)
            time.sleep(bitLen)
        else:
            pi.set_PWM_dutycycle(ESC,60)
            time.sleep(bitLen)
    wendMessage()
    stop()
    time.sleep(0.25)
    print("Encoded Message: ", bitsToASCII(bitArr)) # encode back to check bits
    print("bit array length: ", len(bitArr), "bits | bit length: ",bitLen)
    input("Done. Press Enter to return to main()")
    main()


### ---------------------------------------------------------------------------
def hold320():
    init()
    print("Output: 320Hz for 30 sec")
    pi.set_PWM_frequency(ESC, 320)

    print("PWM Output: GPIO ",ESC,"| Duty Cycle:", pi.get_PWM_dutycycle(ESC),\
    "| Freq:", pi.get_PWM_frequency(ESC))

    time.sleep(30)
    print("done.")
    input()
    #stop()
    main()

def hold400():
    init()
    print("Output: 400Hz for 30 sec")
    pi.set_PWM_frequency(ESC, 400)

    print("PWM Output: GPIO ",ESC,"| Duty Cycle:", pi.get_PWM_dutycycle(ESC),\
    "| Freq:", pi.get_PWM_frequency(ESC))

    time.sleep(30)
    print("done.")
    input()
    #stop()
    main()

def hold500():
    init()
    print("Output: 500Hz for 30 sec")
    pi.set_PWM_frequency(ESC, 500)

    print("PWM Output: GPIO ",ESC,"| Duty Cycle:", pi.get_PWM_dutycycle(ESC),\
    "| Freq:", pi.get_PWM_frequency(ESC))

    time.sleep(30)
    print("done.")
    input()
    #stop()
    main()

### ---------------------------------------------------------------------------
def bitTest():
    init()
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
    print("To quit, press q. Otherwise, enter a 1 or 0 to transmit ")
    inp = "i"
    while inp != "q":
      inp = str(input(":> "))
      if inp == 1:
        fm1()
      else: fm0()
    pi.set_PWM_frequency(ESC, 0)
    main()
#+--------------------+#
#| test of freq range |#
#+--------------------+#
def bitTest1():
    init()
    print("testing series of frequencies")
    for i in freqList:
       pi.set_PWM_frequency(ESC, i)
       print("Frequency: ", i)
       time.sleep(1)
    stop()
    print("End of Test")
    main()


def calibrate():
    print("----------------Current PWM settings-----------------")
    print("")
    print("PWM Output: GPIO ",ESC,"| Duty Cycle:", pi.get_PWM_dutycycle(ESC),\
    "| Freq:", pi.get_PWM_frequency(ESC))
    print("")
    print("-----------------------------------------------------")
    print("Setting minimum duty cycle")
    setDuty(10) # 10%
    time.sleep(2)
    print("Setting maximum duty cycle")
    setDuty(90) # 90%
    time.sleep(2)
    setDuty(0)
    time.sleep(1)
    print("Done.")
    main()

def main1():
    pi.set_PWM_range(ESC,100) # range of pwm (50 is 50% Dut)
    init()
    setDuty(0)
    print("Enter c to calibrate or press enter to skip")
    inp1 = input()
    if inp1 == 'c':
      print("Calibrating")
      calibrate()
    else:
      main()

def main():
    print("Select from options below:")
    print("--------------------------")
    print("1 | PFM Test")
    print("2 | PWM Test")
    print("3 | Send String (PWM)")
    print("4 | Send String (PFM)")
    print("5 | Bit test ")
    print("6 | hold 320Hz")
    print("7 | hold 400Hz")
    print("8 | hold 500Hz")
    inp=int(input())
    if inp == 1:
        testPFM()
    elif inp == 2:
        testPWM()
    elif inp == 3:
        message = input("Enter Message: ")
        sendStringW(message)
    elif inp == 4:
        message = input("Enter Message: ")
        sendStringF(message)
    elif inp == 5:
        bitTest()
    elif inp == 6:
        hold320()
    elif inp == 7:
        hold400()
    elif inp == 8:
        hold500()
    else:
        print("Stopping..")
        stop()

try:
    main1()
except:
    print("Stopping...")
    stop()


#pi.set_servo_pulsewidth(ESC, 0)
#pi.wave_add_serial(4, 300, 'Hello world') # Adds to waveform as serial?


##============================================================================##
# The selectable frequencies depend upon the sample rate
# which may be 1, 2, 4, 5, 8, or 10 microseconds (default 5).
# The sample rate is set when the pigpio daemon is started.
#
# The frequencies for each sample rate are:
#
#                        Hertz
#
#        1: 40000 20000 10000 8000 5000 4000 2500 2000 1600
#            1250  1000   800  500  400  250  200  100   50
#
#        2: 20000 10000  5000 4000 2500 2000 1250 1000  800
#             625   500   400  250  200  125  100   50   25
#
#        4: 10000  5000  2500 2000 1250 1000  625  500  400
#             313   250   200  125  100   63   50   25   13
# sample
#  rate
#  (us)  5:  8000  4000  2000 1600 1000  800  500  400  320
#             250   200   160  100   80   50   40   20   10
#
#        8:  5000  2500  1250 1000  625  500  313  250  200
#             156   125   100   63   50   31   25   13    6
#
#       10:  4000  2000  1000  800  500  400  250  200  160
#             125   100    80   50   40   25   20   10    5


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
