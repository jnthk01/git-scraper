import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
from flask import Flask, render_template, request, session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load your dataset
df = pd.read_csv('gitDataFeed.csv')

# Preprocess and initialize the embedding model
df['main_topic'] = df['main_topic'].str.lower()
df['tags'] = df['tags'].str.lower()

# Load Sentence Transformer
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = embedding_model.encode(df['main_topic'].tolist(), convert_to_numpy=True)
embedding_dimension = embeddings.shape[1]

# Initialize FAISS index
faiss_index = faiss.IndexFlatL2(embedding_dimension)
faiss_index.add(np.array(embeddings).astype('float32'))

def retrieve(query, k=5):
    query_embedding = embedding_model.encode([query], convert_to_numpy=True)
    distances, indices = faiss_index.search(np.array(query_embedding).astype('float32'), k)
    return df.iloc[indices[0]]

def retrieve_top_repositories_by_topic(main_topic, k=10):
    # Retrieve the top `k` repositories based on the `main_topic`
    top_repositories = df[df['main_topic'] == main_topic].head(k)
    return top_repositories

def format_response(retrieved_data):
    response = []
    for _, row in retrieved_data.iterrows():
        response.append({
            'author_name': row['author_name'],
            'repository_name': row['repository_name'],
            'repository_url': row['repository_url'],
            'tags': row['tags'],
            'stars': row['stars']
        })
    return response

# New function to provide query instructions
def get_instructions():
    instructions = [
        {"command": "List of all main topics", "description": "Displays all the main topics from the dataset."},
        # {"command": "Most starred in [topic]", "description": "Displays the repository with the most stars in a particular topic."},
        {"command": "Give me stars for [repository name]", "description": "Displays the number of stars for a specific repository."},
        {"command": "Give me tags for [repository name]", "description": "Displays the tags associated with a specific repository."},
        {"command": "Tell me about [main_topic]", "description": "Displays the top 10 repositories for a specific main topic."},
        {"command": "[query]", "description": "Searches the repositories based on the given query and returns relevant results."}
    ]
    return instructions

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'response_data' not in session:
        session['response_data'] = []

    if request.method == 'POST':
        query = request.form['query'].lower()
        print(query)

        # Command: List all main topics
        if "list of all main topics" in query:
            main_topics = df['main_topic'].unique()
            session['response_data'] = [{"main_topic": topic} for topic in main_topics]

        # Command: Most starred in a specific topic
        elif "most starred in" in query:
            topic = query.replace("most starred in ", "").strip()
            most_starred = df[df['main_topic'].str.contains(topic)].sort_values(by='stars', ascending=False).head(1)
            if not most_starred.empty:
                row = most_starred.iloc[0]
                session['response_data'] = [{
                    'author_name': row['author_name'],
                    'repository_name': row['repository_name'],
                    'repository_url': row['repository_url'],
                    'tags': row['tags'],
                    'stars': row['stars']
                }]
            else:
                session['response_data'] = [{"error": f"No repositories found for the topic '{topic}'."}]

        # Command: Give me stars for a specific repository
        elif "give me stars for" in query:
            repo_name = query.replace("give me stars for ", "").strip()
            repo_data = df[df['repository_name'].str.lower() == repo_name]
            if not repo_data.empty:
                stars = repo_data['stars'].values[0]
                session['response_data'] = [{"stars": stars}]
            else:
                session['response_data'] = [{"error": f"No repository found for '{repo_name}'."}]

        # Command: Give me tags for a specific repository
        elif "give me tags for" in query:
            repo_name = query.replace("give me tags for ", "").strip()
            repo_data = df[df['repository_name'].str.lower() == repo_name]
            if not repo_data.empty:
                tags = repo_data['tags'].values[0]
                session['response_data'] = [{"tags": tags}]
            else:
                session['response_data'] = [{"error": f"No repository found for '{repo_name}'."}]

        # Command: Tell me about {main_topic}
        elif "tell me about" in query:
            main_topic = query.replace("tell me about", "").strip()
            top_repositories = retrieve_top_repositories_by_topic(main_topic)
            if not top_repositories.empty:
                session['response_data'] = format_response(top_repositories)
            else:
                session['response_data'] = [{"error": f"No repositories found for the main topic '{main_topic}'."}]

        # Default search
        else:
            retrieved_data = retrieve(query)
            session['response_data'] = format_response(retrieved_data)

    response_data = session['response_data']
    print(response_data)
    return render_template('index.html', response_data=response_data)

@app.route('/instructions', methods=['GET'])
def instructions():
    instructions = get_instructions()
    return render_template('instructions.html', instructions=instructions)

@app.route('/clear', methods=['GET'])
def clear_session():
    session.clear()
    return index()

if __name__ == '__main__':
    app.run(debug=True)
