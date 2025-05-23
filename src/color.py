class Color:
    """ANSI escape codes for terminal colors and backgrounds"""

    # Normal colors
    BLACK = "\033[30m"  # Black
    RED = "\033[31m"  # Red
    GREEN = "\033[32m"  # Green
    YELLOW = "\033[33m"  # Yellow
    BLUE = "\033[34m"  # Blue
    CYAN = "\033[36m"  # Cyan
    WHITE = "\033[37m"  # White
    PURPLE = "\033[35m"  # Purple

    # Bright colors
    BRIGHTBLACK = "\033[90m"  # Bright black
    BRIGHTRED = "\033[91m"  # Bright red
    BRIGHTGREEN = "\033[92m"  # Bright green
    BRIGHTYELLOW = "\033[93m"  # Bright yellow
    BRIGHTBLUE = "\033[94m"  # Bright blue
    BRIGHTCYAN = "\033[96m"  # Bright cyan
    BRIGHTWHITE = "\033[97m"  # Bright white
    BRIGHTPURPLE = "\033[95m"  # Bright purple

    # Dark colors
    DARKRED = "\033[31;2m"  # Dark red
    DARKGREEN = "\033[32;2m"  # Dark green
    DARKYELLOW = "\033[33;2m"  # Dark yellow
    DARKBLUE = "\033[34;2m"  # Dark blue
    DARKCYAN = "\033[36;2m"  # Dark cyan
    DARKPURPLE = "\033[35;2m"  # Dark purple

    # Light colors
    LIGHTRED = "\033[91;1m"  # Light red
    LIGHTGREEN = "\033[92;1m"  # Light green
    LIGHTYELLOW = "\033[93;1m"  # Light yellow
    LIGHTBLUE = "\033[94;1m"  # Light blue
    LIGHTCYAN = "\033[96;1m"  # Light cyan
    LIGHTPURPLE = "\033[95;1m"  # Light purple

    # Pastel colors
    PASTELPINK = "\033[95m"  # Pastel pink
    PASTELBLUE = "\033[94m"  # Pastel blue
    PASTELGREEN = "\033[92m"  # Pastel green
    PASTELYELLOW = "\033[93m"  # Pastel yellow
    PASTELPURPLE = "\033[95;1m"  # Pastel purple

    # Additional colors
    ORANGE = "\033[38;5;208m"  # Orange
    MAGENTA = "\033[35m"  # Magenta
    TEAL = "\033[38;5;6m"  # Teal
    LAVENDER = "\033[38;5;183m"  # Lavender
    CORAL = "\033[38;5;209m"  # Coral
    GOLD = "\033[38;5;220m"  # Gold
    SILVER = "\033[38;5;7m"  # Silver
    MAROON = "\033[38;5;1m"  # Maroon
    OLIVE = "\033[38;5;3m"  # Olive
    NAVY = "\033[38;5;4m"  # Navy
    INDIGO = "\033[38;5;54m"  # Indigo
    TURQUOISE = "\033[38;5;45m"  # Turquoise
    SALMON = "\033[38;5;203m"  # Salmon
    PEACH = "\033[38;5;223m"  # Peach
    MINT = "\033[38;5;121m"  # Mint
    LILAC = "\033[38;5;183m"  # Lilac
    MUSTARD = "\033[38;5;142m"  # Mustard
    BURGUNDY = "\033[38;5;88m"  # Burgundy
    SKYBLUE = "\033[38;5;117m"  # Sky blue
    FORESTGREEN = "\033[38;5;28m"  # Forest green
    CHOCOLATE = "\033[38;5;130m"  # Chocolate
    PLUM = "\033[38;5;96m"  # Plum
    BEIGE = "\033[38;5;230m"  # Beige
    CRIMSON = "\033[38;5;160m"  # Crimson
    LIME = "\033[38;5;118m"  # Lime
    AQUA = "\033[38;5;51m"  # Aqua
    VIOLET = "\033[38;5;93m"  # Violet
    TAN = "\033[38;5;180m"  # Tan
    ROSE = "\033[38;5;207m"  # Rose
    EMERALD = "\033[38;5;46m"  # Emerald
    RUBY = "\033[38;5;124m"  # Ruby
    SAPPHIRE = "\033[38;5;21m"  # Sapphire
    AMBER = "\033[38;5;214m"  # Amber
    COBALT = "\033[38;5;26m"  # Cobalt
    LEMON = "\033[38;5;226m"  # Lemon
    GRAPE = "\033[38;5;55m"  # Grape
    PEARL = "\033[38;5;231m"  # Pearl
    CHARCOAL = "\033[38;5;238m"  # Charcoal
    SLATE = "\033[38;5;240m"  # Slate
    SNOW = "\033[38;5;255m"  # Snow
    MIDNIGHT = "\033[38;5;17m"  # Midnight
    CREAM = "\033[38;5;230m"  # Cream
    BRONZE = "\033[38;5;130m"  # Bronze
    COPPER = "\033[38;5;130m"  # Copper
    STEEL = "\033[38;5;67m"  # Steel
    LAVABLUE = "\033[38;5;27m"  # Lava blue
    SUNSET = "\033[38;5;209m"  # Sunset
    OCEAN = "\033[38;5;27m"  # Ocean
    CLOUD = "\033[38;5;255m"  # Cloud
    FIRE = "\033[38;5;196m"  # Fire
    ICE = "\033[38;5;45m"  # Ice
    EARTH = "\033[38;5;94m"  # Earth
    WINE = "\033[38;5;88m"  # Wine
    HONEY = "\033[38;5;220m"  # Honey
    LAVENDERBLUE = "\033[38;5;183m"  # Lavender blue
    DUSTYROSE = "\033[38;5;174m"  # Dusty rose
    MOSS = "\033[38;5;64m"  # Moss
    SAND = "\033[38;5;180m"  # Sand
    STORM = "\033[38;5;67m"  # Storm
    TWILIGHT = "\033[38;5;54m"  # Twilight
    SUNFLOWER = "\033[38;5;220m"  # Sunflower
    LAGOON = "\033[38;5;45m"  # Lagoon
    MAUVE = "\033[38;5;183m"  # Mauve
    PEAR = "\033[38;5;118m"  # Pear
    RUST = "\033[38;5;130m"  # Rust
    FROST = "\033[38;5;45m"  # Frost
    ASH = "\033[38;5;240m"  # Ash
    GLACIER = "\033[38;5;45m"  # Glacier
    DUSK = "\033[38;5;54m"  # Dusk
    DAWN = "\033[38;5;223m"  # Dawn
    MOONLIGHT = "\033[38;5;255m"  # Moonlight
    SUNRISE = "\033[38;5;209m"  # Sunrise
    CANDY = "\033[38;5;207m"  # Candy
    LAVA = "\033[38;5;196m"  # Lava
    FOG = "\033[38;5;255m"  # Fog
    SHADOW = "\033[38;5;238m"  # Shadow
    LIGHTNING = "\033[38;5;226m"  # Lightning
    THUNDER = "\033[38;5;238m"  # Thunder
    RAIN = "\033[38;5;45m"  # Rain
    MIST = "\033[38;5;255m"  # Mist
    FROSTED = "\033[38;5;45m"  # Frosted
    DARKNESS = "\033[38;5;232m"  # Darkness
    LIGHT = "\033[38;5;255m"  # Light
    MOON = "\033[38;5;255m"  # Moon
    SUN = "\033[38;5;226m"  # Sun
    STARLIGHT = "\033[38;5;255m"  # Starlight
    GALAXY = "\033[38;5;54m"  # Galaxy
    AURORA = "\033[38;5;45m"  # Aurora
    COMET = "\033[38;5;255m"  # Comet
    METEOR = "\033[38;5;196m"  # Meteor
    NEBULA = "\033[38;5;54m"  # Nebula
    VOID = "\033[38;5;232m"  # Void
    COSMIC = "\033[38;5;54m"  # Cosmic
    INFINITY = "\033[38;5;45m"  # Infinity
    ETERNITY = "\033[38;5;255m"  # Eternity
    UNIVERSE = "\033[38;5;54m"  # Universe
    SPACE = "\033[38;5;232m"  # Space
    TIME = "\033[38;5;255m"  # Time
    DREAM = "\033[38;5;183m"  # Dream
    NIGHT = "\033[38;5;17m"  # Night
    DAY = "\033[38;5;226m"  # Day
    TWILIGHT = "\033[38;5;54m"  # Twilight
    DAWN = "\033[38;5;223m"  # Dawn
    DUSK = "\033[38;5;54m"  # Dusk
    SUNSET = "\033[38;5;209m"  # Sunset
    SUNRISE = "\033[38;5;209m"  # Sunrise
    MOONLIGHT = "\033[38;5;255m"  # Moonlight
    STARLIGHT = "\033[38;5;255m"  # Starlight
    GALAXY = "\033[38;5;54m"  # Galaxy
    AURORA = "\033[38;5;45m"  # Aurora
    COMET = "\033[38;5;255m"  # Comet
    METEOR = "\033[38;5;196m"  # Meteor
    NEBULA = "\033[38;5;54m"  # Nebula
    VOID = "\033[38;5;232m"  # Void
    COSMIC = "\033[38;5;54m"  # Cosmic
    INFINITY = "\033[38;5;45m"  # Infinity
    ETERNITY = "\033[38;5;255m"  # Eternity
    UNIVERSE = "\033[38;5;54m"  # Universe
    SPACE = "\033[38;5;232m"  # Space
    TIME = "\033[38;5;255m"  # Time
    DREAM = "\033[38;5;183m"  # Dream
    NIGHT = "\033[38;5;17m"  # Night
    DAY = "\033[38;5;226m"  # Day

    # Background colors
    BG_BLACK = "\033[40m"  # Black background
    BG_RED = "\033[41m"  # Red background
    BG_GREEN = "\033[42m"  # Green background
    BG_YELLOW = "\033[43m"  # Yellow background
    BG_BLUE = "\033[44m"  # Blue background
    BG_CYAN = "\033[46m"  # Cyan background
    BG_WHITE = "\033[47m"  # White background
    BG_PURPLE = "\033[45m"  # Purple background
    BG_BRIGHTBLACK = "\033[100m"  # Bright black background
    BG_BRIGHTRED = "\033[101m"  # Bright red background
    BG_BRIGHTGREEN = "\033[102m"  # Bright green background
    BG_BRIGHTYELLOW = "\033[103m"  # Bright yellow background
    BG_BRIGHTBLUE = "\033[104m"  # Bright blue background
    BG_BRIGHTCYAN = "\033[106m"  # Bright cyan background
    BG_BRIGHTWHITE = "\033[107m"  # Bright white background
    BG_BRIGHTPURPLE = "\033[105m"  # Bright purple background
    BG_ORANGE = "\033[48;5;208m"  # Orange background
    BG_MAGENTA = "\033[48;5;201m"  # Magenta background
    BG_TEAL = "\033[48;5;6m"  # Teal background
    BG_LAVENDER = "\033[48;5;183m"  # Lavender background
    BG_CORAL = "\033[48;5;209m"  # Coral background
    BG_GOLD = "\033[48;5;220m"  # Gold background
    BG_SILVER = "\033[48;5;7m"  # Silver background
    BG_MAROON = "\033[48;5;1m"  # Maroon background
    BG_OLIVE = "\033[48;5;3m"  # Olive background
    BG_NAVY = "\033[48;5;4m"  # Navy background
    BG_INDIGO = "\033[48;5;54m"  # Indigo background
    BG_TURQUOISE = "\033[48;5;45m"  # Turquoise background
    BG_SALMON = "\033[48;5;203m"  # Salmon background
    BG_PEACH = "\033[48;5;223m"  # Peach background
    BG_MINT = "\033[48;5;121m"  # Mint background
    BG_LILAC = "\033[48;5;183m"  # Lilac background
    BG_MUSTARD = "\033[48;5;142m"  # Mustard background
    BG_BURGUNDY = "\033[48;5;88m"  # Burgundy background
    BG_SKYBLUE = "\033[48;5;117m"  # Sky blue background
    BG_FORESTGREEN = "\033[48;5;28m"  # Forest green background
    BG_CHOCOLATE = "\033[48;5;130m"  # Chocolate background
    BG_PLUM = "\033[48;5;96m"  # Plum background
    BG_BEIGE = "\033[48;5;230m"  # Beige background
    BG_CRIMSON = "\033[48;5;160m"  # Crimson background
    BG_LIME = "\033[48;5;118m"  # Lime background
    BG_AQUA = "\033[48;5;51m"  # Aqua background
    BG_VIOLET = "\033[48;5;93m"  # Violet background
    BG_TAN = "\033[48;5;180m"  # Tan background
    BG_ROSE = "\033[48;5;207m"  # Rose background
    BG_EMERALD = "\033[48;5;46m"  # Emerald background
    BG_RUBY = "\033[48;5;124m"  # Ruby background
    BG_SAPPHIRE = "\033[48;5;21m"  # Sapphire background
    BG_AMBER = "\033[48;5;214m"  # Amber background
    BG_COBALT = "\033[48;5;26m"  # Cobalt background
    BG_LEMON = "\033[48;5;226m"  # Lemon background
    BG_GRAPE = "\033[48;5;55m"  # Grape background
    BG_PEARL = "\033[48;5;231m"  # Pearl background
    BG_CHARCOAL = "\033[48;5;238m"  # Charcoal background
    BG_SLATE = "\033[48;5;240m"  # Slate background
    BG_SNOW = "\033[48;5;255m"  # Snow background
    BG_MIDNIGHT = "\033[48;5;17m"  # Midnight background
    BG_CREAM = "\033[48;5;230m"  # Cream background
    BG_BRONZE = "\033[48;5;130m"  # Bronze background
    BG_COPPER = "\033[48;5;130m"  # Copper background
    BG_STEEL = "\033[48;5;67m"  # Steel background
    BG_LAVABLUE = "\033[48;5;27m"  # Lava blue background
    BG_SUNSET = "\033[48;5;209m"  # Sunset background
    BG_OCEAN = "\033[48;5;27m"  # Ocean background
    BG_CLOUD = "\033[48;5;255m"  # Cloud background
    BG_FIRE = "\033[48;5;196m"  # Fire background
    BG_ICE = "\033[48;5;45m"  # Ice background
    BG_EARTH = "\033[48;5;94m"  # Earth background
    BG_WINE = "\033[48;5;88m"  # Wine background
    BG_HONEY = "\033[48;5;220m"  # Honey background
    BG_LAVENDERBLUE = "\033[48;5;183m"  # Lavender blue background
    BG_DUSTYROSE = "\033[48;5;174m"  # Dusty rose background
    BG_MOSS = "\033[48;5;64m"  # Moss background
    BG_SAND = "\033[48;5;180m"  # Sand background
    BG_STORM = "\033[48;5;67m"  # Storm background
    BG_TWILIGHT = "\033[48;5;54m"  # Twilight background
    BG_SUNFLOWER = "\033[48;5;220m"  # Sunflower background
    BG_LAGOON = "\033[48;5;45m"  # Lagoon background
    BG_MAUVE = "\033[48;5;183m"  # Mauve background
    BG_PEAR = "\033[48;5;118m"  # Pear background
    BG_RUST = "\033[48;5;130m"  # Rust background
    BG_FROST = "\033[48;5;45m"  # Frost background
    BG_ASH = "\033[48;5;240m"  # Ash background
    BG_GLACIER = "\033[48;5;45m"  # Glacier background
    BG_DUSK = "\033[48;5;54m"  # Dusk background
    BG_DAWN = "\033[48;5;223m"  # Dawn background
    BG_MOONLIGHT = "\033[48;5;255m"  # Moonlight background
    BG_SUNRISE = "\033[48;5;209m"  # Sunrise background
    BG_CANDY = "\033[48;5;207m"  # Candy background
    BG_LAVA = "\033[48;5;196m"  # Lava background
    BG_FOG = "\033[48;5;255m"  # Fog background
    BG_SHADOW = "\033[48;5;238m"  # Shadow background
    BG_LIGHTNING = "\033[48;5;226m"  # Lightning background
    BG_THUNDER = "\033[48;5;238m"  # Thunder background
    BG_RAIN = "\033[48;5;45m"  # Rain background
    BG_MIST = "\033[48;5;255m"  # Mist background
    BG_FROSTED = "\033[48;5;45m"  # Frosted background
    BG_DARKNESS = "\033[48;5;232m"  # Darkness background
    BG_LIGHT = "\033[48;5;255m"  # Light background
    BG_MOON = "\033[48;5;255m"  # Moon background
    BG_SUN = "\033[48;5;226m"  # Sun background
    BG_STARLIGHT = "\033[48;5;255m"  # Starlight background
    BG_GALAXY = "\033[48;5;54m"  # Galaxy background
    BG_AURORA = "\033[48;5;45m"  # Aurora background
    BG_COMET = "\033[48;5;255m"  # Comet background
    BG_METEOR = "\033[48;5;196m"  # Meteor background
    BG_NEBULA = "\033[48;5;54m"  # Nebula background
    BG_VOID = "\033[48;5;232m"  # Void background
    BG_COSMIC = "\033[48;5;54m"  # Cosmic background
    BG_INFINITY = "\033[48;5;45m"  # Infinity background
    BG_ETERNITY = "\033[48;5;255m"  # Eternity background
    BG_UNIVERSE = "\033[48;5;54m"  # Universe background
    BG_SPACE = "\033[48;5;232m"  # Space background
    BG_TIME = "\033[48;5;255m"  # Time background
    BG_DREAM = "\033[48;5;183m"  # Dream background
    BG_NIGHT = "\033[48;5;17m"  # Night background
    BG_DAY = "\033[48;5;226m"  # Day background
    BG_TWILIGHT = "\033[48;5;54m"  # Twilight background
    BG_DAWN = "\033[48;5;223m"  # Dawn background
    BG_DUSK = "\033[48;5;54m"  # Dusk background
    BG_SUNSET = "\033[48;5;209m"  # Sunset background
    BG_SUNRISE = "\033[48;5;209m"  # Sunrise background
    BG_MOONLIGHT = "\033[48;5;255m"  # Moonlight background
    BG_STARLIGHT = "\033[48;5;255m"  # Starlight background
    BG_GALAXY = "\033[48;5;54m"  # Galaxy background
    BG_AURORA = "\033[48;5;45m"  # Aurora background
    BG_COMET = "\033[48;5;255m"  # Comet background
    BG_METEOR = "\033[48;5;196m"  # Meteor background
    BG_NEBULA = "\033[48;5;54m"  # Nebula background
    BG_VOID = "\033[48;5;232m"  # Void background
    BG_COSMIC = "\033[48;5;54m"  # Cosmic background
    BG_INFINITY = "\033[48;5;45m"  # Infinity background
    BG_ETERNITY = "\033[48;5;255m"  # Eternity background
    BG_UNIVERSE = "\033[48;5;54m"  # Universe background
    BG_SPACE = "\033[48;5;232m"  # Space background
    BG_TIME = "\033[48;5;255m"  # Time background
    BG_DREAM = "\033[48;5;183m"  # Dream background
    BG_NIGHT = "\033[48;5;17m"  # Night background
    BG_DAY = "\033[48;5;226m"  # Day background

    # End of color
    ENDC = "\033[0m"  # End of color
