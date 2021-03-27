import pytest
from typing import Dict
from pendulum import duration

from scheduling_assistant import future_alloc


def test_future_alloc():
    # ---------- Normal case ----------
    target = {
        "A": 0.5,
        "B": 0.5
    }

    past = {
        "A": duration(hours=2),
        "B": duration(hours=0)
    }

    future = future_alloc(past, target)
    assert future["B"] == past["A"]

    #past["A"] = duration(hours=5)

    #future = future_alloc(past, target)
    #assert future["B"] == past["A"]

    ## ---------- Normal case ----------

