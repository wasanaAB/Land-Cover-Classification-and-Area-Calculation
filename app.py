from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', selected_map="sri_lanka_map.html")

@app.route('/update_map', methods=['POST'])
def update_map():
    selected_option = request.form['map_type']

    if selected_option == "Land Classification":
        map_file = "sri_lanka_classified_map_with_legend_and_flatlands.html"
    elif selected_option == "Provinces Classification":
        map_file = "sri_lanka_district_classified_map.html"
    elif selected_option == "Land Area Analysis":
        map_file = "http://127.0.0.1:8050"  # Dash app
    else:
        map_file = "sri_lanka_map.html"  # fallback/default

    return render_template('index.html', selected_map=map_file)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
