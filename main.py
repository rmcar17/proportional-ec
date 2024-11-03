from pathlib import Path

from proportional_ec import (
    draw_ec_map,
    generate_polygons_centroids_and_lines,
    load_topo_data,
)

if __name__ == "__main__":
    topo_file = Path("tiles.topo.json")
    gdf = load_topo_data(topo_file)

    state_polygons, state_centroids, border_lines = (
        generate_polygons_centroids_and_lines(gdf)
    )

    draw_ec_map(state_polygons, state_centroids, border_lines)
