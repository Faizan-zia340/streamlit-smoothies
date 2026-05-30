# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col

# Write directly to the app
st.title(":cup_with_straw: My Healthy Smoothie Diner :cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom Smoothie!
    """
)

st.header("🍳 Breakfast Menu")
st.write("""
**Omega 3 & Blueberry Oatmeal**

**Kale, Spinach & Rocket Smoothie**

**Hard-Boiled Free-Range Egg**
""")

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# New SniS Connection
cnx = st.connection("snowflake")
session = cnx.session()

# Pull the table data
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME')).to_pandas()

# --- FIX FOR THE JSON ISSUE ---
# If your database column has stringified JSON, we must extract just the name.
# We look for the 'name' key; if it's already a clean string, it falls back safely.
def extract_fruit_name(val):
    if isinstance(val, str) and val.startswith('{'):
        import json
        try:
            return json.loads(val).get('name', val)
        except:
            return val
    return val

# Clean the dataframe column before sending it to the multiselect
clean_fruit_list = my_dataframe['FRUIT_NAME'].apply(extract_fruit_name)
# ------------------------------

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    clean_fruit_list, # Passed the cleaned list here
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

    # Using bind variables inside session.sql() protects against SQL syntax errors
    # if a user types weird characters or quotes in their name.
    my_insert_stmt = """
        INSERT INTO smoothies.public.orders (ingredients, name_on_order)
        VALUES (?, ?)
    """
    
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        # Pass the values securely into the query execution
        session.sql(my_insert_stmt, params=[ingredients_string.strip(), name_on_order]).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
