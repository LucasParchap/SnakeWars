import arcade
import random
import os
import pickle

SPRITE_SIZE = 32
screen_width, screen_height = arcade.get_display_size()

MAP_WIDTH = screen_width // SPRITE_SIZE
MAP_HEIGHT = screen_height // SPRITE_SIZE

def generate_map(width, height):
    map_data = ["x" * width]
    for _ in range(height - 2):
        map_data.append("x" + "." * (width - 2) + "x")
    map_data.append("x" * width)
    return "\n".join(map_data)

REWARD_FOOD = 50
REWARD_SURVIVAL = 10
REWARD_NEAR_FOOD = 50
REWARD_AWAY_FOOD = -30
REWARD_OUT = -200
REWARD_BOMB = -250

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
    def __init__(self, learning_rate=0.1, discount_factor=0.95, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.99):
        self.table = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

    def reduce_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    def set(self, state, action, reward, new_state):
        state = tuple(state)
        new_state = tuple(new_state)

        if state not in self.table:
            self.table[state] = {action: 0 for action in ACTIONS}

        if new_state not in self.table:
            self.table[new_state] = {action: 0 for action in ACTIONS}

        max_future_q = max(self.table[new_state].values())
        current_q = self.table[state][action]
        delta = reward + self.discount_factor * max(self.table[new_state].values()) - self.table[state][action]
        self.table[state][action] += self.learning_rate * delta

    def best_action(self, state):
        state = tuple(state)
        if state in self.table and self.table[state]:
            if random.random() < self.epsilon:
                return random.choice(ACTIONS)
            return arg_max(self.table[state])
        else:
            return random.choice(ACTIONS)

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.table, file)

    def load(self, filename):
        with open(filename, 'rb') as file:
            self.table = pickle.load(file)


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
        positions = []
        empty_spaces = [
            (row_idx, col_idx)
            for row_idx, row in enumerate(self.map)
            for col_idx, cell in enumerate(row)
            if cell == '.'
        ]
        while len(positions) < num_food and empty_spaces:
            pos = random.choice(empty_spaces)
            if all(abs(pos[0] - p[0]) + abs(pos[1] - p[1]) > 3 for p in positions):
                positions.append(pos)
                empty_spaces.remove(pos)
        return positions

    def place_bombs(self, num_bombs):
        positions = []
        empty_spaces = [
            (row_idx, col_idx)
            for row_idx, row in enumerate(self.map)
            for col_idx, cell in enumerate(row)
            if cell == '.' and (row_idx, col_idx) not in self.food_positions
        ]
        while len(positions) < num_bombs and empty_spaces:
            pos = random.choice(empty_spaces)
            positions.append(pos)
            empty_spaces.remove(pos)
        return positions
    def get_radar(self, head):
        if not isinstance(head, tuple) or len(head) != 2:
            raise ValueError(f"Invalid head position: {head}")

        radar = {
            ACTION_UP: self.height - head[0],
            ACTION_DOWN: head[0],
            ACTION_LEFT: head[1],
            ACTION_RIGHT: self.width - head[1]
        }

        food_distances = {
            ACTION_UP: min([abs(food[0] - head[0]) for food in self.food_positions] or [self.height]),
            ACTION_DOWN: min([abs(food[0] - head[0]) for food in self.food_positions] or [self.height]),
            ACTION_LEFT: min([abs(food[1] - head[1]) for food in self.food_positions] or [self.width]),
            ACTION_RIGHT: min([abs(food[1] - head[1]) for food in self.food_positions] or [self.width]),
        }
        return {**radar, **food_distances}

    def move(self, snake, action):
        move = MOVES[action]
        new_head = (snake.body[0][0] + move[0], snake.body[0][1] + move[1])

        if new_head in self.walls:
            return snake.body[0], REWARD_OUT

        if new_head in self.bomb_positions:
            print(f"Bomb hit! Position: {new_head}. Snake loses 50% of its body.")
            snake.reduce_body(0.5)
            return new_head, REWARD_OUT

        reward = 0
        if new_head in self.food_positions:
            self.food_positions.remove(new_head)
            self.food_positions.append(self.place_food(1)[0])
            snake.grow = True
            reward += REWARD_FOOD
        else:
            closest_food = min(self.food_positions,
                               key=lambda food: abs(food[0] - new_head[0]) + abs(food[1] - new_head[1]))
            current_distance = abs(closest_food[0] - snake.body[0][0]) + abs(closest_food[1] - snake.body[0][1])
            new_distance = abs(closest_food[0] - new_head[0]) + abs(closest_food[1] - new_head[1])

            if new_distance < current_distance:
                reward += 5
            else:
                reward -= 10

        return new_head, reward


class Snake:
    def __init__(self, start_position):
        self.body = [start_position]
        self.grow = False

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

