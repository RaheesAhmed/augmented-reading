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
        # Add equation alignment wrapper if not already present
        if not any(env in equation for env in ['\\begin{align', '\\begin{equation']):
            equation = f'\\begin{{align*}}\n{equation}\n\\end{{align*}}'
        
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
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        h1 {
            color: #1E3D59;
            margin-bottom: 2rem;
        }
        h2, h3 {
            color: #1E3D59;
            margin-top: 1rem;
        }
        .stButton>button {
            margin-top: 1.5rem;
        }
        .color-picker-container {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("LaTeX Equation Colorizer")
    
    # URL input and Process button in the same row
    col1, col2 = st.columns([4, 1])
    
    with col1:
        wiki_url = st.text_input(
            "Wikipedia URL",
            value="https://en.wikipedia.org/wiki/Ordinary_least_squares",
            help="Enter the Wikipedia URL containing LaTeX equations"
        )
    
    with col2:
        process_button = st.button("Process Equations", type="primary", use_container_width=True)
    
    # Variable Colors in one line
    st.markdown("### Variable Colors")
    color_cols = st.columns(4)
    
    with color_cols[0]:
        x_color = st.color_picker("x variables", "#FF4B4B", key="x")  # Softer red
    with color_cols[1]:
        y_color = st.color_picker("y variables", "#45B08C", key="y")  # Softer green
    with color_cols[2]:
        beta_color = st.color_picker("β variables", "#3B7DD8", key="beta")  # Softer blue
    with color_cols[3]:
        epsilon_color = st.color_picker("ε variables", "#9C4DD9", key="epsilon")  # Softer purple
    
    colors = {
        'x': x_color,
        'y': y_color,
        'β': beta_color,
        'ε': epsilon_color
    }

    # Process equations when button is clicked
    if process_button:
        try:
            with st.spinner("Fetching and processing equations..."):
                content = fetch_wikipedia_content(wiki_url)
                equations = extract_latex_equations(content)
                
                if not equations:
                    st.warning("⚠️ No equations found. Please check the URL.")
                    return
                
                # Display results in a nice container
                st.markdown(f"### 📊 Found {len(equations)} unique equations")
                
                for i, eq in enumerate(equations, 1):
                    with st.container():
                        colorized_eq = colorize_variables(eq, colors)
                        if colorized_eq and not colorized_eq.isspace():
                            st.markdown(f"#### Equation {i}")
                            st.latex(colorized_eq)
                            
                            # Show original LaTeX in a cleaner expander
                            with st.expander("🔍 Show original LaTeX"):
                                st.code(eq, language="latex")
                            
                            # Subtle divider
                            st.markdown("<hr style='margin: 2rem 0; opacity: 0.2;'>", 
                                      unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

    # Add helpful footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 1rem;'>
        📝 This tool helps you visualize mathematical equations by coloring variables.
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    create_streamlit_app()