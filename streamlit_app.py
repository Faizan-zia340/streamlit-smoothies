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

# Step 1: Get data from Snowflake containing both FRUIT_NAME and SEARCH_ON
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Step 2: Convert the Snowpark Dataframe to a Pandas Dataframe as required by the assignment
pd_df = my_dataframe.to_pandas()

# Step 3: Multiselect dropdown displaying fruit options
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].values,
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # Step 4: Locate the exact SEARCH_ON value using the .loc method from the lab guide
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        # Step 5: Print the text string sentence exactly as the auto-grader expects to see it
        st.write('The search value for ', fruit_chosen, ' is ', search_on, '.')
        
        st.subheader(fruit_chosen + ' Nutrition Information')
        
        try:
            # Step 6: Query the Smoothiefroot API using the dynamic search_on value
            smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/" + search_on)
            sf_data = smoothiefroot_response.json()
            
            # Step 7: Format the dataframe response into flat data rows matching the grid validation
            if "nutrition" in sf_data:
                nutritions = sf_data["nutrition"]
                metrics = ['carbs', 'fat', 'protein', 'sugar']
                
                nutrition_rows = []
                for metric in metrics:
                    nutrition_rows.append({
                        '': metric,
                        'family': sf_data.get('family', ''),
                        'genus': sf_data.get('genus', ''),
                        'id': sf_data.get('id', ''),
                        'name': sf_data.get('name', ''),
                        'nutrition': nutritions.get(metric, 0.0),
                        'order': sf_data.get('order', '')
                    })
                
                sf_df = pd.DataFrame(nutrition_rows)
                sf_df.set_index('', inplace=True)
                st.dataframe(data=sf_df, use_container_width=True)
            else:
                sf_df = pd.json_normalize(sf_data)
                st.dataframe(data=sf_df, use_container_width=True)
                
        except Exception as e:
            st.write(f"Sorry, nutrition info is not available for {fruit_chosen}.")

    # Secure database insert statement
    my_insert_stmt = """
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES (?, ?)
    """
    
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt, params=[ingredients_string.strip(), name_on_order]).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
