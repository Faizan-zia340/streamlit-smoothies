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

# CRITICAL FIX: Pull both FRUIT_NAME and SEARCH_ON columns from Snowflake
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON')).to_pandas()

# The multiselect should only display clean text strings
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe['FRUIT_NAME'].values, # Clean list of names for the dropdown
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # Look up the correct search term from the dataframe for the API call
        search_on = my_dataframe.loc[my_dataframe['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        st.subheader(fruit_chosen + ' Nutrition Information')
        try:
            # Call the Fruityvice API using the clean search_on value
            fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)
            fv_data = fruityvice_response.json()
            
            # Displaying as text/json directly or a clean table
            st.dataframe(data=fv_data, use_container_width=True)
        except Exception as e:
            st.write(f"Could not get nutrition info for {fruit_chosen}")

    # Build the insert statement securely
    my_insert_stmt = """
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES (?, ?)
    """

    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        # Using parameters prevents SQL injection and syntax errors with quotes
        session.sql(my_insert_stmt, params=[ingredients_string.strip(), name_on_order]).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
