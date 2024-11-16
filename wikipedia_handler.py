from bs4 import BeautifulSoup
import re
from typing import List, Tuple
import streamlit.components.v1 as components
import html

class WikipediaLatexHandler:
    def __init__(self):
        self.equation_map = {}
        self.style_map = {}
        
    def extract_and_map_equations(self, html_content: str) -> Tuple[str, List[str]]:
        """Extract LaTeX equations and replace them with placeholders."""
        soup = BeautifulSoup(html_content, 'html.parser')
        equations = []
        
        # Find all math elements
        for idx, math_elem in enumerate(soup.find_all('math')):
            annotation = math_elem.find('annotation', encoding='application/x-tex')
            if annotation and annotation.string:
                latex = annotation.string.strip()
                placeholder = f"LATEX_EQUATION_{idx}"
                self.equation_map[placeholder] = latex
                equations.append(latex)
                
                # Replace the math element with an interactive div
                new_div = soup.new_tag('div')
                new_div['class'] = 'interactive-latex'
                new_div['id'] = f'equation-{idx}'
                new_div['data-equation'] = placeholder
                new_div['data-original'] = html.escape(latex)
                math_elem.replace_with(new_div)
        
        return str(soup), equations

    def update_equation_style(self, placeholder: str, color: str):
        """Update the style of an equation."""
        if placeholder in self.equation_map:
            self.style_map[placeholder] = {
                'color': color,
                'equation': self.equation_map[placeholder]
            }
            return True
        return False

    def get_styled_equation(self, placeholder: str) -> str:
        """Get the styled version of an equation."""
        if placeholder in self.style_map:
            style = self.style_map[placeholder]
            return f"\\color{{{style['color']}}}{{{style['equation']}}}"
        return self.equation_map.get(placeholder, '')

    def create_interactive_component(self):
        """Create a custom HTML component for equation interaction."""
        js_code = """
        <script>
        function updateEquationColor(equationId, color) {
            const equation = document.getElementById(equationId);
            if (equation) {
                equation.style.color = color;
                // Store the color in the dataset
                equation.dataset.color = color;
                
                // Add MathJax refresh if needed
                if (window.MathJax) {
                    MathJax.Hub.Queue(["Typeset", MathJax.Hub, equation]);
                }
            }
        }

        // Add event listener to handle equation clicks
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.interactive-latex').forEach(function(elem) {
                elem.addEventListener('click', function() {
                    const color = this.dataset.color || '#000000';
                    console.log('Equation clicked:', this.id, 'Current color:', color);
                });
            });
        });
        </script>
        <style>
        .interactive-latex {
            cursor: pointer;
            padding: 2px;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        .interactive-latex:hover {
            background-color: rgba(0,0,0,0.05);
        }
        </style>
        """
        
        # Add current styles
        for placeholder, style_info in self.style_map.items():
            equation_id = f"equation-{placeholder.split('_')[-1]}"
            color = style_info['color']
            js_code += f"""
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                updateEquationColor("{equation_id}", "{color}");
            }});
            </script>
            """
        
        return components.html(js_code, height=0) 