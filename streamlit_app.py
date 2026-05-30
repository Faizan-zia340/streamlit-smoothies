import streamlit as st
from snowflake.snowpark.functions import col
import requests

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connection to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# FIX: Only select FRUIT_NAME since SEARCH_ON column does not exist yet
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME')).to_pandas()

# Dropdown displays clean text strings
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe['FRUIT_NAME'].values, 
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # Format the fruit name safely for the API URL (e.g., "Dragon Fruit" -> "Dragon%20Fruit")
        search_on = fruit_chosen.replace(' ', '%20')
        
        st.subheader(fruit_chosen + ' Nutrition Information')
        try:
            # Call the Fruityvice API using the formatted name string
            fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)
            fv_data = fruityvice_response.json()
            
            # Display the API data on screen
            st.dataframe(data=fv_data, use_container_width=True)
        except Exception as e:
            st.write(f"Could not get nutrition info for {fruit_chosen}")

    # Build the insert statement securely using bind parameters (?)
    my_insert_stmt = """
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES (?, ?)
    """

    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        # Execute statement safely using native parameters to avoid breaking on names like "faizan"
        session.sql(my_insert_stmt, params=[ingredients_string.strip(), name_on_order]).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