class SnakeGame(arcade.Window):
    def __init__(self, width, height, snake, env, agent):
        super().__init__(width, height, "Snake Game", fullscreen=True)
        self.env = env
        self.snake = snake
        self.agent = agent
        arcade.set_background_color(arcade.color.BLACK)
        self.total_reward = 0

        self.wall_sprites = None
        self.food_sprites = None
        self.snake_sprites = arcade.SpriteList()

        self.snake_head_sprite = arcade.Sprite("assets/snake_head.png", scale=1)

        self.time_since_last_move = 0
        self.snake_move_interval = 0.1
        self.snake_direction = ACTION_RIGHT
        self.pending_direction = self.snake_direction

        self.manual_control = False

    def do(self):
        head_position = self.snake.body[0]
        radar = self.env.get_radar(head_position)

        state = (
            head_position,
            tuple(self.env.food_positions),
            tuple(self.snake.body[1:]),
            tuple(radar.values())
        )

        action = self.agent.best_action(state)

        new_head, reward = self.env.move(self.snake, action)

        new_radar = self.env.get_radar(new_head)
        new_state = (
            new_head,
            tuple(self.env.food_positions),
            tuple(self.snake.body[1:]),
            tuple(new_radar.values())
        )

        self.agent.set(state, action, reward, new_state)
        self.agent.reduce_epsilon()

        self.snake.move(new_head)
        self.update_snake_position()
        self.update_food_positions()

        self.total_reward += reward
    def on_key_press(self, key, modifiers):
        if key == arcade.key.F:
            self.close()
        elif key == arcade.key.L:
            self.manual_control = not self.manual_control
        elif self.manual_control:
            if key == arcade.key.Z:
                self.pending_direction = ACTION_UP
            elif key == arcade.key.S:
                self.pending_direction = ACTION_DOWN
            elif key == arcade.key.Q:
                self.pending_direction = ACTION_LEFT
            elif key == arcade.key.D:
                self.pending_direction = ACTION_RIGHT

    def setup(self):
        self.wall_sprites = arcade.SpriteList()
        for wall in self.env.walls:
            sprite = arcade.Sprite(":resources:images/tiles/brickGrey.png", SPRITE_SIZE / 128)
            sprite.center_x = wall[1] * SPRITE_SIZE + SPRITE_SIZE // 2
            sprite.center_y = (self.env.height - wall[0] - 1) * SPRITE_SIZE + SPRITE_SIZE // 2
            self.wall_sprites.append(sprite)

        self.food_sprites = arcade.SpriteList()
        for food in self.env.food_positions:
            sprite = arcade.Sprite(":resources:images/items/star.png", SPRITE_SIZE / 128)
            sprite.center_x = food[1] * SPRITE_SIZE + SPRITE_SIZE // 2
            sprite.center_y = (self.env.height - food[0] - 1) * SPRITE_SIZE + SPRITE_SIZE // 2
            self.food_sprites.append(sprite)

        self.bomb_sprites = arcade.SpriteList()
        for bomb in self.env.bomb_positions:
            sprite = arcade.Sprite(":resources:images/tiles/bomb.png", SPRITE_SIZE / 128)
            sprite.center_x = bomb[1] * SPRITE_SIZE + SPRITE_SIZE // 2
            sprite.center_y = (self.env.height - bomb[0] - 1) * SPRITE_SIZE + SPRITE_SIZE // 2
            self.bomb_sprites.append(sprite)

    def on_draw(self):
        arcade.start_render()
        self.wall_sprites.draw()
        self.food_sprites.draw()
        self.bomb_sprites.draw()
        self.snake_sprites.draw()
        self.snake_head_sprite.draw()

    def on_update(self, delta_time):
        self.time_since_last_move += delta_time

        if self.time_since_last_move >= self.snake_move_interval:
            self.time_since_last_move = 0

            head_position = self.snake.body[0]

            radar = self.env.get_radar(head_position)

            state = (
                head_position,
                tuple(self.env.food_positions),
                tuple(self.snake.body[1:]),
                tuple(radar.values())
            )

            if self.manual_control:
                self.snake_direction = self.pending_direction
            else:
                self.snake_direction = self.agent.best_action(state)

            new_head, reward = self.env.move(self.snake, self.snake_direction)

            if not isinstance(new_head, tuple) or len(new_head) != 2:
                raise ValueError(f"Invalid new head position: {new_head}")

            if not self.manual_control:
                new_radar = self.env.get_radar(new_head)
                new_state = (
                    new_head,
                    tuple(self.env.food_positions),
                    tuple(self.snake.body[1:]),
                    tuple(new_radar.values())
                )
                self.agent.set(state, self.snake_direction, reward, new_state)
                self.agent.reduce_epsilon()

            self.snake.move(new_head)
            self.update_snake_position()
            self.update_food_positions()
            self.total_reward += reward

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

    def update_food_positions(self):
        for i, food in enumerate(self.env.food_positions):
            self.food_sprites[i].center_x = (food[1] + 0.5) * SPRITE_SIZE
            self.food_sprites[i].center_y = (self.env.height - food[0] - 0.5) * SPRITE_SIZE



if __name__ == "__main__":
    MAP = generate_map(MAP_WIDTH, MAP_HEIGHT)
    env = Environment(MAP)

    snake = Snake((1, 1))
    agent = QTable()

    if os.path.exists(FILE_AGENT):
        agent.load(FILE_AGENT)

    game = SnakeGame(SPRITE_SIZE * MAP_WIDTH, SPRITE_SIZE * MAP_HEIGHT, snake, env, agent)
    game.setup()
    arcade.run()

    agent.save(FILE_AGENT)






