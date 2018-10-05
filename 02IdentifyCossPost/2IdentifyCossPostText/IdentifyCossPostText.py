# -*- coding: utf-8 -*-
# match same post by text similarity

# input1: IdentifySameUser    # generated by TwitterFacebookData2017\01IdentifySameUser 
# twitterID #followr #twitterUrl #sameLongUrl FacebookID #likes #facebookUrl     howMatchUserID        twitterName       facebookName   timeZone 
# 109118967	3904208	41	    5	113525172018777	2464791	12	FacebookFromTwitterProfiles	jaimecamil	jaimecamil      -14400
# 62477022	244525	15	    7	192465074360	1724259	14	FacebookFromTwitterProfiles	andaadam	AndaAdamOfficial -18000
#   0           1       2           3           4         5     6                    7                   8                   9             10

# input2: FormatTwitterTweets:
#    userID       TweetID            #RT #favorite #comment    date         isRT isRep      expandURL    #mentions #hashtage   text
#|::|14985126|::|714569507218456577|::|1|::|2|::|0|::|2016-03-28 21:47:01|::|0|::|0|::|http://bit.ly/1LammK9|::|0|::|0|::|What to https://t.co/WdNuNLJ0Mu|;;|
#    0                  1              2    3    4               5           6    7            8                9    10        11   

# input3: FormatFacebookFeeds
# userID		feedID	#shares	#likes	#comments	created_time	    type	status_type	link	            name	description	message
#|::|94319190752|::|10153640287040753|::|0|::|5|::|1|::|2016-04-14 00:00:00|::|link|::|shared_story|::|http://www.patheos.com|::|Are Polytheists |::|Why is|::|Yvonne|;;|
#       0               1                2     3    4              5                   6          7              8                        9            10       11

# output: IdentifyCossPostText  # is used for Question2EffectIdeal, Question3PostAll, and experiments     
# twUserID	twTweetID	fbUserID	fbFeedID  urlOrderNum #twRT #twFavorite	#twComment #fbReshare #fbLikes #fbComment timeDifference  twitterName facebookName 
# 19019298	7.14543E+17	37791069588	1.01541E+16	13	1	1	    0	        0	0	0	    -4	        IAmBiotech	IAmBiotech
# 13877002	7.15385E+17	72139486384	1.01541E+16	1	2	4	    0	        1	7	2	    -583	clarionledger	clarionledger
#   0              1                2             3             4       5       6           7           8       9       10           11               12            13

# output: IdentifyCossPostTextRepeat # is used for Question1Overlap
# this don't remove repeated tweet or feeds, for example, tA and tB in Twitter have same means and will match fC. this will generate result as below:
#  tA  fC
#  tB  fB


import urllib2
import urllib
import cookielib
import re
import datetime
import time
import sys
import os
import traceback
import math
#from nltk.metrics import edit_distance
import numpy as np
from scipy.spatial import distance

def printTime(beginTime):
    endTime = datetime.datetime.now() #calculate time
    print ("------------consumed-----------time-----------begin-----------")
    print ("consumed time:" + str(endTime - beginTime) )
    print ("------------consumed-----------time-----------end-------------")


def readSelectUsers(inFile1,userIdDictTW,userIdDictFB):
    fin = open(inFile1) 
    count =0
    selectCount = 0
    for current in fin:
        count += 1
        data = current.replace('\n','')
        curL = data.split('\t')
        twitterID = curL[0]
        facebookID = curL[4]
        UtcOffset = int(curL[10])/3600
        userIdDictTW[twitterID] = UtcOffset
        userIdDictFB[facebookID] = UtcOffset
    print '----readFacebookTwitter finished------len(userIdDictTW)----' + str(len(userIdDictTW)) + '----'
    print '----readFacebookTwitter finished------len(userIdDictFB)----' + str(len(userIdDictFB)) + '----'
    fin.close()

