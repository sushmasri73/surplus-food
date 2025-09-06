CREATE TABLE IF NOT EXISTS food_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_email TEXT,
    food_name TEXT,
    quantity TEXT,
    expiry_date DATE,
    pickup_location TEXT,
    photo_url TEXT,
    is_claimed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);