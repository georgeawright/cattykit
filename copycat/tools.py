TEMPERATURE_SCALER = 0.3
TEMPERATURE_EXPONENT_FLOOR = 0.005


def temperature_adjust(value, temperature):
    exponent = (1 - temperature) / TEMPERATURE_SCALER + TEMPERATURE_EXPONENT_FLOOR
    return value**exponent


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
