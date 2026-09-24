from seat_finder_bot import compare_class_states


def test_compare_class_states_equal():
    class1 = {
        "left": 5,
        "total": 30,
        "name": "CSCI 1200"
    }

    class2 = {
        "left": 5,
        "total": 30,
        "name": "CSCI 1200"
    }

    assert compare_class_states(class1, class2)


def test_compare_class_states_different_seats():
    class1 = {
        "left": 5,
        "total": 30,
        "name": "CSCI 1200"
    }

    class2 = {
        "left": 4,
        "total": 30,
        "name": "CSCI 1200"
    }

    assert not compare_class_states(class1, class2)