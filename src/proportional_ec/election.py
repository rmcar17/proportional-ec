from collections.abc import Callable

from proportional_ec.typing import Candidate, Seats, StatePo, Vote


def _filter_results(
    state_results: dict[StatePo, dict[Candidate, Seats]],
) -> dict[StatePo, dict[Candidate, Seats]]:
    filtered_state_results = {}

    for state in state_results:
        filtered_state_results[state] = {}
        for candidate in state_results[state]:
            if state_results[state][candidate] > 0:
                filtered_state_results[state][candidate] = state_results[state][
                    candidate
                ]
    return filtered_state_results


def run_election(
    election_method: Callable[[dict[Candidate, Vote], Seats], dict[Candidate, Seats]],
    state_candidate_counts: dict[StatePo, dict[Candidate, Vote]],
    state_ec_votes: dict[StatePo, Seats],
) -> dict[StatePo, dict[Candidate, Seats]]:
    state_results = {}

    for state in state_candidate_counts:
        state_results[state] = election_method(
            state_candidate_counts[state],
            state_ec_votes[state],
        )

    return _filter_results(state_results)
