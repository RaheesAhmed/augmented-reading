import streamlit as st
import streamlit.components.v1 as components
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List
import html
import json

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
    equations = set()
    
    math_elements = soup.find_all('math')
    
    for math_elem in math_elements:
        annotation = math_elem.find('annotation', encoding='application/x-tex')
        if annotation and annotation.string:
            latex = annotation.string.strip()
            latex = re.sub(r'\s+', ' ', latex)
            latex = latex.replace('\\displaystyle', '')
            
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
        if not any(env in equation for env in ['\\begin{align', '\\begin{equation']):
            equation = f'\\begin{{align*}}\n{equation}\n\\end{{align*}}'
        
        equation = re.sub(r'\\mathbf\{([xy])\}', 
                         lambda m: fr'\\mathbf{{\color{{{colors[m.group(1)]}}}{{{m.group(1)}}}}}', 
                         equation)
        
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

def create_interactive_html(equations: List[str], colors: Dict[str, str]) -> str:
    """Create an interactive HTML page with color controls and equations."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LaTeX Equation Colorizer</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .color-controls { display: flex; gap: 20px; margin-bottom: 20px; }
            .color-control { display: flex; flex-direction: column; align-items: center; }
            .equation-container { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .original-latex { margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 3px; font-size: 14px; }
            .katex { font-size: 1.2em; }
            .error { color: red; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="color-controls">
    """
    
    # Add color pickers
    for var, color in colors.items():
        html_content += f"""
            <div class="color-control">
                <label>{var} variables</label>
                <input type="color" value="{color}" onchange="updateColor('{var}', this.value)">
            </div>
        """
    
    html_content += """
        </div>
        <div id="equations">
    """
    
    # Add equations
    for i, eq in enumerate(equations, 1):
        safe_eq = html.escape(eq)
        html_content += f"""
            <div class="equation-container">
                <h3>Equation {i}</h3>
                <div id="equation_{i}"></div>
                <div id="error_{i}" class="error"></div>
                <details>
                    <summary>Show original LaTeX</summary>
                    <pre class="original-latex">{safe_eq}</pre>
                </details>
            </div>
        """
    
    # Add JavaScript for color updating and equation rendering
    html_content += """
        </div>
        <script>
            let colors = """ + json.dumps(colors) + """;
            let equations = """ + json.dumps(equations) + """;
            
            function updateColor(variable, color) {
                colors[variable] = color;
                renderAllEquations();
            }
            
            function colorizeEquation(eq) {
                try {
                    // Add equation alignment wrapper if not already present
                    if (!eq.includes('\\begin{align') && !eq.includes('\\begin{equation}')) {
                        eq = '\\\\begin{align*}' + eq + '\\\\end{align*}';
                    }
                    
                    // Handle vector notation first
                    eq = eq.replace(/\\mathbf\{([xy])\}/g, (match, p1) => 
                        `\\\\mathbf{\\\\color{${colors[p1]}}{${p1}}}`
                    );
                    
                    // Handle subscripted variables
                    ['x', 'y'].forEach(var_name => {
                        // Handle subscripts with curly braces
                        eq = eq.replace(new RegExp(`${var_name}_\\{([^}]+)\\}`, 'g'), 
                            (match, p1) => `\\\\color{${colors[var_name]}}{${var_name}}_\\{${p1}\\}`
                        );
                        
                        // Handle single number subscripts
                        eq = eq.replace(new RegExp(`${var_name}_([0-9])`, 'g'), 
                            (match, p1) => `\\\\color{${colors[var_name]}}{${var_name}}_${p1}`
                        );
                        
                        // Handle standalone variables
                        eq = eq.replace(new RegExp(`(?<![\\\\\\w])${var_name}(?![\\w_])`, 'g'), 
                            `\\\\color{${colors[var_name]}}{${var_name}}`
                        );
                    });
                    
                    // Handle Greek letters
                    eq = eq.replace(/\\beta\\b/g, 
                        `\\\\color{${colors['β']}}{\\\\beta}`
                    );
                    eq = eq.replace(/\\varepsilon\\b/g, 
                        `\\\\color{${colors['ε']}}{\\\\varepsilon}`
                    );
                    
                    return eq;
                } catch (error) {
                    console.error('Error in colorizeEquation:', error);
                    return eq;
                }
            }
            
            function renderAllEquations() {
                equations.forEach((eq, i) => {
                    const containerEl = document.getElementById(`equation_${i + 1}`);
                    const errorEl = document.getElementById(`error_${i + 1}`);
                    try {
                        const colorized = colorizeEquation(eq);
                        katex.render(colorized, containerEl, {
                            displayMode: true,
                            throwOnError: false,
                            strict: false
                        });
                        errorEl.textContent = '';
                    } catch (error) {
                        console.error(`Error rendering equation ${i + 1}:`, error);
                        errorEl.textContent = `Error: ${error.message}`;
                        containerEl.textContent = eq;
                    }
                });
            }
            
            // Initial render
            document.addEventListener('DOMContentLoaded', renderAllEquations);
        </script>
    </body>
    </html>
    """
    return html_content


def create_streamlit_app():
    st.title("LaTeX Equation Colorizer")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        wiki_url = st.text_input(
            "Wikipedia URL",
            value="https://en.wikipedia.org/wiki/Ordinary_least_squares",
            help="Enter the Wikipedia URL containing LaTeX equations"
        )
    with col2:
        process_button = st.button("Process Equations", type="primary", use_container_width=True)
    
    colors = {
        'x': '#FF4B4B',
        'y': '#45B08C',
        'β': '#3B7DD8',
        'ε': '#9C4DD9'
    }

    if process_button:
        try:
            with st.spinner("Fetching and processing equations..."):
                content = fetch_wikipedia_content(wiki_url)
                equations = extract_latex_equations(content)
                
                if not equations:
                    st.warning("⚠️ No equations found. Please check the URL.")
                    return
                
                # Create interactive HTML page
                html_content = create_interactive_html(equations, colors)
                
                # Display in iframe
                components.html(html_content, height=800, scrolling=True)
                
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    create_streamlit_app()