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

# UPDATED: Select both FRUIT_NAME and SEARCH_ON columns from Snowflake
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON')).to_pandas()

# Dropdown options display only the clean FRUIT_NAME values
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe['FRUIT_NAME'].values,
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # UPDATED: Get the matching SEARCH_ON value for the selected fruit
        search_on = my_dataframe.loc[my_dataframe['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        st.subheader(fruit_chosen + ' Nutrition Information')
        
        try:
            # UPDATED: Hit the correct smoothiefroot API using the search_on variable
            smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/" + search_on)
            sf_data = smoothiefroot_response.json()
            
            # Convert JSON data into a clean structured table matching Image 3 layout
            if isinstance(sf_data, list):
                sf_df = pd.json_normalize(sf_data)
            else:
                sf_df = pd.json_normalize([sf_data])
                
            st.dataframe(data=sf_df, use_container_width=True)
            
        except Exception as e:
            st.write(f"Sorry, nutrition info is not available for {fruit_chosen}.")

    # Secure database insert using Snowflake parameters (?)
    my_insert_stmt = """
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES (?, ?)
    """
    
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt, params=[ingredients_string.strip(), name_on_order]).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