def readTweets(inFile2,userIdDictTW,userTweetDict):
    
    startTime = time.strptime('2016-03-15 00:00:00','%Y-%m-%d %H:%M:%S')
    #startTime = time.strptime('2016-04-13 00:00:00','%Y-%m-%d %H:%M:%S')  # needn't care about the start time 
    endTime = time.strptime('2016-04-15 00:00:00','%Y-%m-%d %H:%M:%S')    # the end time should be setted, because the most recent tweets have no retweets
    startTime1 = int(time.mktime(startTime))    
    endTime1 = int(time.mktime(endTime))
    
    fin = open(inFile2)
    columnMark =  '|::|'
    rowMark = '|;;|\n'  
    count =0
    for current in fin:
        count +=1
        if (count % 500000 ==0):
            print count        
        data = current[4:-5]
        curL = data.split(columnMark)
        userID = curL[0]
        #if userID not in userIdDictTW :
        #    continue
        if not userIdDictTW.has_key(userID):
            continue
        #if curL[8] == 'null':
        #    continue
        message = curL[11]
        TweetID = curL[1]
        retweet = curL[2]     # reshare for FB
        favorate = curL[3]    # Likes   for FB
        comment = curL[4]     # comment   for FB
        pubTime = curL[5]     # pubTime
        isRT = curL[6]  # it is '0' or '1' for Twitter, and it is link, status or photo for Facebook
        
        # ---------------------timezone-----------adjuct-----------------------------------begin-------------
        timeLag = userIdDictTW[userID]
        originalTime = datetime.datetime.strptime(pubTime,"%Y-%m-%d %H:%M:%S")
        adjustTime = originalTime + datetime.timedelta(hours = timeLag)  
        createdTime = adjustTime.strftime("%Y-%m-%d %H:%M:%S")    
        # ---------------------timezone-----------adjuct------------------------------------end-------------
        gettedTime = time.strptime(createdTime,'%Y-%m-%d %H:%M:%S') # 2012-06-11 07:03:04
        gettedTime1 = int(time.mktime(gettedTime))
        if( not (gettedTime1 >= startTime1 and gettedTime1 <= endTime1)): #---------------------not selected period----------------------------filter----------------- 
            #print time.strftime("%Y-%m-%d %X",gettedTime)
            continue                                                      
        if( isRT == '1'):                                                #-----------------------retweet in Twitter-------------------------filter-----------------
            continue
      
        
        if (not userTweetDict.has_key(userID)):
            userTweetDict.setdefault(userID,[])
            #userTweetDict[userID].append([TweetID,message,retweet,favorate,comment])
        
        userTweetDict[userID].append([TweetID,message,retweet,favorate,comment,pubTime])
        
    fin.close()
    print '----readTweets finished------len(userTweetDict)----' + str(len(userTweetDict)) + '----'
def computeTimeDifference(timeTW,timeFB):
    dateTW = time.strptime(timeTW,'%Y-%m-%d %H:%M:%S')  # 2012-06-11 07:03:04  
    dateFB = time.strptime(timeFB,'%Y-%m-%d %H:%M:%S') # 2012-06-11 07:03:04
    dateTW2=datetime.datetime(dateTW[0],dateTW[1],dateTW[2],dateTW[3],dateTW[4],dateTW[5])
    dateFB2=datetime.datetime(dateFB[0],dateFB[1],dateFB[2],dateFB[3],dateFB[4],dateFB[5])
    eclispedDay = (dateFB2 - dateTW2).days
    timeDiffernce = (dateFB2 - dateTW2).seconds
    timeDiffernce += eclispedDay*24*60*60 
    timeDiffernce = timeDiffernce/60  
    return timeDiffernce   # return how many sceonds
