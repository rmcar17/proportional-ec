from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from math import ceil
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patheffects import withStroke

from proportional_ec.constants import PARTY_COLOUR, STATE_PO
from proportional_ec.summarise import aggregate_election_results
from proportional_ec.typing import Candidate, Party, Seats, StatePo

TEXT_PATH_EFFECTS = [withStroke(linewidth=3, foreground="black")]


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
    for state, geom in zip(gdf.name, gdf.geometry, strict=True):
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

        state_centroids[state] = next(zip(*closest_centroid_polygon.xy, strict=True))
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
        x_coords, y_coords = zip(*border_line, strict=True)
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
            color="white",
            path_effects=TEXT_PATH_EFFECTS,
            fontfamily="sans-serif",
            fontweight="roman",
        )


@dataclass
class Extremities:
    top: float
    bottom: float
    left: float
    right: float


AGGREGATE_MAP_OFFSET = 50
AGGREGATE_BAR_WIDTH = 60
AGGREGATE_TEXT_OFFSET = 20


def draw_aggregate(
    ax: plt.Axes,
    extremities: Extremities,
    overall_results: dict[Candidate, Seats],
    candidate_party: dict[Candidate, Party],
    candidate_order: Sequence[Candidate],
) -> None:
    # Go from bottom up, runner up at bottom, winner at top
    candidate_order = candidate_order[1:] + [candidate_order[0]]

    aggregate_bar_height = extremities.top - extremities.bottom

    total_seats = sum(overall_results.values())

    sub_bar_position = (
        extremities.left - AGGREGATE_MAP_OFFSET - AGGREGATE_BAR_WIDTH,
        extremities.bottom,
    )
    for i, candidate in enumerate(candidate_order):
        sub_bar_height = (
            Fraction(overall_results[candidate], total_seats) * aggregate_bar_height
        )
        rect = plt.Rectangle(
            sub_bar_position,
            AGGREGATE_BAR_WIDTH,
            sub_bar_height,
            facecolor=PARTY_COLOUR[candidate_party[candidate]],
            edgecolor="black",
            alpha=0.5,
        )
        ax.add_patch(rect)

        if overall_results[candidate] > 30:
            x = sub_bar_position[0] + AGGREGATE_BAR_WIDTH / 2
            if i == 0:
                y = sub_bar_position[1] + AGGREGATE_TEXT_OFFSET
                va = "bottom"
            elif i == len(candidate_order) - 1:
                y = sub_bar_position[1] + sub_bar_height - AGGREGATE_TEXT_OFFSET
                va = "top"
            else:
                y = sub_bar_position[1] + sub_bar_height / 2
                va = "center"
            ax.text(
                x,
                y,
                str(overall_results[candidate]),
                fontweight="roman",
                fontfamily="sans-serif",
                horizontalalignment="center",
                verticalalignment=va,
                color="white",
                path_effects=TEXT_PATH_EFFECTS,
            )

        sub_bar_position = (sub_bar_position[0], sub_bar_position[1] + sub_bar_height)


BREAK_DOWN_MAP_OFFSET = 50
BREAK_DOWN_COLUMNS = 3
STATE_BOX_WIDTH = 40
STATE_BOX_HEIGHT = 40


