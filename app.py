import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import datetime
import folium
from streamlit_folium import st_folium
import os
from geopy.geocoders import Nominatim
# Import all database functions from db.py
from db import init_db, add_user, get_user_role, update_user_role, add_food_listing, get_food_listings, claim_food_listing, count_claimed_listings

# --- 1. Firebase Initialization ---
# To avoid re-initializing on every run, we use a check
if not firebase_admin._apps:
    try:
        # A service account key is needed for server-side auth
        # You would download this JSON file from your Firebase console
        cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Failed to initialize Firebase: {e}")

# --- 2. App Functions (UI and Logic) ---
def donor_dashboard():
    st.title("Welcome, Donor!")
    
    # Add food safety disclaimer
    st.warning("⚠️ Food Safety Disclaimer: By posting a food item, you certify it is safe for consumption and was handled properly. The app and its developers are not responsible for any food-related issues.", icon="⚠️")
    
    st.header("Post Surplus Food")

    with st.form("food_listing_form"):
        food_name = st.text_input("Food Item Name")
        quantity = st.text_input("Quantity (e.g., 5 servings, 2 kg)")
        expiry_date = st.date_input("Best Before Date", min_value=datetime.date.today())
        
        uploaded_file = st.file_uploader("Upload a photo of the food", type=['png', 'jpg', 'jpeg'])
        
        pickup_location = st.text_input("Pickup Location (e.g., street address)")
        
        submit_button = st.form_submit_button(label="Post Food Item")

        if submit_button:
            if food_name and quantity and pickup_location:
                photo_url = None
                if uploaded_file is not None:
                    # Create the 'uploads' directory if it doesn't exist
                    if not os.path.exists("uploads"):
                        os.makedirs("uploads")
                    
                    # Save the file to the uploads directory
                    file_path = os.path.join("uploads", uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    photo_url = file_path # Store the file path in the DB
                
                add_food_listing(
                    st.session_state.user_email,
                    food_name,
                    quantity,
                    expiry_date,
                    pickup_location,
                    photo_url
                )
                
                st.success(f"Successfully posted: {food_name} ({quantity})")
            else:
                st.error("Please fill in all the required fields.")

    st.button("Logout", on_click=logout)

def receiver_dashboard():
    st.title("Welcome, Receiver!")
    
    # Add food safety disclaimer
    st.warning("⚠️ Food Safety Disclaimer: Food items are donated by community members and are not inspected. Please exercise caution and common sense before consuming any food received.", icon="⚠️")
    
    st.header("Available Food Items Near You")
    
    # Get the Google Maps API key from secrets
    google_api_key = st.secrets.get("google", {}).get("api_key")
    
    # Initialize geocoder with a user agent
    geolocator = Nominatim(user_agent="surplus_food_app")
    
    # Fetch all unclaimed food listings from the database
    listings = get_food_listings()
    
    if not listings:
        st.info("There are no food items available at the moment. Please check back later!")
    else:
        # Create a Folium map centered on a default location
        m = folium.Map(location=[40.7128, -74.0060], zoom_start=12)

        for listing in listings:
            listing_id, donor_email, food_name, quantity, expiry_date, pickup_location, photo_url, is_claimed, receiver_email, created_at = listing
            
            # Use geocoding to get coordinates from the pickup location
            location = geolocator.geocode(pickup_location)
            
            if location:
                lat = location.latitude
                lon = location.longitude

                # Add a marker to the map for each food listing
                folium.Marker(
                    location=[lat, lon],
                    tooltip=food_name,
                    popup=f"**{food_name}** - {quantity}<br>Click to claim!"
                ).add_to(m)

            with st.container(border=True):
                st.subheader(food_name)
                st.write(f"**Quantity:** {quantity}")
                st.write(f"**Best Before:** {expiry_date}")
                st.write(f"**Pickup Location:** {pickup_location}")
                st.write(f"**Posted by:** {donor_email}")

                if st.button(f"Claim this item", key=f"claim_{listing_id}"):
                    claim_food_listing(listing_id, st.session_state.user_email)
                    st.success("You have claimed this item! The donor has been notified.")
                    st.experimental_rerun()
    
    # Display the map in Streamlit
    st_folium(m, width=700, height=500)
    
    st.button("Logout", on_click=logout)

def analytics_dashboard():
    st.title("Analytics Dashboard")
    st.write("A summary of the community's impact.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_donations = count_claimed_listings()
        st.metric(label="Meals Saved", value=total_donations)
        
    with col2:
        st.metric(label="CO₂ Saved", value="~0 kg")
    
    with col3:
        st.metric(label="People Helped", value="~0")

    st.button("Logout", on_click=logout)

def logout():
    st.session_state.clear()
    st.experimental_rerun()

def authentication_page():
    st.title("Login / Register")
    choice = st.radio("Choose an option:", ["Login", "Register"])
    
    email = st.text_input("Email Address")
    password = st.text_input("Password", type="password")

    if choice == "Register":
        if st.button("Create Account"):
            try:
                user = auth.create_user(email=email, password=password)
                add_user(email)
                st.success("Account created successfully!")
                st.info("Please login with your new credentials.")
            except Exception as e:
                st.error(f"Error creating user: {e}")
    
    elif choice == "Login":
        if st.button("Login"):
            try:
                user_role = get_user_role(email)
                if user_role is not None:
                    st.session_state['user_email'] = email
                    st.session_state['logged_in'] = True
                    st.session_state['user_role'] = user_role
                    st.success(f"Welcome back!")
                    st.experimental_rerun()
                else:
                    st.error("User not found in local database. Please register.")
            except Exception as e:
                st.error("Login failed. Please check your credentials.")

# --- 3. Main App Flow ---
def main():
    # Call init_db() to create the database and tables on startup
    init_db()

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if st.session_state['logged_in']:
        # Navigation with a sidebar radio button
        page = st.sidebar.radio("Navigation", ["Donor", "Receiver", "Analytics"])
        
        if page == "Donor":
            donor_dashboard()
        elif page == "Receiver":
            receiver_dashboard()
        elif page == "Analytics":
            analytics_dashboard()
    else:
        authentication_page()

if __name__ == "__main__":
    main()