def compare(inFile1,userTweetDict,userFeedsDict,outFile):
    #-----------avoid one match multiple 20170227----------------------begin-------------------
    tweetIdCount = {} # tweetIdCount[tweetId] = 1  # this is used to remove multiple match, i.e., one tweet match muliple feeds, or one feed match multple tweet
    feedIdCount = {}  # feedIdCount[feedId] = 1
    tweetFeedDict = {} # tweetFeedDict[tweetId + feedId] = content needed to write outFile
    #-----------avoid one match multiple 20170227----------------------end---------------------
    fin = open(inFile1)   # IdentifySameUser
    # twitterID #followr #twitterUrl #sameLongUrl FacebookID #likes #facebookUrl     howMatchUserID        twitterName       facebookName   timeZone 
    # 109118967	3904208	41	    5	113525172018777	2464791	12	FacebookFromTwitterProfiles	jaimecamil	jaimecamil      -14400
    #   0           1       2           3           4         5     6                    7                   8                   9             10

    fout = open(outFile,'w')
    foutRepeat = open(outFile + 'Repeat','w')  # this used for Question1Overlap
    count = 0
    selectCount = 0
    tweetCount = 0
    feedCount = 0
    for current in fin:
        count += 1
        if(count % 100 == 0):
            print count
        data = current.replace('\n','')
        curL = data.split('\t')
        twitterID = curL[0]
        facebookID = curL[4]
        follower = curL[1]
        likes = curL[5]
        twitterName = curL[8]
        facebookName = curL[9]

        if(not userTweetDict.has_key(twitterID)): 
            continue
        if(not userFeedsDict.has_key(facebookID)):
            continue
        
        if userFeedsDict.has_key(facebookID):
            
            for valueTW in userTweetDict[twitterID]:
                textTW = valueTW[1]
            
                for valueFB in userFeedsDict[facebookID]:
                    textFB = valueFB[1]
                    #a = edit_distance(s1, s2, transpositions=False)                
                    #if a <= 20:
                    #    fout.write(valueTW[0] + '\t' +valueFB[0] +'\n' )
                    #else:
                    #s1 = cleanContent(textTW)          #------------------------------------clean  text  TW-------------------------------------
                    #s2 = cleanContent(textFB)          #------------------------------------clean  text  FB-------------------------------------
                    s1 = textTW
                    s2 = textFB
                    s1Set = set(s1.split())
                    s2Set = set(s2.split())
                    commonWords = s1Set & s2Set 
                    unionWords = s1Set | s2Set  
                    if(len(unionWords) == 0):
                        continue
                    Jaccard = round(float(len(commonWords)) / len(unionWords),4)
                    
                    if Jaccard >= 0.55:
                        cosine = CountVector(s1, s2)
                        #cosine = 0.2
                        if cosine <= 0.45:
                            #-----------avoid one match multiple 20170227----------------------begin-------------------
                            tweetId = valueTW[0]
                            feedId = valueFB[0]     
                            if(not tweetIdCount.has_key(tweetId)):
                                tweetIdCount[tweetId] = 0
                            tweetIdCount[tweetId] += 1
                            if(not feedIdCount.has_key(feedId)):
                                feedIdCount[feedId] = 0
                            feedIdCount[feedId] += 1                            
                            #-----------avoid one match multiple 20170227----------------------end---------------------

                            timeDiffernce = computeTimeDifference(valueTW[5],valueFB[5])
                            # userTweetDict[userID] = [TweetID,message,retweet,favorate,comment,pubTime]
                            writeContent = twitterID + '\t' + tweetId + '\t' + facebookID + '\t' + feedId + '\t'+  "0" + '\t'  + \
                                valueTW[2] + '\t'  + valueTW[3] + '\t'  + valueTW[4] + '\t'  + valueFB[2] + '\t'  + valueFB[3] + '\t'  + valueFB[4] + '\t' + \
                                str(timeDiffernce) + '\t'  + "null"+ '\t'  + "null" + '\n'
                            #fout.write(writeContent +'\n')
                            if(tweetFeedDict.has_key(tweetId + "," + feedId)):
                                print writeContent                            
                            tweetFeedDict[tweetId + "," + feedId] = writeContent
                            
    #-----------avoid one match multiple 20160920----------------------begin-------------------
    for (u,v) in tweetFeedDict.items():
        uSplit = u.split(",")
        tweetId = uSplit[0]
        feedId = uSplit[1]
        
        foutRepeat.write(v) 
        if(tweetIdCount[tweetId] > 1):
            #print "tweetId:" + tweetId
            continue
        if( feedIdCount[feedId] > 1):
            #print "feedId:" + feedId
            continue
        fout.write(v) 
    #-----------avoid one match multiple 20160920----------------------end---------------------
     


