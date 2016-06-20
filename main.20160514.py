#!/usr/bin/env python
# -*- coding: utf-8 -*-

#PIN configuration
pinOutControl = 40
pinPIR = 38
trigSR04 = 35
echoSR04 = 37

#Global Parameters
lengthCM_SR04 = 15  #距離SR04在幾公分以內, 才認定為正開始使用照護系統
timeLasted_SR04 = 5  #有人站在SR04面前持續了幾秒後, 才認定為要始用照護系統
nextWelcomeTimer = 60  #上次Welcome之後, 至少要隔多久才能再Welcome 

#speakerName = ["Bruce", "Theresa", "Angela" "TW_LIT_AKoan", "TW_SPK_AKoan"]


#-------------------------------------------------
tmpTime_SR04 = 0  #開始計時時的秒數, 用於計算timeLasted_SR04
statusSR04 = 0
statusPIR = 0

tmpLastWelcomeTime = 0  #上次的歡迎時間

import RPi.GPIO as GPIO
import time
import timeit
import speechClass
import json
import os
import random

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(pinOutControl ,GPIO.OUT)
GPIO.setup(pinPIR ,GPIO.IN)

GPIO.setup(trigSR04 ,GPIO.OUT)
GPIO.setup(echoSR04 ,GPIO.IN)
GPIO.output(trigSR04, GPIO.LOW)

os.system("amixer set PCM -- 100%")

def is_json(myjson):
        try:
                json_object = json.loads(myjson)
        except ValueError, e:
                return False
        return True

def getWords_1(vHour):
	if vHour>=6 and vHour<11:
		wordArray_1 = ["早安", "Good Morning", "早哦!Good morning", "早上愉快", "Have a nice day."]		
	elif vHour>=11 and vHour<13:
		wordArray_1 = ["午安", "吃過飯了嗎?", "吃過中餐了嗎?", "準備吃飯了嗎?", "午餐時間到了哦?", "中午時間了."]
	elif vHour>=13 and vHour<17:
		wordArray_1 = ["午安", "下午愉快", "Good afternoon", "下午忙嗎?"]
	elif vHour>=17 and vHour<18:
		wordArray_1 = ["午安", "時間真快, 快下班了哦?", "Have a nice day, 今天忙嗎?", "Good afternoon, 來個下午茶吧?", "午安, 太忙的話休息一下."]
	elif vHour>=18 and vHour<19:
		wordArray_1 = ["晚安", "晚安, 準備下班了嗎?", "Hi, 還沒下班哦?", "Good night",  "晚安, 不要太晚下班.", "Good night, 今天忙嗎?", "今天過得如何?"]
	elif (vHour>=19 and vHour<24) or (vHour>=0 and vHour<4):
		wordArray_1 = ["這麼晚還沒下班?", "晚安, 很晚了哦, 早點下班", "加班嗎? 不要太累哦?", "很晚了, 請早點下班."]
	elif vHour>=4 and vHour<6:
		wordArray_1 = ["早安, 這麼早上班!", "Good morning, 早起的鳥有蟲吃!", "Good morning, 很早哦!"]
	
	return random.choice(wordArray_1)

def getWords_2():
	wordArray_2 = ["歡迎使用福委會的員工照護系統。", "員工照護系統歡迎您！", "歡迎再來使用"]
	return random.choice(wordArray_2)

def speakWords(wordsSpeak, speakerName, frequency, speed):
        nessContent = wordsSpeak
        #print nessContent
        newsArray = nessContent.split("｜")

        i=0
        person = speechClass.TTSspech()

        for newsSpeak in newsArray:
                if(len(newsSpeak)>0):
                        #print len(newsSpeak)
                        print "(" + str(len(newsSpeak)) + ") " + newsSpeak
                        person.setWords("\"" + newsSpeak + "\"")
                        person.setSpeaker("\"" + speakerName + "\"")  # Bruce, Theresa, Angela, MCHEN_Bruce, MCHEN_Jo$
                        person.setSpeed(speed)

                        id = int(person.createConvertID())
                        print "URL: " + person.getVoiceURL()
                        if(id>0):
                                #print person.getVoiceURL()
                                #while person.isBusySpeakingNow():time.sleep( 0.05 )
                                person.playVoice(frequency ,5)


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

def getDistance():
	sampleCounts = 6  #要取幾次標本

	count = 0
	maxValue = 0
	minValue = 99999
	totalValue = 0

	while(count<sampleCounts):
		valueSR04 = readSR04()
		if valueSR04>maxValue:
			maxValue = valueSR04
		if valueSR04<minValue:
			minValue = valueSR04

		totalValue += valueSR04
		count += 1
	
	return (totalValue-maxValue-minValue) / (sampleCounts-2)

while True:


	dt = list(time.localtime())
        nowHour = dt[3]
        nowMinute = dt[4]


	statusPIR = GPIO.input(pinPIR)

	#如果有人站在前面
	if getDistance()<lengthCM_SR04:
		#如果是第一次發現有人, 則開始計時.
		if statusSR04 == 0:
			print "第一次發現有人, 則開始計時"
			tmpTime_SR04 = timeit.default_timer()
			statusSR04 = 1
		else:
			#如果在SR04前面站的時間夠久, 且距離上次Welcome時間也夠長了, 則開始Welcome
			if (timeit.default_timer() - tmpTime_SR04) > timeLasted_SR04:
				print "在SR04前面站的時間夠久"
		                if (tmpLastWelcomeTime == 0 or (timeit.default_timer() - tmpLastWelcomeTime)>nextWelcomeTimer):
					print "距離上次Welcome時間也夠長"
                        		tmpLastWelcomeTime = timeit.default_timer()

		                        word_1 = getWords_1(nowHour)
		                        word_2 = getWords_2()

                		        words = word_1 + "  " + word_2
		                        print words
	
		                        #speaker = random.choice(speakerName)
		                        speakWords(words, "Bruce", 15600, 0)


	#如果沒人站在前面
	else:
		#如果是剛離開
		if statusSR04 == 1:
			print "您站了" + str(timeit.default_timer() - tmpTime_SR04) + "秒鐘。"
			statusSR04 = 0
			tmpTime_SR04 = 0
	
