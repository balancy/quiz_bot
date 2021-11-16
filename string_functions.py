from thefuzz import fuzz


def check_strings_similarity(string_1, string_2, min_accuracy=90):
    """Checks if strings are similar with certain accuracy.

    Args:
        string_1
        string_2
        min_accuracy: minimal accuracy for strings to be similar

    Returns:
        if strings are similar
    """

    accuracy = fuzz.token_set_ratio(string_1, string_2)

    return accuracy >= min_accuracy
