def calculate_average(numbers):
    # Handle None and non-iterable inputs
    if numbers is None or not hasattr(numbers, '__iter__'):
        return 0

    # Convert to list to safely check length
    numbers_list = list(numbers)

    if not numbers_list:
        return 0

    total = 0
    for num in numbers_list:
        # Skip non-numeric values to prevent crashes
        if not isinstance(num, (int, float)) or isinstance(num, bool):
            continue
        total += num

    # Avoid division by zero if all values were non-numeric
    if len(numbers_list) == 0:
        return 0

    return total / len(numbers_list)


def get_user_name(user):
    if user is None or not isinstance(user, dict) or "name" not in user:
        return ""
    name = user["name"]
    if name is None or not isinstance(name, str):
        return ""
    return name.upper()