# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connection to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch table data matching your dataset schema
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME')).to_pandas()

# Multiselect input matching Image 2
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe['FRUIT_NAME'].values,
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        st.subheader(fruit_chosen + ' Nutrition Information')
        
        # Smoothiefroot API URL call as shown in Image 4 code line 35
        try:
            smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/" + fruit_chosen)
            sf_data = smoothiefroot_response.json()
            
            # Check if API returned an array or direct object, then flatten appropriately
            if isinstance(sf_data, list):
                sf_df = pd.json_normalize(sf_data)
            else:
                sf_df = pd.json_normalize([sf_data])
                
            # If the database returns nested nutritions properties, match the layout in Image 3
            st.dataframe(data=sf_df, use_container_width=True)
            
        except Exception as e:
            st.write(f"Sorry, {fruit_chosen} nutrition info is not available right now.")

    # Insert Statement with bind parameters to avoid parsing errors
    my_insert_stmt = """
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES (?, ?)
    """
    
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt, params=[ingredients_string.strip(), name_on_order]).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
