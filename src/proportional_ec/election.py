from typing import Callable

from proportional_ec.typing import Candidate, Seats, StatePo, Vote


def run_election(
    election_method: Callable[[dict[Candidate, Vote], Seats], dict[Candidate, Seats]],
    state_candidate_counts: dict[StatePo, dict[Candidate, Vote]],
    state_ec_votes: dict[StatePo, Seats],
) -> dict[StatePo, dict[Candidate, Seats]]:
    state_results = {}

    for state in state_candidate_counts:
        state_results[state] = election_method(
            state_candidate_counts[state], state_ec_votes[state]
        )

    return state_results