def draw_state_break_down(
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

    state_spaces_per_column = ceil(Fraction(len(STATE_PO) / BREAK_DOWN_COLUMNS))

    vertical_offset = (extremities.top - extremities.bottom) / (state_spaces_per_column)

    state_pos = sorted(STATE_PO.values())
    state_index = 0
    current_horizontal_offset = 0
    for _ in range(BREAK_DOWN_COLUMNS):
        horizontal_start = extremities.right + BREAK_DOWN_MAP_OFFSET
        max_boxes_in_row = 1
        for row in range(state_spaces_per_column):
            state_name_position = (
                horizontal_start + current_horizontal_offset,
                extremities.top - STATE_BOX_HEIGHT - row * vertical_offset,
            )
            rect = plt.Rectangle(
                state_name_position,
                STATE_BOX_WIDTH,
                STATE_BOX_HEIGHT,
                facecolor="grey",
                edgecolor="black",
                alpha=0.5,
            )
            ax.add_patch(rect)

            ax.text(
                state_name_position[0] + STATE_BOX_WIDTH / 2,
                extremities.top - row * vertical_offset - STATE_BOX_HEIGHT / 2,
                state_pos[state_index],
                horizontalalignment="center",
                verticalalignment="center",
                color="white",
                path_effects=TEXT_PATH_EFFECTS,
                fontfamily="sans-serif",
                fontweight="roman",
            )

            skipped = 0
            for i, candidate in enumerate(candidate_order):
                if state_seats[state_pos[state_index]].get(candidate, 0) == 0:
                    skipped += 1
                    continue

                state_candidate_result_position = (
                    state_name_position[0] + (i + 1 - skipped) * STATE_BOX_WIDTH,
                    state_name_position[1],
                )
                rect = plt.Rectangle(
                    state_candidate_result_position,
                    STATE_BOX_WIDTH,
                    STATE_BOX_HEIGHT,
                    facecolor=PARTY_COLOUR[candidate_party[candidate]],
                    edgecolor="black",
                    alpha=0.5,
                )
                ax.add_patch(rect)
                ax.text(
                    state_candidate_result_position[0] + STATE_BOX_WIDTH / 2,
                    state_candidate_result_position[1] + STATE_BOX_HEIGHT / 2,
                    state_seats[state_pos[state_index]].get(candidate, 0),
                    horizontalalignment="center",
                    verticalalignment="center",
                    color="white",
                    path_effects=TEXT_PATH_EFFECTS,
                    fontfamily="sans-serif",
                    fontweight="roman",
                )
            not_skipped = len(candidate_order) - skipped
            max_boxes_in_row = max(max_boxes_in_row, not_skipped + 1)

            state_index += 1
            if state_index >= len(state_pos):
                break
        current_horizontal_offset += STATE_BOX_WIDTH * (max_boxes_in_row + 0.5)
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


def normalise_name(candidate: Candidate) -> str:
    candidate = candidate.replace('""', '"')

    is_junior = candidate.endswith(" JR")
    if is_junior:
        candidate = candidate[:-2]

    candidate = candidate.title()

    if candidate.startswith("Mc"):
        candidate = candidate[:2] + candidate[2].upper() + candidate[3:]

    candidate = " ".join(reversed(candidate.split(", ")))

    if is_junior:
        candidate += " Jr."
    return candidate


LEGEND_FIGURE_OFFSET = 10


def draw_legend(
    ax: plt.Axes,
    extremities: Extremities,
    overall_results: dict[Candidate, Seats],
    candidate_party: dict[Candidate, Party],
    candidate_order: Sequence[Candidate],
) -> None:
    handles = []
    for candidate in candidate_order:
        party_colour = PARTY_COLOUR[candidate_party[candidate]]
        handles.append(
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=party_colour,
                markersize=10,
                label=f"{normalise_name(candidate)} ({overall_results[candidate]} EV{"s" if overall_results[candidate] != 1 else ""})",
            ),
        )
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    # Convert physical coordinates to data coordinates
    normalized_x = (
        extremities.left
        - xlim[0]
        - AGGREGATE_MAP_OFFSET
        - AGGREGATE_BAR_WIDTH
        - LEGEND_FIGURE_OFFSET
    ) / (xlim[1] - xlim[0])
    normalized_y = (
        extremities.bottom + (extremities.top - extremities.bottom) / 2 - ylim[0]
    ) / (ylim[1] - ylim[0])
    ax.legend(
        handles=handles,
        loc="center right",
        bbox_to_anchor=(normalized_x, normalized_y),
        title="Election Results",
        fontsize="large",
    )


def draw_ec_map(
    topo_file: str | Path,
    year: int,
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

    extremities = get_extremities(state_polygons)
    candidate_order = sorted(
        overall_results,
        key=lambda x: overall_results[x],
        reverse=True,
    )
    draw_state_break_down(
        ax,
        extremities,
        state_seats,
        candidate_party,
        candidate_order,
    )

    draw_aggregate(ax, extremities, overall_results, candidate_party, candidate_order)
    draw_legend(ax, extremities, overall_results, candidate_party, candidate_order)

    ax.set_title(
        f"{year} Presidential Election",
        loc="center",
        fontsize=24,
        x=0.41,
        y=0.92,
    )
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")

    plt.savefig("out.png")
    plt.show()
