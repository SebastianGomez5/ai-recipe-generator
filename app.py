import streamlit as st
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from fpdf import FPDF
from PIL import Image
import requests
from io import BytesIO

load_dotenv(find_dotenv())
client = OpenAI()
def generate_recipe(ingredients):
    system_prompt = "You are an excellent first-class chef."
    user_prompt = f'''
    Generate a detailed recipe using the following ingredients: {', '.join(ingredients)}.  
    Include step-by-step instructions and a brief description. Also submit it in the following format:
    Recipe title:
    Recipe ingredients with size and serving size:
    List of ingredients for the recipe:
    '''
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1020,
        temperature=0.9
    )
    return response.choices[0].message.content

def get_recipe_name(text):
    for line in text.splitlines():
        if "title" in line.lower():
            return line.replace("Recipe title:", "").strip()
    return "Generated Recipe"

def get_image(recipe_name):
    response = client.images.generate(
        model="dall-e-3",
        prompt=f'''Create a realistic photo of the actual dish titled {recipe_name}, The dish should be beautifully presented on a ceramic plate with a close-up focus on the textures and colors of the ingredients.
        The setting should be on a wooden table with natural lighting to highlight the appetizing characteristics of the food. Ensure that the image captures the rich, vibrant colors and intricate details of the food, making it look freshly prepared and ready to eat.
        ''',
        n=1,
        style='vivid',
        quality='standard',
        size="1024x1024"
    )
    image_url = response.data[0].url
    image_response = requests.get(image_url)
    return Image.open(BytesIO(image_response.content))

def save_recipe_as_pdf(recipe_text, recipe_image, filename="recipe.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add title
    pdf.set_font("Arial", 'B', 16)
    title = get_recipe_name(recipe_text)
    pdf.multi_cell(0, 10, title, align='C')

    # Save and add image (proportional scaling)
    image_path = "temp_image.png"
    recipe_image.save(image_path)
    img_width, img_height = recipe_image.size
    
    max_width = pdf.w - 20
    ratio = max_width / img_width
    new_height = img_height * ratio
    
    y_after_image = pdf.get_y() + new_height + 10
    pdf.image(image_path, x=10, y=pdf.get_y()+5, w=max_width)
    pdf.set_y(y_after_image)

    # Add recipe text
    pdf.set_font("Arial", size=12)
    for line in recipe_text.splitlines():
        pdf.multi_cell(0, 10, line)

    pdf.output(filename)

st.title("AI-Powered Recipe Generator")
st.write("Enter ingredients you have, and get a delicious recipe!")

ingredients = st.text_input("Ingredients (comma-separated):")
if st.button("Generate Recipe"):
    if ingredients:
        ingredient_list = [ingredient.strip() for ingredient in ingredients.split(",")]
        recipe = generate_recipe(ingredient_list)
        st.write(recipe)

        # Generate and display image
        recipe_name = get_recipe_name(recipe)
        recipe_image = get_image(recipe_name)
        st.image(recipe_image, caption=recipe_name)

        # Save recipe as PDF
        if st.button("Download Recipe as PDF"):
            save_recipe_as_pdf(recipe, recipe_image)
            st.success("Recipe saved as PDF!")
    else:
        st.warning("Please enter at least one ingredient.")
        
try:
    recipe = generate_recipe(ingredient_list)
    st.write(recipe)
except Exception as e:
    st.error(f"Error al generar receta: {str(e)}. Revisa tu plan/billing en OpenAI.")