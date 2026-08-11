import math
import random

TEMPERATURE_SCALER = 0.3
TEMPERATURE_EXPONENT_FLOOR = 0.005


def temperature_adjust(value, temperature):
    exponent = (1 - temperature) / TEMPERATURE_SCALER + TEMPERATURE_EXPONENT_FLOOR
    return value**exponent


def temperature_adjust_list(values, temperature):
    exponent = (1 - temperature) / TEMPERATURE_SCALER + TEMPERATURE_EXPONENT_FLOOR
    return [value**exponent for value in values]


def select_item_from_list(items, weights):
    return select_items_from_list(items, weights, k=1)[0]


def select_items_from_list(items, weights, k):
    if k > len(items):
        raise ValueError("Cannot select more items than are available.")

    weights = [weight + 1e-5 for weight in weights]
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
            index
            for index, item in enumerate(remaining_items)
            if item is selected_item
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
