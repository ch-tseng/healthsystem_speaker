import RPi.GPIO as GPIO
import time
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

pinOutControl = 40
pinPIR = 38
trigSR04 = 35
echoSR04 = 37

GPIO.setup(pinOutControl ,GPIO.OUT)
GPIO.setup(pinPIR ,GPIO.IN)

GPIO.setup(trigSR04 ,GPIO.OUT)
GPIO.setup(echoSR04 ,GPIO.IN)
GPIO.output(trigSR04, GPIO.LOW)

def readSR04():
    
        time.sleep(0.3)

        GPIO.output(trigSR04, True)
        time.sleep(0.00001)
        GPIO.output(trigSR04, False)

        # listen to the input pin. 0 means nothing is happening. Once a
        # signal is received the value will be 1 so the while loop
        # stops and has the last recorded time the signal was 0
        # change this value to the pin you are using
        # GPIO input = the pin that's connected to "Echo" on the sensor
        while GPIO.input(echoSR04) == 0:
          signaloff = time.time()
        
        # listen to the input pin. Once a signal is received, record the
        # time the signal came through
        # change this value to the pin you are using
        # GPIO input = the pin that's connected to "Echo" on the sensor
        while GPIO.input(echoSR04) == 1:
          signalon = time.time()
        
        # work out the difference in the two recorded times above to 
        # calculate the distance of an object in front of the sensor
        timepassed = signalon - signaloff
        
        # we now have our distance but it's not in a useful unit of
        # measurement. So now we convert this distance into centimetres
        distance = timepassed * 17000
        
        # return the distance of an object in front of the sensor in cm
        return distance
        

while True:

	statusPIR = GPIO.input(pinPIR)

	if statusPIR == 0:
		GPIO.output(pinOutControl ,0)
		time.sleep(0.1)
	elif statusPIR == 1:
		print readSR04()
        	GPIO.output(pinOutControl ,1)
        	time.sleep(0.1)
