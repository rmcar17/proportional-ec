from fractions import Fraction
from math import floor
from proportional_ec.typing import Candidate, Seats, Vote


def _total_votes(candidate_votes: dict[Candidate, Vote]) -> int:
    return sum(candidate_votes.values())


def droop_quota(total_votes: int, available_seats: int) -> Fraction:
    return Fraction(total_votes, available_seats + 1)


def run_largest_remainder_election(
    candidate_votes: dict[Candidate, Vote],
    available_seats: Seats,
    quota_size: Fraction,
) -> dict[Candidate, Seats]:
    candidate_seats = {}

    candidate_quota_remainders = {}
    for candidate in candidate_votes:
        quota = Fraction(candidate_votes[candidate], quota_size)
        whole_seats = floor(quota)  # Seats which can be immediately allocated

        candidate_seats[candidate] = whole_seats
        candidate_quota_remainders[candidate] = quota - whole_seats

    seats_allocated = sum(candidate_seats.values())
    if seats_allocated > available_seats:
        msg = "More seats allocated than available. Can happen if there are no fractional components for the droop quota."
        raise RuntimeError(msg)
    seats_remaining = available_seats - seats_allocated

    if seats_remaining == 0:
        return candidate_seats

    remainder_allocation_priority = sorted(
        candidate_seats,
        key=lambda candidate: candidate_quota_remainders[candidate],
        reverse=True,
    )

    for candidate in remainder_allocation_priority[:seats_remaining]:
        candidate_seats[candidate] += 1

    if (
        candidate_quota_remainders[remainder_allocation_priority[seats_remaining - 1]]
        == candidate_quota_remainders[remainder_allocation_priority[seats_remaining]]
    ):
        msg = "Tie when allocating largest remainder seats."
        raise RuntimeError(msg)

    if sum(candidate_seats.values()) != available_seats:
        msg = "Invalid number of seats allocated."
        raise RuntimeError(msg)

    return candidate_seats


def run_droop_quota_largest_remainder(
    candidate_votes: dict[Candidate, Vote],
    available_seats: Seats,
) -> dict[Candidate, Seats]:
    total_votes = _total_votes(candidate_votes)
    quota_size = droop_quota(total_votes, available_seats)

    return run_largest_remainder_election(candidate_votes, available_seats, quota_size)
