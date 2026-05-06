class Colors:
    CLASS = "\033[94m"   # Blue
    FIELD = "\033[92m"   # Green
    VAR = "\033[96m"     # Cyan
    TYPE = "\033[93m"    # Yellow
    ATTR = "\033[95m"    # Magenta
    CODE = "\033[97m"    # White
    NONE = "\033[91m"    # Red
    END = "\033[0m"      # Reset

    @staticmethod
    def set_colors():
        Colors.CLASS = "\033[94m"
        Colors.FIELD = "\033[92m"
        Colors.VAR = "\033[96m"
        Colors.TYPE = "\033[93m"
        Colors.ATTR = "\033[95m"
        Colors.CODE = "\033[97m"
        Colors.NONE = "\033[91m"
        Colors.END = "\033[0m"

    @staticmethod
    def set_no_colors():
        Colors.CLASS = ""
        Colors.FIELD = ""
        Colors.VAR = ""
        Colors.TYPE = ""
        Colors.ATTR = ""
        Colors.CODE = ""
        Colors.NONE = ""
        Colors.END = ""