from color import Color
import random
import time


def print_all_colors():
    """
    Prints all colors from the Color class, using their own color and background.
    """
    # Get all color attributes from the Color class
    color_attrs = [
        attr
        for attr in dir(Color)
        if not callable(getattr(Color, attr)) and not attr.startswith("__")
    ]

    # Filter out only the colors (not backgrounds or ENDC)
    colors = [
        attr for attr in color_attrs if not attr.startswith("BG_") and attr != "ENDC"
    ]

    # Print each color with its own color and background
    for color in colors:
        # Get the color code
        color_code = getattr(Color, color)

        # Print the color name in its own color
        print(f"{color_code}{color}{Color.ENDC}")

        # Check if there's a corresponding background color
        bg_color = f"BG_{color}"
        if hasattr(Color, bg_color):
            bg_color_code = getattr(Color, bg_color)
            print(f"{bg_color_code}{color} with {bg_color}{Color.ENDC}")

        print()  # Add a blank line for separation
        time.sleep(1)  # Pause for 1 second between colors


def print_random_combinations():
    """
    Prints 35 random combinations of color and background.
    """
    # Get all color and background attributes from the Color class
    color_attrs = [
        attr
        for attr in dir(Color)
        if not callable(getattr(Color, attr)) and not attr.startswith("__")
    ]

    # Filter out only the colors and backgrounds
    colors = [
        attr for attr in color_attrs if not attr.startswith("BG_") and attr != "ENDC"
    ]
    backgrounds = [attr for attr in color_attrs if attr.startswith("BG_")]

    # Print 35 random combinations
    for _ in range(35):
        # Randomly select a color and background
        color = random.choice(colors)
        bg_color = random.choice(backgrounds)

        # Get the color and background codes
        color_code = getattr(Color, color)
        bg_color_code = getattr(Color, bg_color)

        # Print the combination
        print(f"{bg_color_code}{color_code}{color} with {bg_color}{Color.ENDC}")
        time.sleep(1)  # Pause for 1 second between combinations


if __name__ == "__main__":
    print("Printing all colors one by one with their backgrounds...\n")
    print_all_colors()

    print("\nPrinting 35 random color and background combinations...\n")
    print_random_combinations()
