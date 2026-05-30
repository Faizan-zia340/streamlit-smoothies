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
    
    # 1. Ek khali list banayein saare dataframes ko jama karne ke liye
    all_fruits_data = []

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # Base string cleanup
        search_on = fruit_chosen.strip().lower()
        
        # Mapping Fixes
        if search_on == 'apples':
            search_on = 'apple'
        elif search_on == 'blueberries':
            search_on = 'blueberry'
        elif search_on == 'elderberries':
            search_on = 'elderberry'
        elif search_on == 'dragon fruit':
            search_on = 'pitahaya'
        elif search_on == 'cantaloupe':
            search_on = 'melon'
        
        try:
            # Call the Fruityvice API
            fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)
            fv_data = fruityvice_response.json()
            
            if "error" not in fv_data:
                # Data ko flatten karein
                fv_df = pd.json_normalize(fv_data)
                # 2. Is fruit ka data list mein append kar dein
                all_fruits_data.append(fv_df)
                
        except Exception as e:
            pass # Background mein skip karein taake app crash na ho

    # 3. LOOP KE BAHAR: Agar data collect hua hai, to sabko aik sath jor (combine) dein
    if all_fruits_data:
        st.subheader('Selected Fruits Nutrition Information')
        # pd.concat se saare fruits ek hi table mein upar-neeche combine ho jayenge
        combined_df = pd.concat(all_fruits_data, ignore_index=True)
        st.dataframe(data=combined_df, use_container_width=True)

    # Secure database insert
    my_insert_stmt = """
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES (?, ?)
    """

    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt, params=[ingredients_string.strip(), name_on_order]).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
