-- Create the history table to store all decodings
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_message TEXT NOT NULL,
    decoded_message TEXT NOT NULL,
    shift_value INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);