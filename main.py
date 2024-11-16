import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List

def fetch_wikipedia_content(url: str) -> str:
    """Fetch content from Wikipedia page."""
    response = requests.get(url)
    return response.text

def extract_latex_equations(html_content: str) -> List[str]:
    """
    Extract LaTeX equations from Wikipedia HTML content.
    Only extracts equations containing our variables of interest (x, y, β, ε).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    equations = set()  # Using a set to remove duplicates
    
    # Find all math elements
    math_elements = soup.find_all('math')
    
    for math_elem in math_elements:
        # Find the LaTeX annotation within the math element
        annotation = math_elem.find('annotation', encoding='application/x-tex')
        if annotation and annotation.string:
            latex = annotation.string.strip()
            # Clean up the LaTeX
            latex = re.sub(r'\s+', ' ', latex)  # Remove extra whitespace
            latex = latex.replace('\\displaystyle', '')  # Remove displaystyle commands
            
            # Only include meaningful equations with our variables
            if (any(var in latex.lower() for var in ['x', 'y', '\\beta', '\\varepsilon']) 
                and len(latex) > 5 
                and not latex.isdigit()):
                equations.add(latex)
    
    return list(equations)

def colorize_variables(equation: str, colors: Dict[str, str]) -> str:
    """
    Apply colors to variables in LaTeX equation.
    Handles both regular variables and their vector/matrix forms.
    """
    try:
        # Handle vector notation first
        equation = re.sub(r'\\mathbf\{([xy])\}', 
                         lambda m: fr'\\mathbf{{\color{{{colors[m.group(1)]}}}{{{m.group(1)}}}}}', 
                         equation)
        
        # Handle subscripted variables
        for var in ['x', 'y']:
            equation = re.sub(fr'{var}_{{([^}}]+)}}', 
                            fr'\\color{{{colors[var]}}}{{{var}}}_{{\\1}}', 
                            equation)
            equation = re.sub(fr'{var}_([0-9])', 
                            fr'\\color{{{colors[var]}}}{{{var}}}_\\1', 
                            equation)
            equation = re.sub(fr'(?<![\\\w]){var}(?![\w_])', 
                            fr'\\color{{{colors[var]}}}{{{var}}}', 
                            equation)
        
        # Handle Greek letters
        equation = re.sub(r'\\beta\b', 
                         fr'\\color{{{colors["β"]}}}{{\\beta}}', 
                         equation)
        equation = re.sub(r'\\varepsilon\b', 
                         fr'\\color{{{colors["ε"]}}}{{\\varepsilon}}', 
                         equation)
        
        return equation
    except Exception as e:
        st.error(f"Error processing equation: {str(e)}")
        return equation

def create_streamlit_app():
    """Create the Streamlit web interface."""
    st.title("LaTeX Variable Colorizer")
    
    # URL input with default value
    wiki_url = st.text_input(
        "Wikipedia URL",
        value="https://en.wikipedia.org/wiki/Ordinary_least_squares",
        help="Enter the Wikipedia URL containing LaTeX equations"
    )
    
    # Color pickers for each variable
    st.subheader("Choose Colors for Variables")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        x_color = st.color_picker("x variables", "#FF0000")  # Red
    with col2:
        y_color = st.color_picker("y variables", "#00FF00")  # Green
    with col3:
        beta_color = st.color_picker("β variables", "#0000FF")  # Blue
    with col4:
        epsilon_color = st.color_picker("ε variables", "#800080")  # Purple
    
    # Color mapping dictionary
    colors = {
        'x': x_color,
        'y': y_color,
        'β': beta_color,
        'ε': epsilon_color
    }
    
    if st.button("Process Equations"):
        try:
            with st.spinner("Fetching and processing equations..."):
                # Get and process equations
                content = fetch_wikipedia_content(wiki_url)
                equations = extract_latex_equations(content)
                
                if not equations:
                    st.warning("No equations found. Please check the URL.")
                    return
                
                # Display processed equations
                st.subheader(f"Found {len(equations)} unique equations:")
                for i, eq in enumerate(equations, 1):
                    colorized_eq = colorize_variables(eq, colors)
                    # Only display if the equation was successfully colorized
                    if colorized_eq and not colorized_eq.isspace():
                        st.write(f"Equation {i}:")
                        st.latex(colorized_eq)
                        with st.expander("Show original LaTeX"):
                            st.code(eq)
                        st.markdown("---")
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    create_streamlit_app()