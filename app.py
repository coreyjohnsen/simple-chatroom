# app.py
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app)

# Load user data from file
def load_users():
    try:
        with open('users.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save user data to file
def save_users(users):
    with open('users.json', 'w') as file:
        json.dump(users, file)

# Dictionary to store user information
users = load_users()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    if username in users:
        return 'Username already exists'
    users[username] = generate_password_hash(password)
    save_users(users)
    session['username'] = username
    return redirect(url_for('chat'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username not in users or not check_password_hash(users[username], password):
        return 'Invalid username or password'
    session['username'] = username
    return redirect(url_for('chat'))

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('chat.html', username=session['username'])

@socketio.on('join')
def on_join(data):
    username = session['username']
    room = data['room']
    join_room(room)
    emit('join_announcement', {'username': username, 'room': room}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    username = session['username']
    emit('broadcast', {'username': username, 'message': message}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = session['username']
    room = data['room']
    leave_room(room)
    emit('leave_announcement', {'username': username, 'room': room}, room=room)

@socketio.on('disconnect')
def on_disconnect():
    username = session['username']
    room = session.get('room')
    leave_room(room)
    emit('leave_announcement', {'username': username, 'room': room}, room=room)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5002)