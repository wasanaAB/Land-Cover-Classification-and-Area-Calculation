import ee
import geemap
import pandas as pd
import plotly.express as px
import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
from dash.dependencies import State
import warnings
warnings.filterwarnings("ignore")

# Initialize Earth Engine
ee.Authenticate()
ee.Initialize(project='gee-map-id1')

# Load Sri Lanka provinces
provinces = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq("ADM0_NAME", "Sri Lanka"))

# Load Sentinel-2 ImageCollection
image = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(provinces.geometry())
    .filterDate("2021-01-01", "2021-12-31")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))
    .median()
    .clip(provinces)
    .select(["B2", "B3", "B4", "B8"])
)

# Training data
vegetation = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Point([80.7698, 7.8731]), {"landcover": 0}),
    ee.Feature(ee.Geometry.Point([80.7748, 7.8781]), {"landcover": 0}),
])
flatlands = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Point([80.7715, 7.8700]), {"landcover": 1}),
    ee.Feature(ee.Geometry.Point([80.7750, 7.8650]), {"landcover": 1}),
])
urban = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Point([80.7800, 7.8800]), {"landcover": 2}),
    ee.Feature(ee.Geometry.Point([80.7840, 7.8830]), {"landcover": 2}),
])

training_points = vegetation.merge(flatlands).merge(urban)
bands = ["B2", "B3", "B4", "B8"]
landcover_names = ["Vegetation", "Flat Lands", "Urban"]

# Train classifier
training = image.select(bands).sampleRegions(
    collection=training_points,
    properties=["landcover"],
    scale=10
)

classifier = ee.Classifier.smileRandomForest(50).train(
    features=training,
    classProperty="landcover",
    inputProperties=bands
)

classified = image.select(bands).classify(classifier)

# Area calculation
def calculate_areas(fc):
    province_stats = []

    def compute_area(feature):
        province_name = feature.get("ADM1_NAME")
        stats = classified.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=feature.geometry(),
            scale=30,
            maxPixels=1e13
        )
        hist = stats.get("classification")
        return ee.Feature(None, {
            "province": province_name,
            "hist": hist
        })

    results = provinces.map(compute_area).getInfo()["features"]

    for f in results:
        props = f["properties"]
        name = props["province"]
        hist = props.get("hist", {})
        row = {"Province": name}
        total = sum(hist.values())
        for i in range(3):
            value = hist.get(str(i), 0)
            row[landcover_names[i]] = round(value * 30 * 30 / 10000, 2)
        province_stats.append(row)

    return pd.DataFrame(province_stats)

df = calculate_areas(provinces)

# Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Sri Lanka Landcover Analysis"

app.layout = html.Div([
    html.H2("Province-wise Landcover Analysis of Sri Lanka", className="text-center mt-4"),
    dbc.Container([
        dcc.Dropdown(
            id="province-dropdown",
            options=[{"label": p, "value": p} for p in df["Province"]],
            placeholder="Select a province...",
            className="mb-3"
        ),
        dbc.Row([
            dbc.Col(dcc.Graph(id="bar-chart"), width=6),
            dbc.Col(dcc.Graph(id="pie-chart"), width=6),
        ]),
        html.Br(),
        html.H4("Landcover Area Table (hectares)"),
        dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True),
        html.Br(),
        html.Button("Download CSV", id="btn_csv", className="btn btn-success"),
        dcc.Download(id="download-dataframe-csv"),
    ])
])

@app.callback(
    Output("bar-chart", "figure"),
    Output("pie-chart", "figure"),
    Input("province-dropdown", "value")
)
def update_graphs(selected_province):
    if not selected_province:
        filtered = df.mean(numeric_only=True)
        title = "Average Landcover Distribution"
    else:
        filtered = df[df["Province"] == selected_province].iloc[0]
        title = f"{selected_province} - Landcover Distribution"

    values = [filtered.get(k, 0) for k in landcover_names]
    fig_bar = px.bar(
        x=landcover_names,
        y=values,
        labels={"x": "Landcover Type", "y": "Area (ha)"},
        title=title,
        color=landcover_names
    )
    fig_pie = px.pie(
        names=landcover_names,
        values=values,
        title=title
    )
    return fig_bar, fig_pie

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    prevent_initial_call=True
)
def download_csv(n):
    return dcc.send_data_frame(df.to_csv, "sri_lanka_landcover_provinces.csv", index=False)

if __name__ == '__main__':
    app.run(debug=True, port=8050)
