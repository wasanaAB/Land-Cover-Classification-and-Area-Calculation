import folium

# Create a map centered at Sri Lanka with a zoom level that shows the full country
m = folium.Map(location=[7.8731, 80.7718], zoom_start=7)  # Centered at Sri Lanka

# Save the map as an HTML file
map_path = 'sri_lanka_map.html'
m.save(map_path)

print(f"Map saved to {map_path}")
