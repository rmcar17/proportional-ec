from proportional_ec.typing import Candidate, Seats, StatePo


def aggregate_election_results(
    state_results: dict[StatePo, dict[Candidate, Seats]],
) -> dict[Candidate, Seats]:
    nation_totals = {}
    for state in state_results:
        for candidate in state_results[state]:
            nation_totals[candidate] = (
                nation_totals.get(candidate, 0) + state_results[state][candidate]
            )
    return nation_totals
