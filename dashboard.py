import diskcache
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, DiskcacheManager
import datetime
from loguru import logger

import main as main_runner
import config
from core.report_generator import ReportGenerator

cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    background_callback_manager=background_callback_manager,
)
server = app.server
app.title = "AGOA Dashboard"

app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(html.H1("AGOA Portfolio Manager Dashboard"), width=12),
        className="mb-4 mt-4 text-center"
    ),

    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H5("Simulation Date Range"),
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        min_date_allowed=datetime.date(2018, 1, 1),
                        max_date_allowed=datetime.date.today(),
                        initial_visible_month=datetime.date.today() - datetime.timedelta(days=180),
                        start_date=config.SIMULATION_START_DATE,
                        end_date=config.SIMULATION_END_DATE,
                        display_format='YYYY-MM-DD',
                        className="dbc-dark"
                    ),
                ], width=6),
                dbc.Col(
                    dbc.Button("Run Simulation", id="run-button", color="primary", className="mt-4 w-100"),
                    width=6
                ),
            ], className="mb-2"),
        ])
    ]),

    # Progress bar — hidden by default, shown while simulation runs
    html.Div([
        html.P(id="progress-label", children="", className="text-center text-muted mt-3 mb-1"),
        dbc.Progress(
            id="simulation-progress",
            value=0,
            max=100,
            striped=True,
            animated=True,
            style={"height": "28px", "fontSize": "14px"},
            className="mb-3",
        ),
    ], id="progress-container", style={"display": "none"}),

    dbc.Row(
        dbc.Col(html.Div(id="simulation-output", className="mt-4"), width=12)
    ),
], fluid=True)


@dash.callback(
    output=Output("simulation-output", "children"),
    inputs=[
        Input("run-button", "n_clicks"),
        State("date-picker-range", "start_date"),
        State("date-picker-range", "end_date"),
    ],
    progress=[
        Output("simulation-progress", "value"),
        Output("simulation-progress", "label"),
        Output("progress-label", "children"),
    ],
    running=[
        (Output("run-button", "disabled"), True, False),
        (Output("progress-container", "style"), {"display": "block"}, {"display": "none"}),
        (Output("simulation-progress", "value"), 0, 0),
        (Output("progress-label", "children"), "Initializing...", ""),
    ],
    background=True,
    prevent_initial_call=True,
)
def run_simulation(set_progress, _, start_date_str, end_date_str):
    def progress_callback(pct, label):
        set_progress((pct, f"{pct}%", label))

    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

    pm, bm = main_runner.run_full_simulation(start_date, end_date, progress_callback=progress_callback)

    if pm is None or bm is None:
        return dbc.Alert("Simulation failed. Check logs for details.", color="danger", className="mt-4")

    set_progress((95, "95%", "Building charts..."))

    report_gen = ReportGenerator(pm, bm)
    equity_fig      = report_gen.get_equity_curve_fig().update_layout(template="plotly_dark")
    drawdown_fig    = report_gen.get_drawdown_fig().update_layout(template="plotly_dark")
    monthly_pnl_fig = report_gen.get_monthly_pnl_fig().update_layout(template="plotly_dark")
    heatmap_fig     = report_gen.get_allocation_heatmap_fig().update_layout(template="plotly_dark")

    set_progress((100, "100%", "Done!"))

    return html.Div([
        dbc.Row([dbc.Col(dcc.Graph(figure=equity_fig),      width=12)], className="mb-4"),
        dbc.Row([dbc.Col(dcc.Graph(figure=drawdown_fig),    width=12)], className="mb-4"),
        dbc.Row([dbc.Col(dcc.Graph(figure=monthly_pnl_fig), width=12)], className="mb-4"),
        dbc.Row([dbc.Col(dcc.Graph(figure=heatmap_fig),     width=12)], className="mb-4"),
    ])


if __name__ == '__main__':
    main_runner.setup_logging()
    logger.info("Starting Dash web server on http://127.0.0.1:8050")
    app.run(debug=True)
