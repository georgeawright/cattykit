TEMPERATURE_SCALER = 0.3
TEMPERATURE_EXPONENT_FLOOR = 0.005


def temperature_adjust(value, temperature):
    exponent = (1 - temperature) / TEMPERATURE_SCALER + TEMPERATURE_EXPONENT_FLOOR
    return value**exponent
