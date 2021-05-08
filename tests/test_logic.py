import pytest

from logic import prioritize


def test_prioritize_no_goal() -> None:
    goal = {}
    past = []
    future = prioritize(goal, past)
    assert future == None


def test_prioritize_no_past() -> None:
    past = []

    goal = { "A": 3, "B": 2 }
    future = prioritize(goal, past)
    assert future == [ ("A", 0), ("B", 0) ]

    goal = { "X": 4, "Y": 5 }
    future = prioritize(goal, past)
    assert future == [ ("Y", 0), ("X", 0) ]

    goal = { "P": 7 }
    future = prioritize(goal, past)
    assert future == [ ("P", 0) ]


def test_prioritize_equal() -> None:
    goal = { "A": 1, "B": 1 }

    past = [ ("A", 2), ("B", 1) ]
    future = prioritize(goal, past)
    assert future == [ ("B", 1), ("A", 0) ]


def test_prioritize_not_started() -> None:
    goal = { "A": 1, "B": 1, "C": 1, "D": 1, "E": 1, "F": 1}
    
    past = [ ("B", 1), ("A", 20), ("B", 20), ("C", 10) ]
    future = prioritize(goal, past)
    assert future == [ ("C", 11), ("D", 21), ("E", 21), ("F", 21), ("A", 1), ("B", 0) ]


def test_prioritize_equal_2() -> None:
    goal = { "A": 1, "B": 1 }
    
    past = [ ("A", 1), ("B", 2)]
    future = prioritize(goal, past)
    assert future == [ ("A", 1), ("B", 0) ]


def test_prioritize_equal_3() -> None:
    goal = { "A": 1, "B": 1, "C": 1, "D": 1}
    
    past = [ ("A", 1), ("B", 1), ("C", 3), ("D", 2) ]
    future = prioritize(goal, past)
    assert future == [ ("D", 1), ("A", 2), ("B", 2), ("C", 0) ]


def test_prioritize_incorrect_order() -> None:
    goal = { "A": 1, "B": 1, "C": 1 }
    
    past = [ ("C", 1) ]
    future = prioritize(goal, past)
    assert future == [ ("A", 1), ("B", 1), ("C", 0) ]


def test_prioritize_two_cycles() -> None:
    goal = { "A": 1, "B": 1, "C": 1, "D": 1 }
    
    past = [ ("A", 2), ("B", 2), ("C", 2), ("A", 1), ("B", 1) ]
    future = prioritize(goal, past)
    assert future == [ ("D", 3), ("A", 0), ("B", 0), ("C", 1) ]
