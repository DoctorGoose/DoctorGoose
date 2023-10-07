# Importing required libraries for Dash and plotting
import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc
from plotly.graph_objs import Figure
import numpy as np
from dash import callback_context
from scipy.integrate import solve_ivp
import time
from black import format_file_contents
from dash import callback_context
from dash.exceptions import PreventUpdate
from dash import ALL
import inspect
from black import FileMode
from dash import no_update
import re

# Initialize the Dash app with Bootstrap styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# Initial parameters for SIR model
initial_params = {'beta': 0.3, 'gamma': 0.1}
initial_conditions = [999, 1, 0]  # S, I, R

t_span = [0, 160]
t_eval = np.linspace(t_span[0], t_span[1], 160)

active_parameters = {'beta': 0.3, 'gamma': 0.1}
graveyard_parameters = {}

# Function to detect parameters from Python code
def detect_parameters(code):
    # Parse 'code' to extract parameters
    # Compare with 'active_parameters' and 'graveyard_parameters'
    # Update both as needed
    pass

# SIR model definition
def sir_model(t, y, beta, gamma):
    S, I, R = y
    return [
        -beta * S * I / 1000,
        beta * S * I / 1000 - gamma * I,
        gamma * I
    ]

# Function to run the SIR model
def run_model(params):
    time.sleep(1)  # Mimic 1s evaluation time
    sol = solve_ivp(sir_model, t_span, initial_conditions, t_eval=t_eval, args=(params['beta'], params['gamma']))
    return sol

# Function to dynamically generate sliders
def generate_sliders():
    sliders = []
    for param, value in active_parameters.items():
        slider = html.Div([
            html.Div(param),
            dcc.Input(id=f"{param}-min", type="number", value=0),
            dcc.Slider(
                id=f"{param}-slider",
                min=0,
                max=1,
                step=0.01,
                value=value,
                marks={i/10: str(i/10) for i in range(11)}
            ),
            dcc.Input(id=f"{param}-max", type="number", value=1),
        ])
        sliders.append(slider)
    return sliders

def extract_equations(code):
    pass

def format_equations(equations):
    pass

def python_to_markdown(py_code):
    markdown_code = f"```python\n{py_code}\n```"
    return markdown_code

# Initial solution
initial_sol = run_model(initial_params)
initial_code = format_file_contents(inspect.getsource(sir_model), fast=True, mode=FileMode())
initial_figure = go.Figure()

# Dash layout definition
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='plot-pane', config={'editable': True}, figure=initial_figure),
        ], width=6),
        dbc.Col([
            html.Div("Parameters"),
            html.Div(id='dynamic-sliders', children=generate_sliders())  # Initialize with at least one slider
        ], width=6),
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Textarea(
                    id='python-pane',
                    value=initial_code,
                    style={'width': '100%', 'height': 300},
                )
        ], width=6),
        dbc.Col([
            dcc.Markdown(  # Change this line
                id='markdown-pane',
                children='Initial Markdown here',  # And this line
            ),
        ], width=6),
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Button('Run Model', id='button-run'),
            html.Button('Lint Code', id='button-lint')
        ], width={"size": 6, "offset": 3}),
    ]),
    
    dcc.Store(id='parameter-store', data=active_parameters),
])
def update_parameters(n_clicks, code):
    detect_parameters(code)
    return active_parameters['beta'], active_parameters['gamma']

@app.callback(
    Output('markdown-pane', 'children'),  # Change this line
    [Input('python-pane', 'value')]
)
def update_markdown(py_code):
    equations = extract_equations(py_code)
    return format_equations(equations)

@app.callback(
    Output('python-pane', 'value'),
    [Input('button-lint', 'n_clicks')],
    [State('python-pane', 'value')]
)
def lint_python_code(n_clicks, code):
    if n_clicks is None:
        raise PreventUpdate
    return format_file_contents(code, fast=True)

@app.callback(
    [Output('plot-pane', 'figure'),
     Output('dynamic-sliders', 'children'),
     Output('parameter-store', 'data')],  # New Output
    [Input('button-run', 'n_clicks'),
     Input('button-lint', 'n_clicks')],
    [State('python-pane', 'value'),
     State('plot-pane', 'figure'),
     State('parameter-store', 'data'),
     State({'type': 'dynamic-slider', 'index': ALL}, 'value')]  # Include param_values as State
)
def update_all(n_clicks_run, n_clicks_lint, code, existing_figure, stored_params, param_values):  # Include param_values
    
    # Use stored parameters
    if stored_params is not None:
        active_parameters = stored_params

    # Inside your callback
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if 'dynamic-slider' in trigger_id and param_values is None:
        raise PreventUpdate

    if param_values is None:
        raise PreventUpdate
    
    # If dynamic sliders are not created yet, skip updating that part
    if param_values is not None and len(param_values) == len(active_parameters):
        for i, (param, value) in enumerate(active_parameters.items()):
            active_parameters[param] = param_values[i]

    if trigger_id == 'button-run':
        detect_parameters(code)
        exec(code, globals())
        sol = run_model(active_parameters)
        
        # Update or add traces based on new solution
        if existing_figure is None or not existing_figure:
            existing_figure = go.Figure()
        else:
            existing_figure = Figure(existing_figure)
        
        if len(existing_figure['data']) == 0:  # No traces, add them
            existing_figure.add_trace(go.Scatter(x=t_eval, y=sol.y[0], mode='lines', name='S'))
            existing_figure.add_trace(go.Scatter(x=t_eval, y=sol.y[1], mode='lines', name='I'))
            existing_figure.add_trace(go.Scatter(x=t_eval, y=sol.y[2], mode='lines', name='R'))
        else:  # Update existing traces
            existing_figure['data'][0]['y'] = sol.y[0]
            existing_figure['data'][1]['y'] = sol.y[1]
            existing_figure['data'][2]['y'] = sol.y[2]
            
    # Lint the code if button-lint is clicked
    if trigger_id == 'button-lint':
        code = format_file_contents(code, fast=True, mode=FileMode())
    
    if trigger_id == 'python-pane':
        exec(python_code, globals())
        
    # Generate dynamic sliders
    dynamic_sliders = generate_sliders()
    
    return existing_figure, dynamic_sliders, active_parameters  # Return updated parameters
    
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
