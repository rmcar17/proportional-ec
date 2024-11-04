import random
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from math import ceil
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt

from proportional_ec.constants import PARTY_COLOUR, STATE_PO
from proportional_ec.summarise import aggregate_election_results
from proportional_ec.typing import Candidate, Party, Seats, StatePo


def normalise_state(state: str) -> StatePo:
    return STATE_PO[state.lower()]


def load_topo_data(file_path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(file_path)
    gdf["name"] = gdf["name"].apply(normalise_state)
    return gdf


def _hexagon_sort_order(points: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    top_left = max(points, key=lambda x: (x[1], -x[0]))
    return -top_left[1], top_left[0]


def generate_polygons_centroids_and_lines(
    gdf: gpd.GeoDataFrame,
) -> tuple[
    dict[StatePo, list[tuple[float, float]]],
    dict[StatePo, tuple[float, float]],
    set[tuple[float, float]],
]:
    state_polygons = {}
    state_centroids = {}
    state_border_edges = {}
    # Hexagon collections for each state
    for state, geom in zip(gdf.name, gdf.geometry):
        if geom.geom_type != "MultiPolygon":
            msg = "Unexpected geometry type"
            raise ValueError(msg)
        state_polygons[state] = []
        edge_counts = {}

        state_centroid = geom.centroid
        closest_centroid_polygon = None
        closest_centroid_distance = float("inf")

        # Hexagons comprising a state
        for polygon in geom.geoms:
            # Find closest polygon to centroid of state
            polygon_centroid = polygon.centroid
            distance_to_centre = polygon_centroid.distance(state_centroid)
            if distance_to_centre < closest_centroid_distance:
                closest_centroid_polygon = polygon_centroid
                closest_centroid_distance = distance_to_centre

            # Get data for hexagon
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

        state_centroids[state] = next(zip(*closest_centroid_polygon.xy))
        # Ensure consistent order
        state_polygons[state].sort(key=_hexagon_sort_order)

        # Get external edges for state
        state_border_edges[state] = {
            edge for edge in edge_counts if edge_counts[edge] == 1
        }

    border_count = {}
    for border_edges in state_border_edges.values():
        for edge in border_edges:
            border_count[edge] = border_count.get(edge, 0) + 1

    state_borders = {edge for edge in border_count if border_count[edge] > 1}

    return state_polygons, state_centroids, state_borders


def draw_state_polygons(
    ax: plt.Axes,
    state_polygons: dict[StatePo, list[tuple[float, float]]],
    state_seats: dict[StatePo, dict[Candidate, Seats]],
    candidate_party: dict[Candidate, Party],
    candidate_order: Sequence[Candidate],
) -> None:
    for state, polygons in state_polygons.items():
        colours = [
            PARTY_COLOUR[candidate_party[candidate]]
            for candidate in candidate_order
            if candidate in state_seats[state]
            for _ in range(state_seats[state][candidate])
        ]

        if len(colours) != len(polygons):
            msg = "Incorrect number of seats allocated."
            raise ValueError(msg)

        for i, polygon in enumerate(polygons):
            ax.add_patch(
                plt.Polygon(
                    polygon,
                    facecolor=colours[i],
                    edgecolor="lightgrey",
                    alpha=0.5,
                ),
            )


def draw_borders(ax: plt.Axes, border_lines: set[tuple[float, float]]) -> None:
    for border_line in border_lines:
        x_coords, y_coords = zip(*border_line)
        ax.plot(x_coords, y_coords, color="black", linewidth=2)


def draw_state_names(
    ax: plt.Axes,
    state_centroids: dict[StatePo, tuple[float, float]],
) -> None:
    for state in state_centroids:
        ax.text(
            state_centroids[state][0],
            state_centroids[state][1],
            state,
            horizontalalignment="center",
            verticalalignment="center",
            color="black",
            fontfamily="sans-serif",
            fontweight="roman",
        )


@dataclass
class Extremities:
    top: float
    bottom: float
    left: float
    right: float


BREAK_DOWN_MAP_OFFSET = 100
BREAK_DOWN_COLUMNS = 4


def draw_state_break_down(
    fig: plt.Figure,
    ax: plt.Axes,
    extremities: Extremities,
    state_seats: dict[StatePo, dict[Candidate, Seats]],
    candidate_party: dict[Candidate, Party],
    candidate_order: Sequence[Candidate],
) -> None:
    ax.plot(
        [extremities.left, extremities.right, extremities.right, extremities.left],
        [extremities.bottom, extremities.top, extremities.bottom, extremities.bottom],
    )

    state_box_width = 40
    state_box_height = 40
    horizontal_offset = state_box_width * (len(candidate_order) + 1.5)

    state_spaces_per_column = ceil(Fraction(len(STATE_PO) / BREAK_DOWN_COLUMNS))

    vertical_offset = (extremities.top - extremities.bottom) / (state_spaces_per_column)

    state_pos = sorted(STATE_PO.values())
    state_index = 0
    for column in range(BREAK_DOWN_COLUMNS):
        for row in range(state_spaces_per_column):
            state_name_position = (
                extremities.right + BREAK_DOWN_MAP_OFFSET + horizontal_offset * column,
                extremities.top - state_box_height - row * vertical_offset,
            )
            rect = plt.Rectangle(
                state_name_position,
                state_box_width,
                state_box_height,
                facecolor="grey",
                edgecolor="black",
                alpha=0.5,
            )
            ax.add_patch(rect)

            t = ax.text(
                state_name_position[0] + state_box_width / 2,
                extremities.top - row * vertical_offset - state_box_height / 2,
                state_pos[state_index],
                horizontalalignment="center",
                verticalalignment="center",
                color="black",
                fontfamily="sans-serif",
                fontweight="roman",
            )

            for i, candidate in enumerate(candidate_order):
                rect = plt.Rectangle(
                    (
                        state_name_position[0] + (i + 1) * state_box_width,
                        state_name_position[1],
                    ),
                    state_box_width,
                    state_box_height,
                    facecolor=PARTY_COLOUR[candidate_party[candidate]],
                    edgecolor="black",
                    alpha=0.6,
                )
                ax.add_patch(rect)

            state_index += 1
            if state_index >= len(state_pos):
                break
        if state_index >= len(state_pos):
            break


def get_extremities(
    state_polygons: dict[StatePo, list[tuple[float, float]]],
) -> Extremities:
    top = float("-inf")
    bottom = float("inf")
    left = float("inf")
    right = float("-inf")

    for state in state_polygons:
        for points in state_polygons[state]:
            for x, y in points:
                top = max(top, y)
                bottom = min(bottom, y)
                left = min(left, x)
                right = max(right, x)
    return Extremities(top, bottom, left, right)


def draw_ec_map(
    topo_file: str | Path,
    state_seats: dict[StatePo, dict[Candidate, Seats]],
    candidate_party: dict[Candidate, Party],
) -> None:
    overall_results = aggregate_election_results(state_seats)
    candidate_order = sorted(
        overall_results,
        key=lambda x: overall_results[x],
        reverse=True,
    )
    candidate_order.append(candidate_order.pop(1))  # Winner on top, runner up on bottom
    print(candidate_order)

    state_polygons, state_centroids, border_lines = (
        generate_polygons_centroids_and_lines(load_topo_data(topo_file))
    )

    fig, ax = plt.subplots(figsize=(20, 10))

    draw_state_polygons(
        ax,
        state_polygons,
        state_seats,
        candidate_party,
        candidate_order,
    )
    draw_borders(ax, border_lines)
    draw_state_names(ax, state_centroids)

    draw_state_break_down(
        fig,
        ax,
        get_extremities(state_polygons),
        state_seats,
        candidate_party,
        sorted(
            overall_results,
            key=lambda x: overall_results[x],
            reverse=True,
        ),
    )

    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")
    plt.savefig("out.png")
    plt.show()
