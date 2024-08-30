from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import pickle 
import psycopg2 as pg
import pandas as pd
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import streamlit as st 
from streamlit_searchbox import st_searchbox
from streamlit_player import st_player
st.set_page_config(layout="wide")
def create_connection():
    engine = pg.connect(database="youtube",user="postgres",password="youtube_123",host="youtubedemo.chc4aisqwah3.ap-south-1.rds.amazonaws.com",port="5432")
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
    qry="""	select 'live' as tags , 10 as cnt  union all
            select distinct translate( unnest(string_to_array(tags, ',')),'"''#&,', '') as tags,count(videoId)cnt
        from VideoList group by tags
	order by tags """
    df = fetch_data(qry, conn)
    df[["cnt"]] =df[["cnt"]].apply(pd.to_numeric)
    filter = df["cnt"] > 10
    df.where(filter, inplace=True)
    df=df.drop_duplicates(['tags'])[['tags']]
    return df
dftag =LoadTagData()
def determine_n_clusters(num_videos):
    return max(2, num_videos // 5)  # Ensure at least 2 clusters
def determine_n_clusters(num_videos):
    return min(max(2, num_videos // 5), 5)
def LoadData(option):
   
    option = "%" + option +"%"
    base_query="""select distinct
       'https://www.youtube.com/watch?v='||vl.videoId as url,
        vl.videoid,
        channel_title,plIt.title,plIt.description,vl.tags from channels ch 
        inner join Playlist pl on ch.channelid=pl.channelid
        inner join PlaylistItem plIt on plIt.Playlistid=pl.Playlistid and pl.channelid=plIt.channelid
        inner join VideoList vl on vl.videoId=plIt.videoId"""
    query = base_query
    params = []
    if option:
        query += ''' WHERE tags like '%s' '''% option
       
    print("Executing query:", query)
    df = fetch_data(query, conn)
    return df
def get_similar_videos(similar_videos_indices,video_index, top_n=5):
    similar_indices = similar_videos_indices[:top_n]
    similar_videos = df.iloc[similar_indices]
    return similar_videos[['url','videoid', 'title', 'tags', 'description']]
def KmeanMLCalc(df):
    df['combined_text'] = df['tags'] 
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(df['combined_text'])
    num_clusters = determine_n_clusters(len(df.index))  # Adjust as needed
    for init_method in ['k-means++', 'random']:
        kmeans = KMeans(n_clusters=num_clusters, init=init_method, random_state=42)
        # clusters = kmeans.fit_predict(X)
        # unique_clusters = set(clusters)
        with open( init_method+'.pkl', 'wb') as file:
            pickle.dump(kmeans, file)
        
        # print(f"Initialization method: {init_method}")
        # print(f"Unique clusters found: {len(unique_clusters)}")
        # if len(unique_clusters) > 1:
        #     score = silhouette_score(X, clusters)
        #     print(f"Silhouette Score: {score}\n")
        # else:
        #     print("Not enough clusters to compute silhouette score.\n")
    for init_method in ['k-means++', 'random']:
        with open(init_method+'.pkl', 'rb') as file:
            kmeans = pickle.load(file)
        clusters = kmeans.fit_predict(X)
        unique_clusters = set(clusters)
        st.write(f"Initialization method: {init_method}")
        st.write(f"Unique clusters found: {len(unique_clusters)}")
        if len(unique_clusters) > 1:
            score = silhouette_score(X, clusters)
            st.write(f"Silhouette Score: {score}\n")
            inertia = kmeans.inertia_
            print(f'Inertia: {inertia}')
            st.write("Inertia:", inertia)
        else:
            st.write("Not enough clusters to compute silhouette score.\n")
        
    # kmeans = KMeans(n_clusters=num_clusters,  random_state=42)
    # kmeans.fit(X)
    # with open('kmeans_model.pkl', 'wb') as file:
    #     pickle.dump(kmeans, file)
    # with open('kmeans_model.pkl', 'rb') as file:
    #     loaded_kmeans = pickle.load(file)
    # df['cluster'] = loaded_kmeans.fit_predict(X)
    # pca = PCA(n_components=2)
    # X_reduced = pca.fit_transform(X.toarray())
    # silhouette_avg = silhouette_score(X, df['cluster'])
    # print(f'Silhouette Score: {silhouette_avg}')
    # st.write("Silhouette Score:", silhouette_avg)
    # inertia = loaded_kmeans.inertia_
    # print(f'Inertia: {inertia}')
    # st.write("Inertia:", inertia)

    # Example: Get the feature vector of a specific video
    video_index = 0  # Index of the video you're interested in
    video_vector = X[video_index]

    # Compute similarity with all other videos
    similarity_scores = cosine_similarity(video_vector, X)
    similar_videos_indices = np.argsort(similarity_scores[0])[::-1]
    # Retrieve and display similar videos
    # Example: Get top 5 similar videos to the video with index 0
    similar_videos = get_similar_videos(similar_videos_indices,0, top_n=5)
    dfloaddata= similar_videos[['url', 'videoid']].head(5) 
    return dfloaddata
left, right = st.columns([10,4],gap = "small")
st.title("My YouTube-like App")
st.sidebar.title("Navigation")

# Sidebar for navigation
sidebar_options = ["Home", "Trending", "Subscriptions"]
choice = st.sidebar.radio("Go to", sidebar_options)
def update_state(selected_option):
    st.session_state.selected_option = selected_option
    st.header("Home")
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
if choice == "Home":
    
    df =LoadData(str(option))
    dfloaddata= KmeanMLCalc(df)

    for index, row in dfloaddata.iterrows():
        st_player(row['url'],key=row['videoid'])
elif choice == "Trending":
    st.header("Trending")
    option ="Trending"
    df =LoadData(str(option))
    print(df)
    dfloaddata= KmeanMLCalc(df)
    for index, row in dfloaddata.iterrows():
        st_player(row['url'],key=row['videoid'])
elif choice == "Subscriptions":
    st.header("Subscriptions")
    # Example subscriptions
    st.write("List of channels you're subscribed to.")

# Footer
st.write("Footer content here")
