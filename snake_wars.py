import arcade
import random
import os
import pickle
import matplotlib.pyplot as plt


SPRITE_SIZE = 32
screen_width, screen_height = arcade.get_display_size()

MAP_WIDTH = screen_width // SPRITE_SIZE
MAP_HEIGHT = screen_height // SPRITE_SIZE

MAP_WIDTH = 30
MAP_HEIGHT = 25
def generate_map(width, height):
    map_data = ["x" * width]
    for _ in range(height - 2):
        map_data.append("x" + "." * (width - 2) + "x")
    map_data.append("x" * width)
    return "\n".join(map_data)


REWARD_FOOD = 100
REWARD_SURVIVAL = -1
REWARD_BOMB = -100

REWARD_KILL = 1000
REWARD_DIE = -1000

ACTION_UP = 'U'
ACTION_DOWN = 'D'
ACTION_LEFT = 'L'
ACTION_RIGHT = 'R'
ACTIONS = [ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT]

MOVES = {
    ACTION_UP: (-1, 0),
    ACTION_DOWN: (1, 0),
    ACTION_LEFT: (0, -1),
    ACTION_RIGHT: (0, 1)
}

FILE_AGENT = 'snake.qtable'

def arg_max(table):
    if not table:
        return random.choice(ACTIONS)
    return max(table, key=table.get)

class QTable:
    def __init__(self, learning_rate=0.9, discount_factor=0.95, epsilon=0.5):
        self.table = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon

    def update_epsilon(self, decay_rate=0.995, min_epsilon=0.1):
        self.epsilon = max(min_epsilon, self.epsilon * decay_rate)


    def set(self, state, action, reward, new_state):
        state = tuple(state)
        new_state = tuple(new_state)

        if state not in self.table:
            self.table[state] = {action: 0 for action in ACTIONS}
        if new_state not in self.table:
            self.table[new_state] = {action: 0 for action in ACTIONS}

        max_future_q = max(self.table[new_state].values(), default=0)
        self.table[state][action] += self.learning_rate * (reward + self.discount_factor * max_future_q - self.table[state][action])
        #print(f"État : {state}, Action : {action}, Valeur Q mise à jour : {self.table[state][action]}")

    def best_action(self, state):
        if random.random() < self.epsilon:
            return random.choice(ACTIONS)
        else:
            if state in self.table and self.table[state]:
                action = arg_max(self.table[state])
            else:
                action = random.choice(ACTIONS)
        return action

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.table, file)

    def load(self, filename):
        with open(filename, 'rb') as file:
            self.table = pickle.load(file)

class Snake:
    def __init__(self, start_position, qtable):
        self.body = [start_position]
        self.grow = False
        self.qtable = qtable
        self.total_reward = 0

    def decide_action(self, state):
        return self.qtable.best_action(state)

    def update_qtable(self, state, action, reward, new_state):
        self.qtable.set(state, action, reward, new_state)

    def move(self, new_head):
        if self.grow:
            self.body = [new_head] + self.body
            self.grow = False
        else:
            self.body = [new_head] + self.body[:-1]

    def reduce_body(self, percentage):
        if len(self.body) > 1:
            segments_to_keep = max(1, int(len(self.body) * (1 - percentage)))
            self.body = self.body[:segments_to_keep]

class ScriptedSnake:
    def __init__(self, start_position):
        self.body = [start_position]
        self.grow = False

    def decide_action(self, env):

        head = self.body[0]

        closest_food = min(
            env.food_positions,
            key=lambda food: abs(food[0] - head[0]) + abs(food[1] - head[1]),
            default=None
        )

        safe_actions = []
        for action, (dx, dy) in MOVES.items():
            next_position = (head[0] + dx, head[1] + dy)

            if next_position in env.walls or next_position in env.bomb_positions:
                continue
            if closest_food and next_position == closest_food:
                return action
            safe_actions.append(action)

        return random.choice(safe_actions) if safe_actions else random.choice(ACTIONS)

    def move(self, new_head):
        if self.grow:
            self.body = [new_head] + self.body
            self.grow = False
        else:
            self.body = [new_head] + self.body[:-1]

    def reduce_body(self, percentage):
        if len(self.body) > 1:
            segments_to_keep = max(1, int(len(self.body) * (1 - percentage)))
            self.body = self.body[:segments_to_keep]

