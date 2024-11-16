import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List
import json

def fetch_wikipedia_content(url: str) -> str:
    """Fetch content from Wikipedia page."""
    response = requests.get(url)
    return response.text

def extract_latex_equations(html_content: str) -> List[str]:
    """Extract LaTeX equations from Wikipedia HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # First, find the relevant section
    content_div = soup.find('div', {'class': 'mw-parser-output'})
    if not content_div:
        return []
    
    equations = []
    
    # Find all math elements within the content div
    math_elements = content_div.find_all(['span', 'math'], 
        class_=['mwe-math-element'])
    
    for element in math_elements:
        # Try to find LaTeX in annotation
        annotation = element.find('annotation', encoding='application/x-tex')
        if annotation and annotation.string:
            latex = annotation.string.strip()
            # Only include equations that contain our variables of interest
            if any(var in latex for var in ['x', 'y', 'β', 'ε']) and len(latex) > 5:
                equations.append(latex)
    
    return equations

def colorize_variables(equation: str, colors: Dict[str, str]) -> str:
    """Apply colors to variables in LaTeX equation."""
    try:
        # Create a mapping for Greek letters and their variations
        greek_map = {
            'β': r'\\beta',
            'ε': r'\\epsilon'
        }
        
        for var, color in colors.items():
            # Handle Greek letters
            if var in greek_map:
                pattern = fr'{greek_map[var]}'
            else:
                # Handle regular variables (x, y) with their subscripts
                pattern = fr'(?<![\\\w]){var}(?:_[{{\d+}}]|\d+)?(?![\w])'
            
            # Create the color command
            color_cmd = fr'\\color{{{color}}}'
            
            # Replace the pattern with colored version
            equation = re.sub(pattern, 
                            lambda m: f'{color_cmd}{{{m.group(0)}}}', 
                            equation)
        
        return equation
    except Exception as e:
        st.error(f"Error processing equation: {str(e)}")
        return equation

def create_streamlit_app():
    st.title("LaTeX Variable Colorizer")
    
    # Input for Wikipedia URL
    wiki_url = st.text_input(
        "Wikipedia URL",
        value="https://en.wikipedia.org/wiki/Ordinary_least_squares",
        help="Enter the full Wikipedia URL"
    )
    
    # Color pickers for each variable type with colors matching the image
    st.subheader("Choose Colors for Variables")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        x_color = st.color_picker("x variables", "#FF69B4")  # Pink
    with col2:
        y_color = st.color_picker("y variables", "#32CD32")  # Lime green
    with col3:
        beta_color = st.color_picker("β variables", "#4169E1")  # Royal blue
    with col4:
        epsilon_color = st.color_picker("ε variables", "#9370DB")  # Medium purple
    
    # Create color mapping
    colors = {
        'x': x_color,
        'y': y_color,
        'β': beta_color,
        'ε': epsilon_color
    }
    
    if st.button("Process Equations"):
        try:
            with st.spinner("Fetching and processing equations..."):
                # Fetch content
                content = fetch_wikipedia_content(wiki_url)
                equations = extract_latex_equations(content)
                
                if not equations:
                    st.warning("No equations found on this page. Try another Wikipedia article with mathematical equations.")
                    return
                
                # Display equations
                st.subheader(f"Found {len(equations)} equations:")
                for i, eq in enumerate(equations, 1):
                    if any(var in eq for var in colors.keys()):  # Only show equations with our variables
                        st.write(f"Equation {i}:")
                        colorized_eq = colorize_variables(eq, colors)
                        st.latex(colorized_eq)
                        st.markdown("---")
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    create_streamlit_app()