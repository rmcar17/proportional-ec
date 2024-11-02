import random
import geopandas as gpd
import matplotlib.pyplot as plt


def generate_polygons_and_lines(
    gdf: gpd.GeoDataFrame,
) -> tuple[dict[str, list[tuple[float, float]]], set[tuple[float, float]]]:
    state_polygons = {}

    state_border_edges = {}
    # Hexagon collections for each state
    for state, geom in zip(gdf.name, gdf.geometry):
        if geom.geom_type != "MultiPolygon":
            msg = "Unexpected geometry type"
            raise ValueError(msg)
        state_polygons[state] = []
        edge_counts = {}

        # Hexagons comprising a state
        for polygon in geom.geoms:
            exterior_coords = [  # Round all coords
                tuple(round(value, 1) for value in coord)
                for coord in polygon.exterior.coords
            ]
            state_polygons[state].append(exterior_coords)

            # Count occurence of an edge inside a state.
            # If only one occurence, it's on the border
            for i in range(len(exterior_coords) - 1):
                start = exterior_coords[i]
                end = exterior_coords[i + 1]
                edge = (min(start, end), max(start, end))
                edge_counts[edge] = edge_counts.get(edge, 0) + 1

        state_border_edges[state] = {
            edge for edge in edge_counts if edge_counts[edge] == 1
        }

        def sort_order(points):
            top_left = min(points)
            return top_left[1], -top_left[0]

        state_polygons[state].sort(key=sort_order)

    border_count = {}
    for border_edges in state_border_edges.values():
        for edge in border_edges:
            border_count[edge] = border_count.get(edge, 0) + 1

    state_borders = {edge for edge in border_count if border_count[edge] > 1}

    return state_polygons, state_borders


if __name__ == "__main__":
    gdf = gpd.read_file("tiles.topo.json")
    state_polygons, lines = generate_polygons_and_lines(gdf)

    fig, ax = plt.subplots(figsize=(20, 10))

    for state in state_polygons:
        colours = ["blue", "red"]
        num = random.randint(0, len(state_polygons[state]))
        for i, polygon in enumerate(state_polygons[state]):
            ax.add_patch(
                plt.Polygon(
                    polygon,
                    facecolor=colours[i < num],
                    edgecolor="lightgrey",
                    alpha=0.5,
                ),
            )

    for line in lines:
        x_coords, y_coords = zip(*line)
        ax.plot(x_coords, y_coords, color="black", linewidth=2)

    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")
    plt.show()
