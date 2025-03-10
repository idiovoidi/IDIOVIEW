"""Color definitions for the application"""

# Main color scheme
COLORS = {
    'primary': '#0078d4',      # Microsoft blue
    'secondary': '#666666',    # Dark gray
    'background': '#1e1e1e',   # Dark theme background
    'background_alt': '#2d2d2d',  # Alternative background color
    'text': '#ffffff',         # White text
    'accent': '#3a96dd',       # Light blue accent
    'warning': '#f9a825',      # Warning yellow
    'error': '#d32f2f',        # Error red
    'success': '#2e7d32',      # Success green
    'hover': '#2b88d8',        # Hover state blue
    'selected': '#0063b1',     # Selected state blue
    'border': '#424242',       # Border gray
}

# Rating colors for star display
RATING_COLORS = {
    1: '#f9a825',  # Bronze
    2: '#9e9e9e',  # Silver
    3: '#ffd700',  # Gold
    4: '#00c853',  # Emerald
    5: '#2196f3'   # Diamond
}

# Colors for prompt analysis
PROMPT_COLORS = {
    'artist': '#4caf50',
    'style': '#2196f3',
    'subject': '#9c27b0',
    'modifier': '#ff9800',
    'negative': '#f44336'
}

# Colors for parameter display
PARAM_COLORS = {
    'steps': '#3f51b5',
    'cfg': '#009688',
    'sampler': '#673ab7',
    'model': '#e91e63'
}

__all__ = ['COLORS', 'RATING_COLORS', 'PROMPT_COLORS', 'PARAM_COLORS'] 