import streamlit as st
import psycopg2 as pg
import pandas as pd
import os
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
dfloaddata=  LoadData(str(option))
dfloaddata= dfloaddata[['url', 'videoid']].head(2) 
def display_video_grid():
    col1 = st.columns(1)
    with col1:
        st.header("Video 1")
        st.video(dfloaddata["url"])
if __name__ == "__main__":
    display_video_grid()
# st.write(dfloaddata)

# Number of videos per page
# VIDEOS_PER_PAGE = 6

# # Calculate total number of pages
# total_pages = len(dfloaddata) // VIDEOS_PER_PAGE + (1 if len(dfloaddata) % VIDEOS_PER_PAGE > 0 else 0)

# # Pagination control
# page = st.slider("Select page", 1, total_pages, 1)

# # Calculate the start and end index for the current page
# start_idx = (page - 1) * VIDEOS_PER_PAGE
# end_idx = min(start_idx + VIDEOS_PER_PAGE, len(dfloaddata))

# Display the current page of videos
# def update_value(x):
#     return f"https://www.youtube.com/watch?v=VIDEO_ID{x}"

# dfloaddata['videoId'] = dfloaddata[['videoid']].apply(update_value)
# current_videos = dfloaddata[start_idx:end_idx]
# num_columns = 1
# columns = st.columns(num_columns)
# for i, video in enumerate(dfloaddata):
    # col = "1"#columns[i % num_columns]
    # with col:
        # st.write(dfloaddata["title"])

# st.write(dfloaddata)
# Function to update session state

# selected_option = st.selectbox("Choose an option", options, 
#                                index=options.index(st.session_state.selected_option) if st.session_state.selected_option else 0)
# st.write("You selected:", selected_option)
# st.video(video_url)
# if __name__ == '__main__':
    # if option != None:
    #     dfvideo =LoadData(option)
    #     video_id= "SUgejgd6v7I"
    #     video_url = f"https://www.youtube.com/watch?v={video_id}"

    