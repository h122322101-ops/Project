import os
import sqlite3
from flask import Flask, request, jsonify, render_template, g

app = Flask(__name__)
DATABASE = 'database.db'

# --- DATABASE CONNECTION & INITIALIZATION ---

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Returns dict-like rows
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database using schema.sql if it doesn't exist."""
    if not os.path.exists(DATABASE):
        with app.app_context():
            db = get_db()
            try:
                with open('schema.sql', mode='r') as f:
                    db.cursor().executescript(f.read())
                db.commit()
                print("Database initialized automatically.")
            except Exception as e:
                print(f"Failed to initialize database: {e}")

# --- HELPER FUNCTIONS ---

def decode_message(message):
    """
    Finds the number of letters in the first word (n).
    Shifts every letter in the entire message backward by n places.
    Spaces and punctuation are preserved.
    """
    words = message.split()
    if not words:
        return message, 0
    
    # Calculate n: number of alphabetic characters in the first word
    first_word = words[0]
    n = sum(1 for char in first_word if char.isalpha())
    
    decoded_chars = []
    for char in message:
        if char.isalpha():
            # Determine base (uppercase or lowercase)
            base = ord('A') if char.isupper() else ord('a')
            # Perform the backward shift with wrap-around
            shifted = chr((ord(char) - base - n) % 26 + base)
            decoded_chars.append(shifted)
        else:
            # Preserve spaces, numbers, and punctuation
            decoded_chars.append(char)
            
    return "".join(decoded_chars), n

# --- ROUTES ---

@app.route('/')
def index():
    """Serves the main single-page application."""
    return render_template('index.html')

@app.route('/api/decode', methods=['POST'])
def api_decode():
    """Processes the encoded message, calculates shift, decodes, and saves to DB."""
    try:
        data = request.get_json()
        
        # Strict Input Validation
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing "message" in JSON payload.'}), 400
        
        original_message = data['message'].strip()
        if not original_message:
            return jsonify({'error': 'Message cannot be empty.'}), 400
            
        # Execute Cryptographic Logic
        decoded_text, shift_value = decode_message(original_message)
        
        # Save to Database
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO history (original_message, decoded_message, shift_value) VALUES (?, ?, ?)",
            (original_message, decoded_text, shift_value)
        )
        db.commit()
        
        return jsonify({
            'decoded_message': decoded_text,
            'n_value': shift_value,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/history', methods=['GET'])
def api_get_history():
    """Retrieves all past decoding sessions."""
    try:
        db = get_db()
        cursor = db.cursor()
        # Fetch descending so the newest are at the top
        cursor.execute("SELECT * FROM history ORDER BY id DESC")
        rows = cursor.fetchall()
        
        history_list = []
        for row in rows:
            history_list.append({
                'id': row['id'],
                'original': row['original_message'],
                'decoded': row['decoded_message'],
                'shift_value': row['shift_value'],
                'timestamp': row['created_at']
            })
            
        return jsonify({'history': history_list, 'status': 'success'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/history', methods=['DELETE'])
def api_clear_history():
    """Wipes the history database."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM history")
        db.commit()
        
        return jsonify({'message': 'History successfully cleared.', 'status': 'success'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    # Initialize DB before running
    init_db()
    # Run the server
    app.run(debug=True, port=5000)