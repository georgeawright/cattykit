import math
import random

TEMPERATURE_SCALER = 0.3
TEMPERATURE_EXPONENT_FLOOR = 0.5
TEMPERATURE_EXPONENT_CEILING = (1 / TEMPERATURE_SCALER) + TEMPERATURE_EXPONENT_FLOOR


def fake_reciprocal(value: float) -> float:
    """Return the Copycat "fake reciprocal" of a normalized value.

    pre: 0.0 <= value <= 1.0
    post: 0.0 <= _ <= 1.0
    post: _ + value == 1.0
    """
    return 1.0 - value


def temperature_adjust(value, temperature) -> float:
    """Adjust a normalized value according to a normalized temperature.

    pre: 0.0 <= value <= 1.0
    pre: 0.0 <= temperature <= 1.0
    post: 0.0 <= _ <= 1.0
    """
    exponent = _temperature_exponent(temperature)
    return value**exponent


def temperature_adjust_list(values, temperature) -> list[float]:
    """Adjust each normalized value in a collection by one temperature.

    pre: all(0.0 <= value <= 1.0 for value in values)
    pre: 0.0 <= temperature <= 1.0
    post: all(0.0 <= result <= 1.0 for result in _)
    """
    exponent = _temperature_exponent(temperature)
    return [value**exponent for value in values]


def _temperature_exponent(temperature: float) -> float:
    """Return the exponent used to adjust values for a temperature.

    pre: 0.0 <= temperature <= 1.0
    post: TEMPERATURE_EXPONENT_FLOOR <= _ <= TEMPERATURE_EXPONENT_CEILING
    """
    return (1 - temperature) / TEMPERATURE_SCALER + TEMPERATURE_EXPONENT_FLOOR


def temperature_adjust_probability(probability, temperature) -> float:
    if probability == 0.0:
        return 0.0
    temperature_factor = 0.1 * (1 - math.sqrt(1 - temperature))
    if probability <= 0.5:
        low_probability_factor = max(1, math.trunc(abs(math.log10(probability))))
        upper_probability = 10 ** -(low_probability_factor - 1)
        return min(
            probability + temperature_factor * (upper_probability - probability),
            0.5,
        )
    return max(probability - temperature_factor * probability, 0.5)


def select_item_from_list(items, weights):
    return select_items_from_list(items, weights, k=1)[0]


def select_items_from_list(items, weights, k):
    if k > len(items):
        raise ValueError("Cannot select more items than are available.")
    if sum(weights) == 0:
        weights = [1] * len(weights)
    if k == 1:
        return random.choices(items, weights=weights, k=1)
    remaining_items = list(items)
    remaining_weights = list(weights)
    selected_items = []
    for _ in range(k):
        selected_item = random.choices(
            remaining_items,
            weights=remaining_weights,
            k=1,
        )[0]
        selected_index = next(
            index for index, item in enumerate(remaining_items) if item is selected_item
        )
        selected_items.append(remaining_items.pop(selected_index))
        remaining_weights.pop(selected_index)

    return selected_items


def describe_count(n):
    if n < blur(2):
        return "few"
    if n < blur(4):
        return "medium"
    return "many"


def blur(n):
    """Returns a number close to n (within n plus or minus its square root)
    According to Copycat comments this would ideally be a normal distribution
    around n but that wasn't necessary."""
    blur_amount = round(math.sqrt(n))
    k = random.randint(0, blur_amount)
    sign = random.choice((1, -1))
    return n + sign * k


def structure_beats_structures(
    proposed_structure,
    proposed_structure_weight,
    incompatible_structures,
    incompatible_structure_weight,
    temperature: float,
):
    for competing_structure in incompatible_structures:
        if not structure_1_beats_structure_2(
            proposed_structure,
            proposed_structure_weight,
            competing_structure,
            incompatible_structure_weight,
            temperature,
        ):
            return False
    return True


def structure_1_beats_structure_2(
    structure_1, weight_1, structure_2, weight_2, temperature
):
    structure_1.update_strength_values()
    structure_2.update_strength_values()
    strength_list = [
        structure_1.total_strength * weight_1,
        structure_2.total_strength * weight_2,
    ]
    adjusted_strength_list = temperature_adjust_list(strength_list, temperature)
    return select_item_from_list([True, False], adjusted_strength_list)