def CountVector(s1,s2):
    dic1 = CountKey(s1)
    dic2 = CountKey(s2)
    if(len(dic1) == 0 or len(dic2) == 0):
        return 1    
    (u,v) = MergeKeys(dic1, dic2)
    value = distance.cosine(u, v)
    return value
def CountKey(line ):
    #line = cleanContent(String)
    line = line.rstrip('')
    
    
    words = line.split( )  #空格分隔
       
    #字典插入与赋值
    table = {}
    for word in words:
        if table.has_key(word):      #如果存在次数加1
            num = table[word]
            table[word] = num + 1
        else:                
            table[word] = 1
    
    
    #键值从大到小排序 函数原型：sorted(dic,value,reverse)
    dic = sorted(table.iteritems(), key = lambda asd:asd[1], reverse = True)
    return dic

def MergeKeys(dic1,dic2): 
    arrayKey = []
    for i in range(len(dic1)):
        arrayKey.append(dic1[i][0])       #向数组中添加元素
    for i in range(len(dic2)):       
        if dic2[i][0] not in arrayKey:           #合并
            arrayKey.append(dic2[i][0])

    arrayNum1 = [0]*len(arrayKey)
    arrayNum2 = [0]*len(arrayKey) 

    for i in range(len(dic1)):     
        key = dic1[i][0]
        value = dic1[i][1]
        j = 0
        while j < len(arrayKey):
            if key == arrayKey[j]:
                arrayNum1[j] = value
                break
            else:
                j = j + 1
 
    for i in range(len(dic2)):     
        key = dic2[i][0]
        value = dic2[i][1]
        j = 0
        while j < len(arrayKey):
            if key == arrayKey[j]:
                arrayNum2[j] = value
                break
            else:
                j = j + 1
    return(arrayNum1,arrayNum2) 

def main(argv):
    inFile1 = argv[1]   # IdentifySameUser 
    inFile2 = argv[2]   # FormatTwitterTweets
    inFile3 = argv[3]   # FormatFacebookFeeds
    outFile = argv[4]   # IdentifyCossPostText
    
    userIdDictTW = {}   # userIdDictTW[idTW] = timezone
    userIdDictFB = {}   # userIdDictFB[idFB] = timezone
    userTweetDict = {}      # userTweetDict[userID] = [[TweetID,message,retweet,favorate,comment,pubTime],[TweetID,message,retweet,favorate,comment,pubTime],...,]
    userFeedsDict = {}      # userFeedsDict[userID] = [[FeedID,message, reshare, likes, comment,pubTime],[FeedID,message, reshare, likes, comment,pubTime],...,]
  
    reload(sys)
    sys.setdefaultencoding('utf-8')
    
    
    readSelectUsers(inFile1, userIdDictTW, userIdDictFB)
    readTweets(inFile2, userIdDictTW, userTweetDict)
    readTweets(inFile3, userIdDictFB, userFeedsDict)
    
    
    beginTime = datetime.datetime.now() 
    compare(inFile1, userTweetDict, userFeedsDict, outFile)


    printTime(beginTime)
    print "\a"
    print 'finish' 

    
if __name__ == "__main__":
    #ִmain fuction
    main(sys.argv)
