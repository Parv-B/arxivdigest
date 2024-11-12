import streamlit as st
import requests
import xml.etree.ElementTree as ET

# Base URL for arXiv API
BASE_URL = 'http://export.arxiv.org/api/query?'

def fetch_papers(search_query="all", start=0, max_results=5):
    """
    Fetches papers from arXiv API based on the search query.

    Args:
        search_query (str): The search query string.
        start (int): The starting index for results.
        max_results (int): The maximum number of results to fetch.

    Returns:
        list: A list of dictionaries containing paper information.
    """
    query = f'search_query={search_query}&start={start}&max_results={max_results}'
    url = BASE_URL + query
    response = requests.get(url)
    root = ET.fromstring(response.content)
    
    papers = []
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = entry.find("{http://www.w3.org/2005/Atom}title").text
        authors = [author.find("{http://www.w3.org/2005/Atom}name").text for author in entry.findall("{http://www.w3.org/2005/Atom}author")]
        summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
        categories = [category.attrib['term'] for category in entry.findall("{http://www.w3.org/2005/Atom}category")]
        link = entry.find("{http://www.w3.org/2005/Atom}id").text
        papers.append({
            "title": title,
            "authors": authors,
            "summary": summary,
            "categories": categories,
            "link": link
        })
    return papers

# Initialize session state
if 'papers' not in st.session_state:
    st.session_state.papers = []
if 'liked_papers' not in st.session_state:
    st.session_state.liked_papers = []
if 'liked_categories' not in st.session_state:
    st.session_state.liked_categories = {}
if 'disliked_categories' not in st.session_state:
    st.session_state.disliked_categories = {}
if 'viewed_categories' not in st.session_state:
    st.session_state.viewed_categories = {}
if 'start_index' not in st.session_state:
    st.session_state.start_index = 0

# Sidebar for navigation
page = st.sidebar.selectbox("Navigation", ["Fetch Papers", "View Preferences", "View Liked Papers", "Generate Recommendations"])

st.title("arXiv Paper Recommender")

if page == "Fetch Papers":
    # User interests input
    user_interest = st.text_input("Enter your interests (e.g., machine learning, quantum computing):")

    # Fetch new papers
    if st.button("Fetch Papers"):
        search_query = user_interest if user_interest else "all"
        new_papers = fetch_papers(search_query=search_query, start=st.session_state.start_index, max_results=5)
        if new_papers:
            st.session_state.papers.extend(new_papers)
            st.session_state.start_index += 5  # Increment start index for next fetch

    # Display fetched papers with radio buttons for liking and disliking
    if st.session_state.papers:
        st.write("Select whether you like or dislike each paper:")
        for idx, paper in enumerate(st.session_state.papers):
            title = paper['title']
            authors = ', '.join(paper['authors'])
            abstract_snippet = ' '.join(paper['summary'].split()[:50]) + '...'
            categories = paper['categories']
            arxiv_url = paper['link']

            # Display paper information
            st.subheader(title)
            st.write(f"**Authors:** {authors}")
            st.write(f"**Abstract:** {abstract_snippet}")
            st.write(f"**Categories:** {', '.join(categories)}")
            st.write(f"[Read more on arXiv]({arxiv_url})")

            # Radio button for like, dislike, or neutral
            preference = st.radio(
                f"Your preference for '{title}'",
                options=["Neutral", "Like", "Dislike"],
                key=f"preference_{idx}"
            )

            # Update state based on user selection
            if preference == "Like":
                if paper not in st.session_state.liked_papers:
                    st.session_state.liked_papers.append(paper)
                for category in categories:
                    st.session_state.liked_categories[category] = st.session_state.liked_categories.get(category, 0) + 1
            elif preference == "Dislike":
                for category in categories:
                    st.session_state.disliked_categories[category] = st.session_state.disliked_categories.get(category, 0) + 1

            for category in categories:
                st.session_state.viewed_categories[category] = st.session_state.viewed_categories.get(category, 0) + 1

elif page == "View Preferences":
    st.header("View Preferences")
    if not st.session_state.viewed_categories:
        st.write("You have not viewed any papers yet.")
    else:
        preference_scores = {
            category: (st.session_state.liked_categories.get(category, 0) - st.session_state.disliked_categories.get(category, 0)) / st.session_state.viewed_categories[category]
            for category in st.session_state.viewed_categories
        }
        sorted_preferences = sorted(preference_scores.items(), key=lambda x: x[1], reverse=True)
        st.write("Your Learned Preferences:")
        for category, score in sorted_preferences:
            st.write(f"Category: {category}, Preference Score: {score:.2f}")

elif page == "View Liked Papers":
    st.header("View Liked Papers")
    if not st.session_state.liked_papers:
        st.write("You have not liked any papers yet.")
    else:
        for paper in st.session_state.liked_papers:
            st.subheader(paper['title'])
            st.write(f"Authors: {', '.join(paper['authors'])}")
            st.write(f"[Read more on arXiv]({paper['link']})")

elif page == "Generate Recommendations":
    st.header("Generate Recommendations")
    preference_scores = {
        category: (st.session_state.liked_categories.get(category, 0) - st.session_state.disliked_categories.get(category, 0)) / st.session_state.viewed_categories[category]
        for category in st.session_state.viewed_categories
    }
    sorted_categories = sorted(preference_scores.items(), key=lambda x: x[1], reverse=True)
    preferred_categories = [cat for cat, score in sorted_categories if score > 0]

    if not preferred_categories:
        st.write("No preferred categories found. Cannot generate recommendations.")
    else:
        st.write("Generating recommendations based on your preferences...")
        for category in preferred_categories:
            st.write(f"\nTop papers in category: {category}")
            recommended_papers = fetch_papers(search_query=f"cat:{category}", max_results=3)
            for paper in recommended_papers:
                st.subheader(paper['title'])
                st.write(f"Authors: {', '.join(paper['authors'])}")
                st.write(f"Abstract: {' '.join(paper['summary'].split()[:50])}...")
                st.write(f"[Read more on arXiv]({paper['link']})")
