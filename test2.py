import streamlit as st
import psycopg2 as pg
import pandas as pd
import os
from streamlit_player import st_player
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
os.system('cls')
def create_connection():
    engine = pg.connect(database="Casestudy1",user="postgres",password="1234567",host="localhost",port="5432")
    print("Connected to PostgreSQL database!")
    return engine
conn = create_connection()
cursor=conn.cursor()
def fetch_data(query, conn,param=""):
    try:
        if param == "":
            df = pd.read_sql(query, conn)
        else:
            cursor.execute(query,param)
            # df  =  cursor.fetchall()
            df = pd.read_sql(query, conn,params=param)
        return df
    except pg.Error as e:
        print(f"Error executing query: {e}")

def LoadTagData():
    qry="""	select 'live' as tags union all
            select distinct unnest(string_to_array(tags, ',')) as tags
        from VideoList"""
    df = fetch_data(qry, conn)
    return df
dftag =LoadTagData()
def LoadData(option):
    option = "%" + option +"%"
    base_query="""select distinct 'https://www.youtube.com/watch?v='||vl.videoId as url,
        vl.videoid,
        channel_title,plIt.title,plIt.description,vl.tags from channels ch 
        inner join Playlist pl on ch.channelid=pl.channelid
        inner join PlaylistItem plIt on plIt.Playlistid=pl.Playlistid and pl.channelid=plIt.channelid
        inner join VideoList vl on vl.videoId=plIt.videoId"""
    query = base_query
    params = []
    if option:
        query += ''' WHERE tags like '%s' '''% option
        # conditions = []
        # for item in filters.items():
        #     conditions.append(f"{key} ='{str(value).strip()}'")
        #     params.append(value)
        
        # query += " AND ".join(conditions)
    print("Executing query:", query)
    # print("With parameters:", params)
    df = fetch_data(query, conn)
    return df
def update_state(selected_option):
    st.session_state.selected_option = selected_option

# Initialize session state if not already set
if 'selected_option' not in st.session_state:
    st.session_state.selected_option = None
options =dftag['tags']
option = st.selectbox(
    "How would you like to be search?",
    options,
    index=0,
    placeholder="Select contact method...",
    
)
st.write("You selected:", option)


# dfloaddata= dfloaddata[['url', 'videoid']].head(5) 

# for index, row in dfloaddata.iterrows():
#     print(row['url'], row['videoid'])
#     st_player(row['url'],key=row['videoid'])


    