class Environment:
    def __init__(self, map_text):
        self.map = [list(row) for row in map_text.strip().split('\n')]
        self.height = len(self.map)
        self.width = len(self.map[0])
        self.walls = self.create_walls()
        self.food_positions = self.place_food(30)
        self.bomb_positions = self.place_bombs(10)

    def create_walls(self):
        walls = []
        for row_idx, row in enumerate(self.map):
            for col_idx, cell in enumerate(row):
                if cell == 'x':
                    walls.append((row_idx, col_idx))
        return walls

    def place_food(self, num_food):
        return self.place_items(num_food, exclude=self.walls)

    def place_bombs(self, num_bombs):
        return self.place_items(num_bombs, exclude=self.walls + self.food_positions)

    def place_items(self, num_items, exclude):
        positions = []
        empty_spaces = [
            (row_idx, col_idx)
            for row_idx, row in enumerate(self.map)
            for col_idx, cell in enumerate(row)
            if cell == '.' and (row_idx, col_idx) not in exclude
        ]
        while len(positions) < num_items and empty_spaces:
            pos = random.choice(empty_spaces)
            positions.append(pos)
            empty_spaces.remove(pos)
        return positions

    def get_game_state(self):
        return {
            "walls": self.walls,
            "food": self.food_positions,
            "bombs": self.bomb_positions,
        }
    '''
    def get_extended_radar(self, head, scripted_positions):
        directions = {
            "UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1),
            "UP_LEFT": (-1, -1), "UP_RIGHT": (-1, 1), "DOWN_LEFT": (1, -1), "DOWN_RIGHT": (1, 1),
        }
        radar = {}

        # Set pour vérification rapide
        scripted_positions_set = set(scripted_positions)

        for direction, (dx, dy) in directions.items():
            x, y = head
            radar[direction] = []
            for step in range(1, 6):
                x += dx
                y += dy
                position = (x, y)
                if position in scripted_positions_set:
                    radar[direction].append("SNAKE")
                    break
                elif position in self.walls:
                    radar[direction].append("WALL")
                    break
                elif position in self.food_positions:
                    radar[direction].append("FOOD")
                    break
                elif position in self.bomb_positions:
                    radar[direction].append("BOMB")
                    break
                elif x < 0 or x >= self.height or y < 0 or y >= self.width:
                    radar[direction].append("WALL")
                    break
                else:
                    radar[direction].append("EMPTY")

        return {dir: signals[0] if signals else "EMPTY" for dir, signals in radar.items()}

    '''
    #Affiché le radar à l'écran
    def get_radar(self, head):
        directions = {
            ACTION_UP: (-1, 0),
            ACTION_DOWN: (1, 0),
            ACTION_LEFT: (0, -1),
            ACTION_RIGHT: (0, 1),
        }

        radar = {}
        for action, (dx, dy) in directions.items():
            x, y = head
            for _ in range(3): 
                x += dx
                y += dy
                if x < 0 or x >= self.height or y < 0 or y >= self.width or (x, y) in self.walls:
                    radar[action] = 'WALL'
                    break
                elif (x, y) in self.food_positions:
                    radar[action] = 'FOOD'
                    break
                elif (x, y) in self.bomb_positions:
                    radar[action] = 'BOMB'
                    break
                else:
                    radar[action] = 'EMPTY'
        print(radar)
        return radar
    '''
    def get_immediate_neighbors(self, head):
        neighbors = {}
        directions = {
            "UP": (-1, 0),
            "DOWN": (1, 0),
            "LEFT": (0, -1),
            "RIGHT": (0, 1),
            "UP_LEFT": (-1, -1),
            "UP_RIGHT": (-1, 1),
            "DOWN_LEFT": (1, -1),
            "DOWN_RIGHT": (1, 1),
        }

        for direction, (dx, dy) in directions.items():
            x, y = head[0] + dx, head[1] + dy

            if x < 0 or x >= self.height or y < 0 or y >= self.width:
                neighbors[direction] = "WALL"
            elif (x, y) in self.walls:
                neighbors[direction] = "WALL"
            elif (x, y) in self.food_positions:
                neighbors[direction] = "FOOD"
            elif (x, y) in self.bomb_positions:
                neighbors[direction] = "BOMB"
            else:
                neighbors[direction] = "EMPTY"

        return neighbors
    '''
    def move(self, snake, action):
        move = MOVES[action]
        new_head = (snake.body[0][0] + move[0], snake.body[0][1] + move[1])

        if new_head[0] < 0 or new_head[0] >= self.height or new_head[1] < 0 or new_head[1] >= self.width:
            return snake.body[0], 0

        if new_head in self.walls:
            return snake.body[0], 0

        if new_head in self.bomb_positions:
            snake.reduce_body(0.5)
            return new_head, REWARD_BOMB

        if new_head in self.food_positions:
            self.food_positions.remove(new_head)
            self.food_positions.append(self.place_food(1)[0])
            snake.grow = True
            return new_head, REWARD_FOOD

        return new_head, REWARD_SURVIVAL
