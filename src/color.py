class Color:
    """ANSI escape codes for terminal colors"""
    # Normal colors
    BLACK        = '\033[30m' # Black
    RED          = '\033[31m' # Red
    GREEN        = '\033[32m' # Green
    YELLOW       = '\033[33m' # Yellow
    BLUE         = '\033[34m' # Blue
    CYAN         = '\033[36m' # Cyan
    WHITE        = '\033[37m' # White
    PURPLE       = '\033[35m' # Purple

    # Bright colors
    BRIGHTBLACK  = '\033[90m' # Bright black
    BRIGHTRED    = '\033[91m' # Bright red
    BRIGHTGREEN  = '\033[92m' # Bright green
    BRIGHTYELLOW = '\033[93m' # Bright yellow
    BRIGHTBLUE   = '\033[94m' # Bright blue
    BRIGHTCYAN   = '\033[96m' # Bright cyan
    BRIGHTWHITE  = '\033[97m' # Bright white
    BRIGHTPURPLE = '\033[95m' # Bright purple

    # Dark colors
    DARKRED      = '\033[31;2m' # Dark red
    DARKGREEN    = '\033[32;2m' # Dark green
    DARKYELLOW   = '\033[33;2m' # Dark yellow
    DARKBLUE     = '\033[34;2m' # Dark blue
    DARKCYAN     = '\033[36;2m' # Dark cyan
    DARKPURPLE   = '\033[35;2m' # Dark purple

    # Light colors
    LIGHTRED     = '\033[91;1m' # Light red
    LIGHTGREEN   = '\033[92;1m' # Light green
    LIGHTYELLOW  = '\033[93;1m' # Light yellow
    LIGHTBLUE    = '\033[94;1m' # Light blue
    LIGHTCYAN    = '\033[96;1m' # Light cyan
    LIGHTPURPLE  = '\033[95;1m' # Light purple

    # Pastel colors
    PASTELPINK   = '\033[95m'   # Pastel pink
    PASTELBLUE   = '\033[94m'   # Pastel blue
    PASTELGREEN  = '\033[92m'   # Pastel green
    PASTELYELLOW = '\033[93m'   # Pastel yellow
    PASTELPURPLE = '\033[95;1m' # Pastel purple

    # End of color
    ENDC        = '\033[0m'     # End of color
