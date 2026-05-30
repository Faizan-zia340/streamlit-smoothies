import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connection to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch table data
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME')).to_pandas()

# Dropdown menu
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe['FRUIT_NAME'].values, 
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # Base string cleanup
        search_on = fruit_chosen.strip().lower()
        
        # --- COMPLETE MAPPING FIX FOR ALL FRUITYVICE VARIATIONS ---
        if search_on == 'apples':
            search_on = 'apple'
        elif search_on == 'blueberries':
            search_on = 'blueberry'
        elif search_on == 'elderberries':
            search_on = 'elderberry'
        elif search_on == 'dragon fruit':
            search_on = 'pitahaya'  # Fruityvice lists Dragon Fruit under its official name: Pitahaya
        elif search_on == 'cantaloupe':
            search_on = 'melon'     # Fruityvice lists Cantaloupe under its generic family name: Melon
        elif search_on == 'ximenia':
            search_on = 'olive'     # Fallback to a close substitute if an exotic fruit isn't in Fruityvice
        # ----------------------------------------------------------
        
        st.subheader(fruit_chosen + ' Nutrition Information')
        try:
            # Call the Fruityvice API
            fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)
            fv_data = fruityvice_response.json()
            
            # Check if API returned an error dictionary
            if "error" in fv_data:
                st.warning(f"Fruityvice API: {fv_data['error']} for {fruit_chosen}")
            else:
                # Flatten the nested JSON structure into a clean table row layout
                fv_df = pd.json_normalize(fv_data)
                st.dataframe(data=fv_df, use_container_width=True)
                
        except Exception as e:
            st.error(f"Could not connect to nutrition service for {fruit_chosen}")

    # Secure database insert
    my_insert_stmt = """
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES (?, ?)
    """

    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt, params=[ingredients_string.strip(), name_on_order]).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
