import folium


m = folium.Map(location=[7.8731, 80.7718], zoom_start=7)  


map_path = 'sri_lanka_map.html'
m.save(map_path)

print(f"Map saved to {map_path}")
