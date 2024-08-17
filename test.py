from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import psycopg2 as pg
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import streamlit as st 
from streamlit_searchbox import st_searchbox
from streamlit_player import st_player

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
left, right = st.columns([10,4],gap = "small")

def update_state(selected_option):
    st.session_state.selected_option = selected_option
with left:


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
df =LoadData(str(option))

df['combined_text'] = df['tags'] + ' ' + df['description']

# with right:
#     Search = st_searchbox(df['combined_text'] , label="Player 1", key="player1_search")
# st.markdown("***")
# st.header(f"{Search}")
# st.error("No matches found between these players.")

vectorizer = TfidfVectorizer(stop_words='english')
X = vectorizer.fit_transform(df['combined_text'])
if len(df.index) < 5:  
    cnt=3
elif len(df.index) > 5 and len(df.index)<=50 :
    cnt=5
elif len(df.index) > 50 and len(df.index)<=100 :
    cnt=10
elif len(df.index) > 100 and len(df.index)<=150 :
    cnt=50
else :
    cnt=100
num_clusters = int(cnt)  # Adjust as needed
kmeans = KMeans(n_clusters=num_clusters, init="random", n_init=1,max_iter=1000, random_state=42)
df['cluster'] = kmeans.fit_predict(X)
# print(df)
pca = PCA(n_components=2)
X_reduced = pca.fit_transform(X.toarray())

# Create a DataFrame for visualization
df_pca = pd.DataFrame(X_reduced, columns=['PC1', 'PC2'])
df_pca['cluster'] = df['cluster']


# Plot the clusters
plt.figure(figsize=(10, 6))
for cluster in df['cluster'].unique():
    cluster_data = df_pca[df_pca['cluster'] == cluster]
    # plt.scatter(cluster_data['PC1'], cluster_data['PC2'], label=f'Cluster {cluster}')

with left:
    silhouette_avg = silhouette_score(X, df['cluster'])
    print(f'Silhouette Score: {silhouette_avg}')
    st.write("Silhouette Score:", silhouette_avg)
    inertia = kmeans.inertia_
    print(f'Inertia: {inertia}')
    st.write("Inertia:", inertia)
with right:
    clustered_df = df[['url','videoid', 'title', 'combined_text', 'cluster']]

    # Group by cluster and aggregate tags and descriptions
    cluster_summary = clustered_df.groupby('cluster').agg({
        'combined_text': ' '.join
    }).reset_index()
    # st.markdown("***")
    # st.header(f"cluster_summary")
    # st.write(cluster_summary)


    def get_related_videos(cluster_label):
        related_videos = df[df['cluster'] == cluster_label]
        return related_videos[['url','videoid', 'title', 'tags', 'description']]

    # Example: Get videos from Cluster 0
    cluster_0_videos = get_related_videos(0)
    print("----------------get_related_videos-----------------")
    st.markdown("***")
    st.header(f"get related videos")
    # st.write(cluster_0_videos)
    dfrelated= cluster_0_videos[['url', 'videoid']].head(5) 

    for index, row in dfrelated.iterrows():
        print(row['url'], row['videoid'])
        st_player(row['url'],key=row['videoid'])
with left:
    # Example: Get the feature vector of a specific video
    video_index = 0  # Index of the video you're interested in
    video_vector = X[video_index]

    # Compute similarity with all other videos
    similarity_scores = cosine_similarity(video_vector, X)
    similar_videos_indices = np.argsort(similarity_scores[0])[::-1]

    # Retrieve and display similar videos
    def get_similar_videos(video_index, top_n=5):
        similar_indices = similar_videos_indices[:top_n]
        similar_videos = df.iloc[similar_indices]
        return similar_videos[['url','videoid', 'title', 'tags', 'description']]

    # Example: Get top 5 similar videos to the video with index 0
    similar_videos = get_similar_videos(0, top_n=5)
    st.markdown("***")
    st.header(f"get similar videos Top5")
    print("-----------------similar_videos--------------")
    # st.write(similar_videos)

    # plt.xlabel('Principal Component 1')
    # plt.ylabel('Principal Component 2')
    # plt.title('Video Clustering')
    # plt.legend()
    # plt.show() 
    dfloaddata= similar_videos[['url', 'videoid']].head(5) 

    for index, row in dfloaddata.iterrows():
        print(row['url'], row['videoid'])
        st_player(row['url'],key=row['videoid'])
# if __name__ == '__main__':