class SnakeGame(arcade.Window):
    def __init__(self, width, height, snake, env, agent):
        calculated_width = MAP_WIDTH * SPRITE_SIZE
        calculated_height = MAP_HEIGHT * SPRITE_SIZE + 70
        super().__init__(calculated_width, calculated_height, "Snake Game", fullscreen=False)
        self.env = env
        self.snake = snake
        self.agent = agent
        arcade.set_background_color(arcade.color.BLACK)

        self.total_reward = 0
        self.episode_history = []
        self.current_episode_score = 0
        self.turn_count = 0

        self.wall_sprites = None
        self.food_sprites = None
        self.snake_sprites = arcade.SpriteList()

        self.snake_head_sprite = arcade.Sprite("assets/snake_head.png", scale=1)

        self.scripted_snake = ScriptedSnake(start_position=(env.height - 2, env.width - 2))
        self.scripted_snake_sprites = arcade.SpriteList()
        self.scripted_snake_head_sprite = arcade.Sprite("assets/snake_head_brown.png", scale=1)

        self.time_since_last_move = 0
        self.snake_move_interval = 0.001
        self.snake_direction = ACTION_RIGHT
        self.pending_direction = self.snake_direction

        self.manual_control = False
        self.save_counter = 0

    def do(self):
        head_position = self.snake.body[0]
        #scripted_positions = self.scripted_snake.body
        radar = self.env.get_radar(head_position)

        state = (
            head_position,
            tuple(radar.values()),
        )

        if self.manual_control:
            self.snake_direction = self.pending_direction
        else:
            self.snake_direction = self.agent.best_action(state)

        new_head, reward = self.env.move(self.snake, self.snake_direction)
        #scripted_positions = self.scripted_snake.body
        new_radar = self.env.get_radar(new_head)

        collision_reward = self.check_collision()
        if collision_reward != 0 :
            reward = collision_reward

        print("Ici ",reward)
        new_state = (
            new_head,
            tuple(new_radar.values()),
        )
        self.agent.set(state, self.snake_direction, reward, new_state)

        self.snake.move(new_head)
        self.update_snake_position()

        self.update_food_positions()

        self.total_reward += reward
        self.current_episode_score += reward

        scripted_action = self.scripted_snake.decide_action(self.env)
        scripted_new_head, _ = self.env.move(self.scripted_snake, scripted_action)
        self.scripted_snake.move(scripted_new_head)
        self.update_scripted_snake_position()

        self.save_counter += 1
        if self.save_counter >= 3000:
            try:
                self.agent.save(FILE_AGENT)
                self.turn_count += 1
                print("QTable sauvegardée après 3000 coups.")
            except Exception as e:
                print(f"Erreur lors de la sauvegarde de la QTable : {e}")
            self.end_episode()
            self.save_counter = 0

    def on_update(self, delta_time):
        self.time_since_last_move += delta_time

        if self.time_since_last_move >= self.snake_move_interval:
            self.time_since_last_move = 0

            try:
                self.do()
            except Exception as e:
                print(f"Erreur dans on_update : {e}")
                raise

    def on_key_press(self, key, modifiers):
        if key == arcade.key.F:
            self.plot_episode_history()
            self.close()
        elif key == arcade.key.L:
            self.manual_control = not self.manual_control
        elif key == arcade.key.O:
            self.snake_move_interval = min(1.0, self.snake_move_interval * 2)
        elif key == arcade.key.P:
            self.snake_move_interval = max(0.001, self.snake_move_interval / 2)
        elif self.manual_control:
            if key == arcade.key.Z:
                self.pending_direction = ACTION_UP
            elif key == arcade.key.S:
                self.pending_direction = ACTION_DOWN
            elif key == arcade.key.Q:
                self.pending_direction = ACTION_LEFT
            elif key == arcade.key.D:
                self.pending_direction = ACTION_RIGHT

    def create_sprites(self, positions, resource):
        sprite_list = arcade.SpriteList()
        for position in positions:
            sprite = arcade.Sprite(resource, SPRITE_SIZE / 128)
            sprite.center_x = position[1] * SPRITE_SIZE + SPRITE_SIZE // 2
            sprite.center_y = (self.env.height - position[0] - 1) * SPRITE_SIZE + SPRITE_SIZE // 2
            sprite_list.append(sprite)
        return sprite_list

    def setup(self):
        game_state = self.env.get_game_state()

        self.wall_sprites = self.create_sprites(game_state["walls"], ":resources:images/tiles/brickGrey.png")
        self.food_sprites = self.create_sprites(game_state["food"], ":resources:images/items/star.png")
        self.bomb_sprites = self.create_sprites(game_state["bombs"], ":resources:images/tiles/bomb.png")

    def on_draw(self):
        arcade.start_render()
        self.wall_sprites.draw()
        self.food_sprites.draw()
        self.bomb_sprites.draw()
        self.snake_sprites.draw()
        self.snake_head_sprite.draw()
        self.scripted_snake_sprites.draw()
        self.scripted_snake_head_sprite.draw()

        arcade.draw_text(f"Score: {self.total_reward}", 10, self.height - 30, arcade.color.WHITE, 20)
        arcade.draw_text(f"Turns: {self.turn_count}", 10, self.height - 60, arcade.color.WHITE, 20)

    def update_snake_position(self):
        head_position = self.snake.body[0]
        self.snake_head_sprite.center_x = (head_position[1] + 0.5) * SPRITE_SIZE
        self.snake_head_sprite.center_y = (self.env.height - head_position[0] - 0.5) * SPRITE_SIZE

        if self.snake_direction == ACTION_UP:
            self.snake_head_sprite.angle = 180
        elif self.snake_direction == ACTION_DOWN:
            self.snake_head_sprite.angle = 0
        elif self.snake_direction == ACTION_LEFT:
            self.snake_head_sprite.angle = 270
        elif self.snake_direction == ACTION_RIGHT:
            self.snake_head_sprite.angle = 90

        while len(self.snake_sprites) > len(self.snake.body) - 1:
            self.snake_sprites.pop().kill()

        while len(self.snake_sprites) < len(self.snake.body) - 1:
            sprite = arcade.Sprite(":resources:images/topdown_tanks/treeGreen_large.png", SPRITE_SIZE / 128)
            self.snake_sprites.append(sprite)

        for i, segment in enumerate(self.snake.body[1:]):
            self.snake_sprites[i].center_x = (segment[1] + 0.5) * SPRITE_SIZE
            self.snake_sprites[i].center_y = (self.env.height - segment[0] - 0.5) * SPRITE_SIZE

    def update_scripted_snake_position(self):
        head_position = self.scripted_snake.body[0]
        self.scripted_snake_head_sprite.center_x = (head_position[1] + 0.5) * SPRITE_SIZE
        self.scripted_snake_head_sprite.center_y = (self.env.height - head_position[0] - 0.5) * SPRITE_SIZE

        if len(self.scripted_snake.body) > 1:
            neck_position = self.scripted_snake.body[1]
            if head_position[0] < neck_position[0]:
                self.scripted_snake_head_sprite.angle = 180
            elif head_position[0] > neck_position[0]:
                self.scripted_snake_head_sprite.angle = 0
            elif head_position[1] < neck_position[1]:
                self.scripted_snake_head_sprite.angle = 270
            elif head_position[1] > neck_position[1]:
                self.scripted_snake_head_sprite.angle = 90

        while len(self.scripted_snake_sprites) > len(self.scripted_snake.body):
            self.scripted_snake_sprites.pop().kill()

        while len(self.scripted_snake_sprites) < len(self.scripted_snake.body):
            sprite = arcade.Sprite(":resources:images/topdown_tanks/treeBrown_large.png", SPRITE_SIZE / 128)
            self.scripted_snake_sprites.append(sprite)

        for i, segment in enumerate(self.scripted_snake.body[1:]):
            self.scripted_snake_sprites[i].center_x = (segment[1] + 0.5) * SPRITE_SIZE
            self.scripted_snake_sprites[i].center_y = (self.env.height - segment[0] - 0.5) * SPRITE_SIZE

    def update_food_positions(self):
        for i, food in enumerate(self.env.food_positions):
            self.food_sprites[i].center_x = (food[1] + 0.5) * SPRITE_SIZE
            self.food_sprites[i].center_y = (self.env.height - food[0] - 0.5) * SPRITE_SIZE

    def end_episode(self):
        try:
            print(f"Fin de l'épisode. Score actuel : {self.current_episode_score}")
            self.episode_history.append(self.current_episode_score)
            self.episode_history = self.episode_history[-10000:]
            self.current_episode_score = 0
            self.total_reward = 0

            self.snake.total_reward = 0
            self.snake.body = [(1, 1)]
            self.snake.grow = False

            self.scripted_snake.body = [(self.env.height - 2, self.env.width - 2)]
            self.scripted_snake.grow = False

            self.env = Environment(generate_map(MAP_WIDTH, MAP_HEIGHT))
            qtable.update_epsilon()
            print('Ceci est l\'epsilon', qtable.epsilon)
            self.setup()
            print("Nouvelle carte générée et sprites réinitialisés.")
        except Exception as e:
            print(f"Erreur dans end_episode : {e}")
            raise

    def plot_episode_history(self):
        if self.episode_history:
            plt.plot(self.episode_history)
            plt.title("Scores des épisodes")
            plt.xlabel("Épisode")
            plt.ylabel("Score")
            plt.grid()
            plt.show()

    def check_collision(self):
        snake_head = self.snake.body[0]
        scripted_snake_head = self.scripted_snake.body[0]

        if snake_head == scripted_snake_head:
            print("Les deux têtes se sont rencontrées, aucune action prise.")
            return

        if snake_head in self.scripted_snake.body[1:]:
            print("Le snake a touché le corps du scripted_snake. Le snake meurt.")
            self.end_episode()
            return REWARD_DIE

        if scripted_snake_head in self.snake.body[1:]:
            print("Le scripted_snake a touché le corps du snake. Le scripted_snake meurt.")
            self.end_episode()
            return REWARD_KILL
        return 0


if __name__ == "__main__":
    MAP = generate_map(MAP_WIDTH, MAP_HEIGHT)
    env = Environment(MAP)

    qtable = QTable()
    snake = Snake(start_position=(1, 1), qtable=qtable)

    game = SnakeGame(SPRITE_SIZE * MAP_WIDTH, SPRITE_SIZE * MAP_HEIGHT, snake, env, qtable)

    game.setup()
    arcade.run()