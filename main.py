import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Set, Tuple
import json
import hashlib

class LatexParser:
    """
    A class to handle the parsing and processing of LaTeX equations from Wikipedia pages.
    """
    def __init__(self):
        # Common LaTeX variable patterns
        self.variable_patterns = {
            'single': r'(?<![\\\w])([a-zA-Z])(?![\w_])',  # Single letter variables
            'subscript': r'([a-zA-Z])_\{([^}]+)\}|([a-zA-Z])_([0-9])',  # Subscripted variables
            'greek': r'\\([a-zA-Z]+)\b',  # Greek letters
            'vector': r'\\mathbf\{([a-zA-Z])\}'  # Vector notation
        }
        
    def fetch_wikipedia_content(self, url: str) -> str:
        """Fetch content from Wikipedia page with error handling."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            st.error(f"Error fetching Wikipedia content: {str(e)}")
            return ""

    def extract_equations(self, html_content: str) -> List[Tuple[str, str]]:
        """
        Extract LaTeX equations and their context from Wikipedia HTML content.
        Returns a list of tuples (equation, context).
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        equations = []
        
        # Find all math elements with display style
        math_elements = soup.find_all(['span', 'math'], class_=['mwe-math-element'])
        
        for math_elem in math_elements:
            # Get context (surrounding paragraph text)
            context = self._get_equation_context(math_elem)
            
            # Find LaTeX annotation
            annotation = math_elem.find('annotation', encoding='application/x-tex')
            if annotation and annotation.string:
                latex = self._clean_latex(annotation.string)
                if self._is_meaningful_equation(latex):
                    equations.append((latex, context))
        
        return equations

    def _clean_latex(self, latex: str) -> str:
        """Clean up LaTeX code for better processing."""
        # Remove display style commands but preserve the content
        latex = re.sub(r'\\displaystyle\s*', '', latex)
        
        # Handle vector notation consistently
        latex = re.sub(r'\\mathbf\s*\{([^}]+)\}', r'\\boldsymbol{\1}', latex)
        latex = re.sub(r'\\vec\s*\{([^}]+)\}', r'\\boldsymbol{\1}', latex)
        
        # Handle left/right delimiters - preserve them but clean up spacing
        latex = re.sub(r'\\left\s*([{[(|])', r'\\left\1', latex)
        latex = re.sub(r'\\right\s*([})\]|])', r'\\right\1', latex)
        
        # Clean up subscripts and superscripts
        latex = re.sub(r'_\s*(\d+)', r'_{\1}', latex)  # Add braces to single number subscripts
        latex = re.sub(r'\^\s*(\d+)', r'^{\1}', latex)  # Add braces to single number superscripts
        
        # Clean up spacing around operators
        latex = re.sub(r'\s*([=+\-*/])\s*', r' \1 ', latex)
        
        # Remove multiple spaces
        latex = re.sub(r'\s+', ' ', latex)
        
        return latex.strip()

    def _is_meaningful_equation(self, latex: str) -> bool:
        """Check if equation is meaningful (contains variables and is not too simple)."""
        return (len(latex) > 5 and 
                not latex.isdigit() and 
                any(re.search(pattern, latex) for pattern in self.variable_patterns.values()))

    def _get_equation_context(self, math_elem) -> str:
        """Get the surrounding context of an equation."""
        parent = math_elem.find_parent(['p', 'div'])
        if parent:
            # Get all text nodes while excluding math elements
            texts = []
            for element in parent.contents:
                if isinstance(element, str):
                    # Direct text node
                    texts.append(element.strip())
                elif element.name != 'math':
                    # Non-math element
                    texts.append(element.get_text().strip())
            
            context = ' '.join(text for text in texts if text)
            return context[:200] + '...' if len(context) > 200 else context
        return ""

    def identify_variables(self, latex: str) -> Dict[str, Set[str]]:
        """
        Identify all variables in a LaTeX equation and categorize them.
        """
        variables = {
            'single': set(),
            'subscript': set(),
            'greek': set(),
            'vector': set()
        }
        
        # Updated patterns with more precise matching
        patterns = {
            'single': r'(?<![\\\w])([a-zA-Z])(?![\w_\{])',  # Single letter variables
            'subscript': r'([a-zA-Z])_\{([^}]+)\}|([a-zA-Z])_([0-9])',  # Subscripted variables
            'greek': r'\\(?!(?:left|right|begin|end|boldsymbol|mathbf|vec))([a-zA-Z]+)(?![a-zA-Z])',  # Greek letters excluding commands
            'vector': r'\\(?:boldsymbol|mathbf|vec)\{([a-zA-Z][^}]*)\}'  # Vector notation
        }
        
        for var_type, pattern in patterns.items():
            matches = re.finditer(pattern, latex)
            for match in matches:
                if var_type == 'subscript':
                    base = match.group(1) or match.group(3)
                    sub = match.group(2) or match.group(4)
                    variables[var_type].add(f"{base}_{{{sub}}}")
                elif var_type == 'greek':
                    var = '\\' + match.group(1)
                    variables[var_type].add(var)
                elif var_type == 'vector':
                    var = match.group(1)
                    variables[var_type].add(var)
                else:
                    var = match.group(1)
                    variables[var_type].add(var)
        
        return variables

