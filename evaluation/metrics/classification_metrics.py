def accuracy(expected, predicted):
    if len(expected) != len(predicted):
        raise ValueError("expected and predicted must have equal lengths")
    if not expected:
        return 0.0
    return sum(a == b for a, b in zip(expected, predicted)) / len(expected)


def field_accuracy(expected_records, predicted_records, fields):
    total = 0
    correct = 0
    for expected, predicted in zip(expected_records, predicted_records):
        for field in fields:
            total += 1
            if normalize(expected.get(field)) == normalize(predicted.get(field)):
                correct += 1
    return correct / total if total else 0.0


def normalize(value):
    if isinstance(value, str):
        return " ".join(value.casefold().strip().split())
    if isinstance(value, list):
        return sorted(normalize(x) for x in value)
    return value
