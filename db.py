import sqlite3
import datetime

DATABASE_NAME = "app.db"

def init_db():
    """
    Initializes the SQLite database and creates the necessary tables.
    This function should be called once when the application starts.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Create the 'users' table to store user roles
    cursor.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, role TEXT)")
    
    # Create the 'food_listings' table to store food donation details
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_email TEXT,
            food_name TEXT,
            quantity TEXT,
            expiry_date DATE,
            pickup_location TEXT,
            photo_url TEXT,
            is_claimed BOOLEAN DEFAULT 0,
            receiver_email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # New: Create the 'ratings' table for user trust
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rater_email TEXT,
            rated_email TEXT,
            rating INTEGER, -- e.g., 1 to 5 stars
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # New: Create the 'reviews' table for user feedback
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reviewer_email TEXT,
            reviewed_email TEXT,
            review_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def add_user(email, role=None):
    """Adds a new user to the database with a default role."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, role) VALUES (?, ?)", (email, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # User with this email already exists
        return False
    finally:
        conn.close()

def get_user_role(email):
    """Retrieves the role of a user based on their email."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def update_user_role(email, role):
    """Updates the role of an existing user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE email = ?", (role, email))
    conn.commit()
    conn.close()

def add_food_listing(donor_email, food_name, quantity, expiry_date, pickup_location, photo_url=None):
    """Inserts a new food listing into the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO food_listings (donor_email, food_name, quantity, expiry_date, pickup_location, photo_url)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (donor_email, food_name, quantity, expiry_date, pickup_location, photo_url)
    )
    conn.commit()
    conn.close()

def get_food_listings():
    """Fetches all unclaimed food listings from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM food_listings WHERE is_claimed = 0 ORDER BY created_at DESC")
    listings = cursor.fetchall()
    conn.close()
    return listings

def claim_food_listing(listing_id, receiver_email):
    """Marks a food listing as claimed and assigns it to a receiver."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE food_listings SET is_claimed = 1, receiver_email = ? WHERE id = ?",
        (receiver_email, listing_id)
    )
    conn.commit()
    conn.close()

def count_claimed_listings():
    """Counts the total number of claimed food listings."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM food_listings WHERE is_claimed = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count