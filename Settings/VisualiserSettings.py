from Settings.AlgorithmSettings import POPULATION_SIZE

SCREEN_WIDTH = 950
SCREEN_HEIGHT = 950

FPS = 60
VISUALISER_NODE_WIDTH = 50
VISUALISER_WINDOW_SIZE = 800
NODE_COUNT = VISUALISER_NODE_WIDTH * VISUALISER_NODE_WIDTH
NODE_SIZE = VISUALISER_WINDOW_SIZE // VISUALISER_NODE_WIDTH

# Colours
BG_COLOUR = (80, 80, 80)
GRID_COLOUR = (150, 150, 150)
GRID_BORDER_COLOUR = (200, 200, 200)

HEALTHY = (0, 255, 0)
INFECTED_UNKNOWN = (255, 0, 0)
INFECTED_KNOWN = (255, 100, 100)
RECOVERED = (255, 255, 0)
DEAD = (0, 0, 0)