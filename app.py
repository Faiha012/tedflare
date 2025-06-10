import streamlit as st
import firebase_admin
from firebase_admin import auth, credentials, firestore
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Firebase Setup
if not firebase_admin._apps:
    import json
    firebase_secrets = st.secrets["firebase"]
    cred = credentials.Certificate(dict(firebase_secrets))
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Load TED Talks Data
df = pd.read_csv("ted_talks.csv")  

df.reset_index(inplace=True)
df.rename(columns={'index': 'id'}, inplace=True)

vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(df['tags'].fillna(''))

# Function to get recommendations using TF-IDF
def get_recommendations(talk_id, num_recommendations=5):
    idx = df[df['id'] == talk_id].index[0]
    sim_scores = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()
    similar_indices = np.argsort(sim_scores)[::-1][1:num_recommendations+1]
    return df.iloc[similar_indices][['title', 'url']]

# User Authentication
def signup(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        st.success("Account created successfully! Please login.")
    except Exception as e:
        st.error(str(e))

def login(email, password):
    try:
        user = auth.get_user_by_email(email)
        st.session_state["user"] = user.uid
        st.success("Logged in successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Login failed: {str(e)}")

def logout():
    st.session_state.pop("user", None)
    st.success("Logged out successfully!")

# Firestore Operations
def save_talk(user_id, talk_id):
    db.collection("users").document(user_id).set({
        "saved_talks": firestore.ArrayUnion([str(talk_id)])
    }, merge=True)

def watch_talk(user_id, talk_id):
    doc_ref = db.collection("users").document(user_id)
    doc_ref.set({"watched_talks": firestore.ArrayUnion([str(talk_id)])}, merge=True)
    
def like_talk(user_id, talk_id):
    db.collection("users").document(user_id).set({
        "liked": firestore.ArrayUnion([str(talk_id)])
    }, merge=True)
    
def unlike_talk(user_id, talk_id):
    db.collection("users").document(user_id).set({
        "liked": firestore.ArrayRemove([str(talk_id)])
    }, merge=True)

def get_user_preferences(user_id):
    doc = db.collection("users").document(user_id).get()
    if doc.exists and 'watched_talks' in doc.to_dict():
        return doc.to_dict()['watched_talks']
    return []

def get_saved_talks(user_id):
    doc = db.collection("users").document(user_id).get()
    if doc.exists and 'saved_talks' in doc.to_dict():
        return doc.to_dict()['saved_talks']
    return []

def unsave_talk(user_id, talk_id):
    db.collection("users").document(user_id).set({
        "saved": firestore.ArrayRemove([str(talk_id)])
    }, merge=True)

def get_watched_talks(user_id):
    doc = db.collection("users").document(user_id).get()
    if doc.exists and 'watched_talks' in doc.to_dict():
        return doc.to_dict()['watched_talks']
    return []

# Function to get liked talks
def get_liked_talks(user_id):
    doc = db.collection("users").document(user_id).get()
    if doc.exists and 'liked' in doc.to_dict():
        return doc.to_dict()['liked']
    return []

# Streamlit UI
st.title("TEDFlare - TED Talks Recommendation System")

if "user" not in st.session_state or st.session_state["user"] is None:
    choice = st.sidebar.selectbox("Login / Signup", ["Login", "Signup"])
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button(choice):
        if choice == "Signup":
            signup(email, password)
        else:
            login(email, password)
else:
    user_id = st.session_state["user"]
    st.sidebar.button("Logout", on_click=logout)

    page = st.sidebar.radio("Go to", ["Home", "Saved Talks", "Watched Talks","Liked Talks"])

    if page == "Home":
        selected_talk = st.selectbox("Choose a TED Talk", df['title'])
        talk_id = df[df['title'] == selected_talk].id.values[0]
        st.write("Watch here:", df[df['title'] == selected_talk]['url'].values[0])

        if st.button("Save Talk"):
            save_talk(user_id, talk_id)
            st.success("Talk saved!")

        if st.button("Mark as Watched"):
            watch_talk(user_id, talk_id)
            st.success("Talk marked as watched!")
        
        # Check if talk is already liked
        liked_talks = get_liked_talks(user_id)
        is_liked = str(talk_id) in liked_talks

        if is_liked:
            if st.button("💔 Unlike Talk"):
                db.collection("users").document(user_id).update({
                    "liked": firestore.ArrayRemove([str(talk_id)])
                })
                st.success("Talk unliked!")
                st.rerun()
        else:
            if st.button("❤️ Like Talk"):
                like_talk(user_id, talk_id) 
                st.success("Talk liked!")
                st.rerun()


        if st.button("Get Recommendations"):
            liked = get_liked_talks(user_id)
            watched = get_watched_talks(user_id)

            combined_ids = list(set(liked + watched))  # remove duplicates

            # Convert to DataFrame indices
            talk_indices = []
            for tid in combined_ids:
                if not df[df['id'] == int(tid)].empty:
                    idx = df[df['id'] == int(tid)].index[0]
                    talk_indices.append(idx)

            if not talk_indices:
                st.warning("Watch or like at least one talk to get recommendations!")
            else:
                # Get the saved talks from Firestore
                user_doc = db.collection("users").document(user_id).get()
                if user_doc.exists:
                    saved_talks = user_doc.to_dict().get("saved_talks", [])
                else:
                    saved_talks = []

                # 🔄 Convert string IDs to integers (if needed)
                liked_indices = [int(talk_id) for talk_id in saved_talks if str(talk_id).isdigit()]
                
                if liked_indices:
                    # Average vector of liked + watched
                    user_profile_vector = np.asarray(tfidf_matrix[liked_indices].mean(axis=0)).reshape(1, -1)
                    similarity_scores = cosine_similarity(user_profile_vector, tfidf_matrix).flatten()

                    # Recommend talks not already liked/watched
                    recommended_indices = np.argsort(similarity_scores)[::-1]
                    recommended_indices = [i for i in recommended_indices if i not in talk_indices]
                    top_indices = recommended_indices[:5]

                    st.info("Recommendations based on all your liked and watched talks 💡")
                    st.write("Recommended Talks:")
                    for idx in top_indices:
                        row = df.iloc[idx]
                        st.write(f"[{row['title']}]({row['url']})")
                else:
                    similarity_scores = np.zeros(len(df))  # fallback if no saved talks

        
        # 🔍 Natural Language Search
        st.subheader("🔍 Search Talks by Keyword or Phrase")
        search_query = st.text_input("Type something like 'Inspire me', 'Talks about AI', or 'Technology and future'")

        if search_query:
            query_vec = vectorizer.transform([search_query])
            sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
            top_indices = np.argsort(sim_scores)[::-1][:5]

            st.write("🎯 Top Matching Talks:")
            for idx in top_indices:
                talk = df.iloc[idx]
                talk_id = talk['id']
                st.markdown(f"**{talk['title']}**  \n[{talk['url']}]({talk['url']})")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button(f"💾 Save", key=f"save_{talk_id}"):
                        save_talk(user_id, talk_id)
                        st.success("Talk saved!")

                with col2:
                    if st.button(f"👁️ Mark as Watched", key=f"watch_{talk_id}"):
                        watch_talk(user_id, talk_id)
                        st.success("Marked as watched!")

                with col3:
                    liked_talks = get_liked_talks(user_id)
                    is_liked = str(talk_id) in liked_talks
                    if is_liked:
                        if st.button("💔 Unlike", key=f"unlike_{talk_id}"):
                            unlike_talk(user_id, talk_id)
                            st.success("Talk unliked!")
                            st.rerun()
                    else:
                        if st.button("❤️ Like", key=f"like_{talk_id}"):
                            like_talk(user_id, talk_id)
                            st.success("Talk liked!")
                            st.rerun()
                    
                st.markdown("---")  # separator between each talk


    elif page == "Saved Talks":
        st.header("🎯 Saved Talks")
        saved = get_saved_talks(user_id)
        if saved:
            for talk_id in saved:
                talk = df[df['id'] == int(talk_id)]
                if not talk.empty:
                    st.write(f"📌 [{talk['title'].values[0]}]({talk['url'].values[0]})")
                    if st.button(f"❌ Unsave: {talk['title'].values[0]}", key=f"unsave_{talk_id}"):
                        unsave_talk(user_id, talk_id)
                        st.success("Talk removed from saved list!")
                        st.rerun()
        else:
            st.info("No saved talks yet.")

    elif page == "Watched Talks":
        st.header("🎬 Watched Talks")
        watched = get_watched_talks(user_id)
        if watched:
            for talk_id in watched:
                talk = df[df['id'] == int(talk_id)].iloc[0]
                st.write(f"👀 [{talk['title']}]({talk['url']})")
        else:
            st.info("No watched talks yet.")
    
    elif page == "Liked Talks":
        st.header("❤️ Liked Talks")
        liked = get_liked_talks(user_id)
        if liked:
            for talk_id in liked:
                talk = df[df['id'] == int(talk_id)]
                if not talk.empty:
                    st.write(f"💖 [{talk['title'].values[0]}]({talk['url'].values[0]})")
                    if st.button(f"💔 Unlike: {talk['title'].values[0]}", key=f"unlike_{talk_id}"):
                        unlike_talk(user_id, talk_id)
                        st.success("Talk removed from liked list!")
                        st.rerun()
        else:
            st.info("No liked talks yet.")


        
