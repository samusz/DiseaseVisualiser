import pygame
import random
import numpy as np
import cProfile

from Visualiser.Node import Node
from DiseaseAlgorithm.DiseaseSpread import DiseaseSpread
from DiseaseAlgorithm.DiseaseManager import DiseaseManager

from Settings.VisualiserSettings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from Settings.VisualiserSettings import VIS_WINDOW_SIZE, VIS_NODE_WIDTH, NODE_SIZE, NODE_COUNT
from Settings.VisualiserSettings import MIN_ALGORITHM_CALL_STEP, TIMED_DAYS, ANIMATE_NODES
from Settings.VisualiserSettings import BG_COLOUR, GRID_BORDER_COLOUR, TIME_SCALE_ANIM
from Settings.AlgorithmSettings import DAY_LIMIT, STARTING_INFECTIONS


class Visualiser:

    pygame.init()
    pygame.font.init()
    pygame.display.set_caption('Disease Spread Visualiser')

    def __init__(self):
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.grid_surf = pygame.Surface((VIS_WINDOW_SIZE, VIS_WINDOW_SIZE))

        self.font = pygame.font.SysFont('Arial', 30)
        self.day_text = ''

        self.grid = np.array([Node() for _ in range(VIS_NODE_WIDTH ** 2)])
        self.grid_sorted = np.array([Node() for _ in range(VIS_NODE_WIDTH ** 2)])
        self.sort_toggle = False
        self.nodes_updated_since_draw = True

        self.disease_manager = DiseaseManager()
        self.spread = DiseaseSpread(self.disease_manager.diseases['COVID-19'])
        self.day_limit = DAY_LIMIT
        self.day = 0
        self.daily_stats = {}
        self.nodes = {
            'healthy': {'nodes': [], 'percentage': 0.00, 'excess': 0, 'needed': 0},
            'infected': {'nodes': [], 'percentage': 0.00, 'excess': 0, 'needed': 0},
            'recovered': {'nodes': [], 'percentage': 0.00, 'excess': 0, 'needed': 0},
            'dead': {'nodes': [], 'percentage': 0.00, 'excess': 0, 'needed': 0},

            'total': {'nodes': [], 'excess': []},
        }

        self.time_step = MIN_ALGORITHM_CALL_STEP   # 1000 = 1s
        self.time_count = pygame.time.get_ticks()

        self.animate_nodes = ANIMATE_NODES
        self.disease_algorithm_runtime = 0

        # PROFILING
        self.profiler = cProfile.Profile()


    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                self.profiler.disable()
                self.profiler.print_stats(sort='cumtime')
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    self.profiler.disable()
                    self.profiler.print_stats(sort='cumtime')
                if event.key == pygame.K_SPACE:
                    if self.sort_toggle:
                        np.random.shuffle(self.grid)
                    self.sort_toggle = not self.sort_toggle


    def run(self):
        self.profiler.enable()

        for i in range(STARTING_INFECTIONS):
            self.spread.population.people[i].infect()

        while self.day <= self.day_limit:
            self.clock.tick(FPS)
            self.events()

            if self.day_has_passed():
                if TIME_SCALE_ANIM and self.animate_nodes:
                    if self.day < TIMED_DAYS:
                        start = pygame.time.get_ticks()
                        self.daily_stats[self.day] = self.spread.pass_day(self.day)
                        runtime = pygame.time.get_ticks() - start

                        self.disease_algorithm_runtime = (self.disease_algorithm_runtime + runtime) // 2
                        self.update_node_animation_time()

                self.daily_stats[self.day] = self.spread.pass_day(self.day)

                # self.write_daily_stats_to_file()

                self.nodes_update()
                self.day += 1

            self.draw()


    def draw(self):
        self.screen.fill(BG_COLOUR)

        self.draw_grid()
        self.draw_UI()

        self.screen.blit(
            self.grid_surf,
            ((SCREEN_WIDTH // 2) - (self.grid_surf.get_width() // 2),
             (SCREEN_HEIGHT // 2) - (self.grid_surf.get_height() // 2))
        )

        self.nodes_updated_since_draw = False
        pygame.display.update()


    def draw_grid(self):
        node_index = 0

        if self.sort_toggle:
            if self.nodes_updated_since_draw:
                self.nodes_sort()

        for y in range(VIS_NODE_WIDTH):
            for x in range(VIS_NODE_WIDTH):

                if not self.sort_toggle:
                    node_surf = self.grid[node_index].draw()
                    self.grid_surf.blit(node_surf, (x * NODE_SIZE, y * NODE_SIZE))
                else:
                    node_surf = self.grid_sorted[node_index].draw(no_anim=True)
                    self.grid_surf.blit(node_surf, (x * NODE_SIZE, y * NODE_SIZE))

                node_index += 1


    def draw_UI(self):
        if self.nodes_updated_since_draw:
            self.day_text = self.font.render(f'Day: {self.day}', 1, (255, 255, 255))

        self.screen.blit(self.day_text, (SCREEN_WIDTH // 2 - self.day_text.get_width() // 2, 20))


    def day_has_passed(self):
        if pygame.time.get_ticks() > self.time_count + self.time_step:
            self.time_count = pygame.time.get_ticks()
            return True
        else:
            return False


    def nodes_update(self):
        self.nodes_tally()
        self.nodes_calc_visualiser_spread_diff()
        self.nodes_convert_excesses()
        self.nodes_updated_since_draw = True


    def nodes_tally(self):
        self.nodes = {
            'healthy': {'nodes': [], 'percentage': 0.00, 'excess': 0, 'needed': 0},
            'infected': {'nodes': [], 'percentage': 0.00, 'excess': 0, 'needed': 0},
            'recovered': {'nodes': [], 'percentage': 0.00, 'excess': 0, 'needed': 0},
            'dead': {'nodes': [], 'percentage': 0.00, 'excess': 0, 'needed': 0},

            'total': {'nodes': [], 'excess': []},
        }

        node_index = 0
        for y in range(VIS_NODE_WIDTH):
            for x in range(VIS_NODE_WIDTH):
                node = self.grid[node_index]
                if node.status == 0:
                    self.nodes['healthy']['nodes'].append(node)
                    self.nodes['total']['nodes'].append(node)
                if node.status in [1, 2]:
                    self.nodes['infected']['nodes'].append(node)
                    self.nodes['total']['nodes'].append(node)
                if node.status == 3:
                    self.nodes['recovered']['nodes'].append(node)
                    self.nodes['total']['nodes'].append(node)
                if node.status == 4:
                    self.nodes['dead']['nodes'].append(node)
                    self.nodes['total']['nodes'].append(node)

                node_index += 1

        self.nodes['healthy']['percentage'] = round((len(self.nodes['healthy']['nodes']) / len(self.nodes['total']['nodes']) * 100), 2)
        self.nodes['infected']['percentage'] = round((len(self.nodes['infected']['nodes']) / len(self.nodes['total']['nodes']) * 100), 2)
        self.nodes['recovered']['percentage'] = round((len(self.nodes['recovered']['nodes']) / len(self.nodes['total']['nodes']) * 100), 2)
        self.nodes['dead']['percentage'] = round((len(self.nodes['dead']['nodes']) / len(self.nodes['total']['nodes']) * 100), 2)


    def nodes_calc_visualiser_spread_diff(self):
        node_types = [
            ('healthy', 'healthy_percentage'),
            ('infected', 'infected_percentage'),
            ('recovered', 'recovered_percentage'),
            ('dead', 'dead_percentage')
        ]

        for node, percent in node_types:
            spread_percent = self.daily_stats[self.day][percent]
            excess_node_count = round((self.nodes[node]['percentage'] - spread_percent) / 100 * NODE_COUNT)

            if excess_node_count > 0:
                if not self.sort_toggle:
                    self.nodes['total']['excess'] += random.sample(self.nodes[node]['nodes'], excess_node_count)
                else:
                    self.nodes['total']['excess'] += self.nodes[node]['nodes'][:excess_node_count]
            elif excess_node_count < 0:
                self.nodes[node]['needed'] = round((spread_percent - self.nodes[node]['percentage']) / 100 * NODE_COUNT)


    def nodes_convert_excesses(self):
        for node in self.nodes['total']['excess']:
            if self.nodes['dead']['needed'] > 0:
                node.convert_dead()
                self.nodes['dead']['needed'] -= 1
                continue

            if self.nodes['recovered']['needed'] > 0:
                node.convert_recovered()
                self.nodes['recovered']['needed'] -= 1
                continue

            if self.nodes['infected']['needed'] > 0:
                node.convert_infected()
                self.nodes['infected']['needed'] -= 1
                continue

            if self.nodes['healthy']['needed'] > 0:
                node.convert_healthy()
                self.nodes['healthy']['needed'] -= 1
                continue


    def nodes_sort(self):
        self.grid_sorted = np.array(sorted(self.grid, reverse=True))


    def write_daily_stats_to_file(self):
        with open(f'./daily_stats.txt', mode='w') as f:
            for key, value in self.daily_stats.items():
                f.write(f'-----------------------------\n')
                f.write(f'Day: {key}\n')

                for k, v in value.items():
                    f.write(f'{k} - {v}\n')

                f.write('\n')


    def update_node_animation_time(self, time=0):
        for node in self.grid:
            node.colour_shift_max_step = 255 * FPS // (self.disease_algorithm_runtime + self.time_step) // 5
            # node.colour_shift_max_step = 5