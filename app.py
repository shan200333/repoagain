from flask import Flask, render_template, request, redirect, url_for, session
import os
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from dotenv import load_dotenv
import hashlib
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Load sensitive information from environment variables
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_default_secret_key")
app.config['MONGO_URI'] = os.getenv("MONGO_URI")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialize PyMongo
mongo = PyMongo(app)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()

        users = mongo.db.users
        if users.find_one({'username': username}):
            return "Username already registered. Please choose a different username."

        users.insert_one({'username': username, 'password': password})
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()

        users = mongo.db.users
        user = users.find_one({'username': username, 'password': password})

        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Incorrect username or password. Please try again."

    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' in session:
        users = mongo.db.users
        songs = mongo.db.songs

        if request.method == 'POST':
            song_name = request.form['song_name']
            user = users.find_one({'username': session['username']})
            songs.insert_one({'user_id': user['_id'], 'song_name': song_name})

        user = users.find_one({'username': session['username']})
        playlist = list(songs.find({'user_id': user['_id']}))

        return render_template('dashboard.html', user=user, playlist=playlist)
    else:
        return redirect(url_for('login'))


@app.route('/remove_song', methods=['POST'])
def remove_song():
    if 'username' in session:
        song_id = request.form.get('song_id')
        mongo.db.songs.delete_one({'_id': ObjectId(song_id)})
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


@app.route('/top_picks')
def top_picks():
    return render_template('top_picks.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route('/search_songs')
def search_songs():
    search_query = request.args.get('search_query')
    if search_query:
        # YouTube Data API for search results
        params = {
            'part': 'snippet',
            'q': search_query,
            'key': YOUTUBE_API_KEY,
            'type': 'video',
            'maxResults': 10
        }
        response = requests.get('https://www.googleapis.com/youtube/v3/search', params=params)
        data = response.json()

        search_results = []
        if 'items' in data:
            for item in data['items']:
                search_results.append({
                    'title': item['snippet']['title'],
                    'video_id': item['id']['videoId'],
                    'description': item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails']['default']['url']
                })

        return render_template('search_results.html', search_query=search_query, search_results=search_results)
    else:
        return "Please provide a search query."


if __name__ == '__main__':
    app.run(debug=True)