def create_streamlit_interface():
    """Create the Streamlit web interface with enhanced features."""
    st.set_page_config(page_title="LaTeX Equation Colorizer", layout="wide")
    
    # Enhanced Custom CSS
    st.markdown("""
        <style>
        .equation-container {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .equation-container:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        .context-box {
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 1rem;
        }
        .variable-list {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 1rem 0;
        }
        .color-customizer {
            padding: 1rem;
            background: #fff;
            border-radius: 0.5rem;
            margin-top: 1rem;
        }
        .latex-code {
            background: #f1f1f1;
            padding: 0.5rem;
            border-radius: 0.3rem;
            font-family: monospace;
            margin-top: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Enhanced LaTeX Equation Colorizer")
    
    # Initialize session state for storing equation colors
    if 'equation_colors' not in st.session_state:
        st.session_state.equation_colors = {}
    
    # Initialize a global counter in session state if it doesn't exist
    if 'color_picker_counter' not in st.session_state:
        st.session_state.color_picker_counter = 0
    
    # Initialize parser
    parser = LatexParser()
    
    # Sidebar for global settings
    with st.sidebar:
        st.header("Settings")
        url = st.text_input(
            "Wikipedia URL",
            value="https://en.wikipedia.org/wiki/Ordinary_least_squares"
        )
        
        st.subheader("Default Color Scheme")
        default_colors = {
            'x': '#FF4B4B',  # Red
            'y': '#45B08C',  # Green
            'β': '#3B7DD8',  # Blue
            'ε': '#9C4DD9'   # Purple
        }
        
        # Global color scheme
        color_scheme = {}
        for var, color in default_colors.items():
            color_scheme[var] = st.color_picker(
                f"{var} variables",
                color,
                key=f"default_{var}_color"
            )
        
        # Advanced settings
        st.subheader("Advanced Settings")
        show_context = st.checkbox("Show equation context", value=True)
        group_similar = st.checkbox("Group similar variables", value=True)
    
    # Main content
    if st.button("Process Equations", type="primary"):
        with st.spinner("Fetching and processing equations..."):
            content = parser.fetch_wikipedia_content(url)
            if content:
                equations = parser.extract_equations(content)
                
                st.markdown(f"### Found {len(equations)} equations")
                
                for i, (eq, context) in enumerate(equations, 1):
                    # Generate unique ID for each equation
                    eq_id = hashlib.md5(eq.encode()).hexdigest()
                    
                    # Initialize colors for this equation if not exists
                    if eq_id not in st.session_state.equation_colors:
                        st.session_state.equation_colors[eq_id] = color_scheme.copy()
                    
                    with st.container():
                        st.markdown(f"#### Equation {i}")
                        
                        # Create tabs for different views
                        eq_tab, custom_tab, latex_tab = st.tabs(["Equation", "Customize", "LaTeX Code"])
                        
                        with eq_tab:
                            if show_context:
                                st.markdown(f"<div class='context-box'>{context}</div>", 
                                          unsafe_allow_html=True)
                            
                            # Display equation with current colors
                            variables = parser.identify_variables(eq)
                            colorized_eq = colorize_equation(
                                eq, 
                                variables, 
                                st.session_state.equation_colors[eq_id]
                            )
                            st.latex(colorized_eq)
                        
                        with custom_tab:
                            # Color customization section
                            st.markdown("<div class='color-customizer'>", unsafe_allow_html=True)
                            
                            # Identify variables
                            variables = parser.identify_variables(eq)
                            
                            cols = st.columns(4)
                            current_col = 0
                            
                            # Create color pickers for each variable type
                            for var_type, vars in variables.items():
                                for var in sorted(vars):
                                    base_var = var[0] if var_type != 'greek' else var
                                    
                                    # Increment the global counter
                                    st.session_state.color_picker_counter += 1
                                    
                                    # Create a unique key using the global counter
                                    unique_key = f"color_picker_{eq_id}_{st.session_state.color_picker_counter}"
                                    
                                    with cols[current_col]:
                                        new_color = st.color_picker(
                                            f"{var} ({var_type})",
                                            st.session_state.equation_colors[eq_id].get(base_var, '#000000'),
                                            key=unique_key
                                        )
                                        st.session_state.equation_colors[eq_id][base_var] = new_color
                                            
                                    current_col = (current_col + 1) % 4
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            # Preview of colorized equation
                            st.markdown("### Preview")
                            st.latex(colorized_eq)
                        
                        with latex_tab:
                            st.code(eq, language="latex")
                        
                        st.markdown("---")

def colorize_equation(latex: str, variables: Dict[str, Set[str]], 
                     color_scheme: Dict[str, str]) -> str:
    """
    Apply colors to variables in LaTeX equation based on the color scheme.
    """
    colorized = latex
    
    # Add equation alignment if not present
    if not any(env in colorized for env in ['\\begin{align', '\\begin{equation']):
        colorized = f'\\begin{{align*}}\n{colorized}\n\\end{{align*}}'
    
    # Sort variables by length (longest first) to avoid partial matches
    for var_type, vars in variables.items():
        sorted_vars = sorted(vars, key=len, reverse=True)
        for var in sorted_vars:
            if var[0] in color_scheme:  # Match base variable (without subscript)
                color = color_scheme[var[0]]
                if var_type == 'greek':
                    colorized = re.sub(
                        fr'({var})(?![a-zA-Z])',
                        fr'\\color{{{color}}}{{\1}}',
                        colorized
                    )
                elif var_type == 'vector':
                    colorized = re.sub(
                        fr'\\(?:boldsymbol|mathbf|vec)\{{{var}\}}',
                        fr'\\boldsymbol{{\\color{{{color}}}{{{var}}}}}',
                        colorized
                    )
                elif var_type == 'subscript':
                    base, sub = var.split('_', 1)
                    colorized = re.sub(
                        fr'({base})_{sub}',
                        fr'\\color{{{color}}}{{\1}}_{sub}',
                        colorized
                    )
                else:
                    colorized = re.sub(
                        fr'(?<![\\\w])({var})(?![\w_{{}}])',
                        fr'\\color{{{color}}}{{\1}}',
                        colorized
                    )
    
    return colorized

if __name__ == "__main__":
    create_streamlit_interface()