# app.py

"""
Flask Application for Intelligent Tutoring System (ITS)

This application allows users to select geometric shapes, input measurements,
and receive calculated results (e.g., area, volume). It integrates with an OWL
ontology to fetch formulas and perform calculations dynamically using sympy.

Author: Your Name
Date: YYYY-MM-DD
"""

from flask import Flask, render_template, request
from owlready2 import get_ontology
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

app = Flask(__name__)

# Load the ontology at startup
ONTOLOGY_PATH = "geometric_shapes.owl"  # Ensure this path is correct
onto = get_ontology(f"file://{ONTOLOGY_PATH}").load()

def get_shape_class(shape_name):
    """
    Retrieves the ontology class corresponding to the given shape name.

    Args:
        shape_name (str): Name of the shape (e.g., 'Triangle').

    Returns:
        owlready2.ThingClass: The ontology class for the shape.
    """
    shape = onto.search_one(iri=f"*{shape_name.capitalize()}")
    return shape

def evaluate_formula(formula_str, variables):
    """
    Evaluates a mathematical formula with given variables using sympy.

    Args:
        formula_str (str): The formula as a string (e.g., "0.5 * base * height").
        variables (dict): Dictionary of variable values (e.g., {'base': 5, 'height': 10}).

    Returns:
        float: The result of the evaluated formula.
    """
    try:
        # Define sympy symbols based on variables
        sym_vars = sp.symbols(list(variables.keys()))
        sym_dict = dict(zip([str(s) for s in sym_vars], sym_vars))
        
        # Parse the formula
        expr = parse_expr(formula_str, local_dict=sym_dict, evaluate=True)
        
        # Substitute variables with their values
        expr_sub = expr.subs(variables)
        
        # Evaluate the expression
        result = expr_sub.evalf()
        
        return float(result)
    except Exception as e:
        print(f"Error evaluating formula '{formula_str}': {e}")
        return None

def calculate_measurements(shape, measurements):
    """
    Calculates the required measurements based on the shape and input measurements.

    Args:
        shape (owlready2.ThingClass): The ontology class for the shape.
        measurements (dict): Dictionary of user-provided measurements.

    Returns:
        dict: Calculated measurements.
    """
    results = {}
    shape_name = shape.name.lower()

    # Mapping of measurement properties to their ontology property names
    measurement_properties = {
        'Area': 'has_area',
        'Perimeter': 'has_perimeter',
        'Volume': 'has_volume',
        'Surface Area': 'has_surface_area',
        'Circumference': 'has_circumference',
    }

    # Iterate over each measurement property
    for display_name, prop_name in measurement_properties.items():
        # Retrieve the formula from the ontology
        if hasattr(shape, prop_name):
            formula_list = getattr(shape, prop_name)
            if formula_list:
                formula_str = formula_list[0]
                # Extract variables from the formula
                # Assuming variable names match measurement keys
                formula_vars = {}
                for var in measurements.keys():
                    if var in formula_str:
                        formula_vars[var] = measurements[var]
                # Evaluate the formula
                result = evaluate_formula(formula_str, formula_vars)
                if result is not None:
                    results[display_name] = result

    return results

@app.route('/')
def home():
    """
    Renders the home page.

    Returns:
        Rendered HTML template for the home page.
    """
    return render_template('home.html')

@app.route('/select_shape', methods=['GET', 'POST'])
def select_shape():
    """
    Handles shape selection and redirects to input page.

    GET: Renders the shape selection form.
    POST: Processes the selected shape and renders the input form.

    Returns:
        Rendered HTML template.
    """
    if request.method == 'POST':
        selected_shape = request.form.get('shape')
        if selected_shape:
            return render_template('select_shape.html', shape=selected_shape)
    # Get all subclasses of Shape to display as options
    shapes = [cls.name for cls in onto.Shape.subclasses()]
    return render_template('select_shape.html', shapes=shapes)

@app.route('/calculate', methods=['POST'])
def calculate():
    """
    Processes user inputs, performs calculations, and renders the results page.

    Args:
        POST request containing shape and measurements.

    Returns:
        Rendered HTML template for the results page.
    """
    if request.method == 'POST':
        shape_name = request.form.get('shape').lower()
        measurements = {}
        
        # Extract measurements based on shape
        if shape_name == 'triangle':
            measurements['base'] = float(request.form.get('base', 0))
            measurements['height'] = float(request.form.get('height', 0))
            # Assuming right-angled triangle; hypotenuse can be calculated if needed
        
        elif shape_name in ['square', 'pentagon', 'hexagon', 'cube']:
            measurements['side_length'] = float(request.form.get('side_length', 0))
        
        elif shape_name == 'circle':
            measurements['radius'] = float(request.form.get('radius', 0))
        
        elif shape_name == 'rectangle':
            measurements['length'] = float(request.form.get('length', 0))
            measurements['width'] = float(request.form.get('width', 0))
        
        elif shape_name == 'sphere':
            measurements['radius'] = float(request.form.get('radius', 0))
        
        elif shape_name in ['cylinder', 'cone']:
            measurements['radius'] = float(request.form.get('radius', 0))
            measurements['height'] = float(request.form.get('height', 0))
        
        else:
            # Handle unknown shape
            return render_template('result.html', error="Unknown shape selected.")
        
        # Retrieve the shape class from ontology
        shape_class = get_shape_class(shape_name)
        if not shape_class:
            return render_template('result.html', error="Shape not found in ontology.")
        
        # Perform calculations
        results = calculate_measurements(shape_class, measurements)
        
        return render_template('result.html', shape=shape_name.capitalize(), measurements=measurements, results=results)
    
    return render_template('home.html')

@app.route('/about')
def about():
    """
    Renders the about page.

    Returns:
        Rendered HTML template for the about page.
    """
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
