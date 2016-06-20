#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

#PIN configuration
pinOutControl = 40
pinPIR = 38
trigSR04 = 35
echoSR04 = 37

#Global Parameters
lengthCM_SR04 = 90  #距離SR04在幾公分以內, 才認定為正開始使用照護系統
timeLasted_SR04 = 2  #有人站在SR04面前持續了幾秒後, 才認定為要始用照護系統
nextWelcomeTimer = 180  #上次Welcome之後, 至少要隔多久才能再Welcome 

#speakerName = ["Bruce", "Theresa", "Angela" "TW_LIT_AKoan", "TW_SPK_AKoan"]


#-------------------------------------------------
tmpTime_SR04 = 0  #開始計時時的秒數, 用於計算timeLasted_SR04
statusSR04 = 0

tmpLastWelcomeTime = 0  #上次的歡迎時間
tmpLastAskForHere = 0	#上次的請經過的人(PIR)使用時間

import RPi.GPIO as GPIO
import time
import timeit
import speechClass
import json
import os
import random
import urllib
import logging
logger = logging.getLogger('main')
hdlr = logging.FileHandler('/home/pi/health/main.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

import pygame
pygame.mixer.init(15200, -16, 1, 1024)

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

def number2speakwords(numValue):
        strTMP = str(numValue)
        unitSpeak = ["", "十", "百", "千", "萬", "十", "百", "千"]

        if strTMP.find('.')==-1:
                strIntNum = strTMP
                strDecimal = ""
        else:
                NumSplit = strTMP.split('.')
                strIntNum = NumSplit[0]
                strDecimal = NumSplit[1]

        print "INT:" + strIntNum + " --> length:" + str(len(strIntNum))
        print "DEC:" + strDecimal + " --> length:" + str(len(strDecimal))

        if len(strIntNum)>2 and strIntNum[len(strIntNum)-2]=="0": #十位是0
                if strIntNum[len(strIntNum)-1]!="0":
                        unitSpeak[1] = '零'
                else:
                        unitSpeak[1] = ''
        if len(strIntNum)>3 and strIntNum[len(strIntNum)-3]=="0": #百位是0
                unitSpeak[2] = ' '
        if len(strIntNum)>4 and strIntNum[len(strIntNum)-4]=="0": #千位是0
                unitSpeak[3] = ' '

        if len(strIntNum)>5:
                if strIntNum[len(strIntNum)-5]!="0": #萬位不是0
                        unitSpeak[4] = "萬"
                else:
                        unitSpeak[4] = ' '

                        if len(strIntNum)>5 and strIntNum[len(strIntNum)-6]!="0": #萬位是0, 十萬位不是0
                                unitSpeak[5] = "十萬"
                        elif len(strIntNum)>6 and strIntNum[len(strIntNum)-7]!="0": #十萬位是0, 百萬位不是0
                                unitSpeak[6] = "百萬"
                        elif len(strIntNum)>7 and strIntNum[len(strIntNum)-8]!="0": #百萬位是0, 千萬位不是0
                                unitSpeak[7] = "千萬"

        stringIntSpeak = ""
        for i in range(0, len(strIntNum)):
                stringIntSpeak = stringIntSpeak + strIntNum[i] + unitSpeak[len(strIntNum)-i-1]
                i=i+1

        stringIntSpeak = stringIntSpeak.replace("0", "")

	if len(strDecimal)>0:
        	return stringIntSpeak + "點" + strDecimal
	else:
		 return stringIntSpeak

def getWeather():
	link = "http://data.sunplusit.com/Api/WeatherUVIF"
	f = urllib.urlopen(link)
	myfile = f.read()
	jsonData = json.loads(myfile)
	nowUV = "而目前室外紫外線指數是" + jsonData[0]['UVIStatus'] + ", " +  jsonData[0]['ProtectiveMeasure']

	link = "http://data.sunplusit.com/Api/WeatherCWB"
        f = urllib.urlopen(link)
        myfile = f.read()
        jsonData = json.loads(myfile)
	nowWeather_tmp = "目前室外的氣象是" + jsonData[0]['Weather'] + ", " + jsonData[0]['Precipitation'] + ", " + jsonData[0]['Temperature'] + ", " +  jsonData[0]['RelativeHumidity'] + ", 整體來說氣候是" + jsonData[0]['ConfortIndex']
	nowWeather = nowWeather_tmp.replace("為", "是 ")

	link = "http://data.sunplusit.com/Api/WeatherAQX"
        f = urllib.urlopen(link)
        myfile = f.read()
        jsonData = json.loads(myfile)
	nowAir_tmp = "另外, 關於室外空氣指數部份, 目前室外的PM2.5數值為" + number2speakwords(jsonData[0]['PM25']) + ", PM十的數值為" + number2speakwords(jsonData[0]['PM10']) + ", 空氣品質PSI指數為" + number2speakwords(jsonData[0]['PSI']) + ", 整體來說空氣品質" + jsonData[0]['Status'] + ", " + jsonData[0]['HealthEffect'] + ", 建議" + jsonData[0]['ActivitiesRecommendation']
	nowAir_tmp = nowAir_tmp.replace(".", "點")
	nowAir = nowAir_tmp.replace("為", "是 ")

	return nowWeather + " , " + nowUV + nowAir

def getWAV_1(vHour):
	'''
	a1	早安
	a2	Good Morning
	a3	早
	a4	早上愉快
	a5	Have a nice day.
	
	b1	午安
	b2	吃中餐了嗎?
	b3	午餐時間快到了
	b4	午安, 早上忙嗎?
	b5	休息一下, 快中午了.
	
	c1	午安.
	c2	午安, 忙嗎？
	c3	Good afternoon.
	c4	Good afternoon. 午安.
	c5	午安, 休息一下.

	d1	Good evening, 晚安
	d2 	晚安, 要準備下班了嗎?
	d3	您好, 今天忙嗎?
	d4	晚安, 忙了一天, 請休息一下.
	d5	晚安, 忙碌的一天又快結束了.

	e1	很晚了, 還不準備下班嗎?
	e2	晚安, 不要加班加太晚, 請早點下班, 
	e3	時間不早了, 忙了一天, 早點休息吧.
	e4	晚安, 又是忙碌的一天, 辛苦了.
	e5	晚安, 很晚了, 要準備下班了嗎?

	f1	辛苦你了
	f2	加班辛苦了
	'''
	if vHour>=5 and vHour<11:
                wordArray_1 = ["a1", "a2", "a3", "a4", "a5"]
        elif vHour>=11 and vHour<13:
                wordArray_1 = ["b1", "b2", "b3", "b4", "b5"]
        elif vHour>=13 and vHour<17:
                wordArray_1 = ["c1", "c2", "c3", "c4", "c5"]
        elif vHour>=17 and vHour<20:
                wordArray_1 = ["d1", "d2", "d3", "d4", "d5"]
        elif vHour>=20 and vHour<24:
                wordArray_1 = ["e1", "e2", "e3", "e4",  "e5"]
        elif vHour>=0 and vHour<5:
                wordArray_1 = ["f1", "f2"]

        return random.choice(wordArray_1)

def getWAV_2():
	'''
	welcome1	歡迎使用福委會的員工照護系統
	welcome2	歡迎您使用福委會員工照護系統
	'''
	wordArray_2 = ["welcome1", "welcome2"]
	return random.choice(wordArray_2)

def getWAV_3():
	wordArray = ["h1", "h2", "h3", "h4", "h5"]
	return random.choice(wordArray)

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


def play_wav(wav_filename):
	pygame.mixer.music.load(wav_filename)
	pygame.mixer.music.play()
	while pygame.mixer.music.get_busy() == True:
		continue

def readSR04_org():
	signalon = time.time()
    	signaloff = time.time()
        time.sleep(0.5)

        GPIO.output(trigSR04, True)
        time.sleep(0.00001)
        GPIO.output(trigSR04, False)

        while GPIO.input(echoSR04) == 0:
          	signaloff = time.time()
	while GPIO.input(echoSR04) == 1:
       		signalon = time.time()
        
	timepassed = signalon - signaloff
	distance = timepassed * 17000
	#if distance>3400:
	#	distance = 3400
	#if distance<10:
        #        distance = 10

	print "     PIR: " + str(GPIO.input(pinPIR)) + " / HSR04: " + str(distance)
        
        return distance

def readSR04():
	time.sleep(0.1)

	GPIO.output(trigSR04, True)

	# set Trigger after 0.01ms to LOW
	time.sleep(0.00001)
	GPIO.output(trigSR04, False)

	StartTime = time.time()
	StopTime = time.time()

	exitError = 0
	i = 0
	# save StartTime
	while GPIO.input(echoSR04) == 0:
		StartTime = time.time()
		i = i + 1
		#print "      wait for echo==0 ---> " + str(i)
		if i>2000:
			exitError = 1
			break

	# save time of arrival
	i = 0
	while GPIO.input(echoSR04) == 1:
		StopTime = time.time()
		i = i + 1
                #print "      wait for echo==1 ---> " + str(i)
		if i>20000:
			exitError = 1
                        break


	# time difference between start and arrival
	TimeElapsed = StopTime - StartTime
	# multiply with the sonic speed (34300 cm/s)
	# and divide by 2, because there and back
	distance = (TimeElapsed * 34029) / 2
	#distance = TimeElapsed / 0.000058
	#GPIO.cleanup()

	if exitError == 1:
		distance = 2500

	#if distance>2500 or distance<4:
        #       distance = 2500
        time.sleep(0.1)

	print "     PIR: " + str(GPIO.input(pinPIR)) + " / SR04:" + str(statusSR04) + " / HSR04--> " + str(distance)
	return distance


def getDistance():
	sampleCounts = 3  #要取幾次標本

	count = 0
	maxValue = 0
	minValue = 99999
	totalValue = 0

	while(count<sampleCounts):
		valueSR04 = readSR04()
		#if GPIO.input(pinPIR)==1:
		while valueSR04<4 or valueSR04>4400:
			valueSR04 = readSR04()
			#print valueSR04

		if valueSR04>maxValue:
			maxValue = valueSR04
		if valueSR04<minValue:
			minValue = valueSR04

		totalValue += valueSR04
		count += 1

	avgDistance = (totalValue-maxValue-minValue) / (sampleCounts-2)
	
	#logger.info(str(avgDistance) + 'cm')
	return avgDistance

try:
	while True:


		dt = list(time.localtime())
		nowYear = dt[0]
		nowMonth = dt[1]
		nowDay = dt[2]
	        nowHour = dt[3]
	        nowMinute = dt[4]

		statusPIR = GPIO.input(pinPIR)

		#如果有人站在前面
		nowDistance = getDistance()
		logger.info( "PIR:" + str(GPIO.input(pinPIR)) + " / HSR04:" + str(nowDistance) + "cm")

		if nowDistance<lengthCM_SR04:
			#如果是第一次發現有人, 則開始計時.
			if statusSR04 == 0:
				logger.info( str(nowDistance) + "cm  --> 第一次發現有人, 開始計時")
				tmpTime_SR04 = timeit.default_timer()
				statusSR04 = 1
				time.sleep(0.1)
			else:
				#如果在SR04前面站的時間夠久, 且距離上次Welcome時間也夠長了, 則開始Welcome
				if (timeit.default_timer() - tmpTime_SR04) > timeLasted_SR04:
					logger.info( str(nowDistance) + "cm  --> SR04前面站的時間夠久.")

			                if (tmpLastWelcomeTime == 0 or (timeit.default_timer() - tmpLastWelcomeTime)>nextWelcomeTimer):
						logger.info( str(nowDistance) + "cm  --> 距離上次Welcome時間也夠長, 啟動體重計電源, 發出氣象訊息..")
	                        		tmpLastWelcomeTime = timeit.default_timer()

						GPIO.output(pinOutControl, GPIO.HIGH)
	                                        time.sleep(0.2)
	                                        GPIO.output(pinOutControl, GPIO.LOW)

			                        word_1 = getWAV_1(nowHour)
			                        word_2 = getWAV_2()
	
			                        play_wav("wav/man/"+word_1+".wav")
						play_wav("wav/man/"+word_2+".wav")
						time.sleep(1)
						play_wav("wav/man/g1.wav")
			                        #speaker = random.choice(speakerName)
						speakString = "今天" + str(nowYear) + "年" + number2speakwords(int(nowMonth)) + "月" + number2speakwords(int(nowDay)) + "日  " + number2speakwords(int(nowHour)) + "點" + number2speakwords(int(nowMinute)) + "分  ," + getWeather()
						logger.info(speakString)
						speakWords(speakString, "MCHEN_Bruce", 15600, 0)

		#如果沒人站在前面
		else:
			#如果是剛離開
			if statusSR04 == 1:
				timeDuring = "您站了" + str(timeit.default_timer() - tmpTime_SR04) + "秒鐘。"
				logger.info( str(nowDistance) + "cm  -->" + timeDuring)
				statusSR04 = 0
				tmpTime_SR04 = 0

			else:
				if (timeit.default_timer() - tmpLastAskForHere) > nextWelcomeTimer:	#如果距離上次welcome時間過了很久
					if statusPIR==1:	#如果有人在附近
						tmpLastAskForHere = timeit.default_timer()
						word_3 = getWAV_3()
						logger.info("有人, 播放邀請使用檔 "+word_3+".wav")
						print "    -> 有人, 播放邀請使用檔 "+word_3+".wav"
						play_wav("wav/man/"+word_3+".wav")
					else:
						print "    -> 沒有人, 不播放邀請使用檔 "

				else:
					if statusPIR==1:
						print "    -> 有人, 但剛播放不久, 不再播放邀請使用檔 "
						logger.info("有人, 但剛播放不久, 不再播放邀請使用檔")
except Exception,e:
                print str(e)
		logger.info(e)
