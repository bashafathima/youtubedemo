import pandas as pd
from googleapiclient.discovery import build
from langdetect import detect, DetectorFactory
from datetime import datetime
from datetime import timezone
import psycopg2 as pg
import re,os
os.system('cls')
DetectorFactory.seed = 0
non_english_pattern = r'[^a-zA-Z\s]+' 
extrasymbol =r'[[]\s] +'

con = pg.connect(database="Casestudy1",user="postgres",password="1234567",host="localhost",port="5432")
cursor=con.cursor()
replacements = {'(': '', ')': '','':'','#':'',',':'','&':'',';':''}
API_KEY = "AIzaSyA6j_KOjqW0MgDklZLeW2as_Y827lhu3jE"
appitest =build("youtube", "v3", developerKey=API_KEY)

def ExtractDetails (jsonrequest,type):
    response = jsonrequest.execute()
    items = response.get('items', [])
    video_details = []
    for item in items:
        title = item['snippet'].get('title', '')
        description = item['snippet'].get('description', '')
        channelid = item['snippet'].get('channelId', '')
        if(type == "playList"):
                playlistid= item["id"]
        try:
            title_lang = detect(title)
            description_lang = detect(description)
        except:
            title_lang = 'unknown'  
            description_lang = 'unknown'
        if title_lang == 'en' and description_lang == 'en' and channelid != '':
            channelid =''.join([replacements.get(char, char) for char in channelid])
            title= item['snippet'].get('title', 'N/A'),
            title =''.join([replacements.get(char, char) for char in title])
            title = re.sub(non_english_pattern, '', title)  
            description= item['snippet'].get('description', 'N/A'),
            description =''.join([replacements.get(char, char) for char in description])
            description=description.replace("'","")
            description=re.sub(non_english_pattern, '', description)  
            categoryId =item['snippet'].get('categoryId', 'N/A'),
            categoryId =''.join([replacements.get(char, char) for char in categoryId])
            published_at= item['snippet'].get('publishedAt', 'N/A'),
            published_at =''.join([replacements.get(char, char) for char in published_at])
            published_at=datetime.fromisoformat(published_at).astimezone(timezone.utc)
            published_at.strftime('%Y-%m-%d %H:%M:%S')
            channel_title= item['snippet'].get('channelTitle', 'N/A'),
            channel_title =''.join([replacements.get(char, char) for char in channel_title])
            thumbnail_url= item['snippet']['thumbnails']['default'].get('url', 'N/A')
            if(type == "channelList"):
                qry ='''INSERT INTO channels  
                        (channelid,categoryId,title, description, published_at, channel_title, thumbnail_url) 
                    VALUES('%s','%s','%s','%s','%s','%s','%s')
                    '''% (channelid.strip(),categoryId.strip(),title.strip(),description.strip(),published_at,channel_title.strip(),thumbnail_url)
                print(qry)
                cursor.execute(qry)
                con.commit()
            if(type == "playList"):
                qry ='''INSERT INTO Playlist(channelid,Playlistid,title, description) 
                    VALUES('%s','%s','%s','%s')
                    '''% (channelid.strip(),playlistid.strip(),title.strip(),description.strip())
                print(qry)
                cursor.execute(qry)
                con.commit()
            if(type == "playListItem"):
                playlistid= item['snippet'].get('playlistId', 'N/A'),
                playlistid =''.join([replacements.get(char, char) for char in playlistid])
                videoId= item['contentDetails'].get('videoId', 'N/A'),
                videoId =''.join([replacements.get(char, char) for char in videoId])
                qry ='''INSERT INTO PlaylistItem  
                        (channelid,Playlistid,videoId,published_at,title, description) 
                    VALUES('%s','%s','%s','%s','%s','%s')
                    '''% (channelid.strip(),playlistid.strip(),videoId,published_at,title,description)
                print(qry)
                cursor.execute(qry)
                con.commit()
            if(type == "VideoTags"):
                videoId= item["id"]
                tags= item['snippet'].get('tags', '')
                tags =str(tags).replace("[","")
                tags =str(tags).replace("]","")
                tags =str(tags).replace("'","")
                if(tags != ''):
                    qry ='''INSERT INTO VideoList (channelid,videoId,tags) 
                        VALUES('%s','%s','%s') '''% (channelid.strip(),videoId,tags)
                    print(qry)
                    cursor.execute(qry)
                    con.commit()

                # for tagsitem in tags:
                #     qry ='''INSERT INTO VideoList  
                #             (channelid,videoId,tags) 
                #         VALUES('%s','%s','%s')
                #         '''% (channelid.strip(),videoId,tagsitem)
                #     print(qry)
                #     cursor.execute(qry)
                #     con.commit()

def ChannelList():
    channelrequest = appitest.search().list(
        part="snippet",
        maxResults=50,
        q=input()
    )
    return channelrequest
# ExtractDetails(ChannelList(),"channelList")

def Playlist():
    qry="select distinct channelid,channel_title from channels"
    cursor.execute(qry)
    con.commit()
    lst = cursor.fetchall()
    for channelid,channel_title in lst:
        playlistrequest = appitest.playlists().list(
            part="snippet,contentDetails",
            channelId=channelid,
            maxResults=10
        )
        ExtractDetails(playlistrequest,"playList")

def PlayListItem():
    qry="select Playlistid,title from Playlist "
    cursor.execute(qry)
    con.commit()
    lst = cursor.fetchall()
    for Playlistid,title in lst:
        playlistItemsrequest = appitest.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=25,
            playlistId=Playlistid
        )
        ExtractDetails(playlistItemsrequest,"playListItem") 

def VideoTags():
    qry="select videoId,title from PlaylistItem "
    cursor.execute(qry)
    con.commit()
    lst = cursor.fetchall()
    for videoId,title in lst:
        videorequest = appitest.videos().list(
                part="snippet,contentDetails,statistics",
                id=videoId
        )
        ExtractDetails(videorequest,"VideoTags") 

# Playlist()
# PlayListItem()
# VideoTags()