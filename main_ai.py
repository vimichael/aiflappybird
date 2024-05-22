# imports
import neat.config
import pygame
from pygame.math import Vector2
from enum import Enum
import os
import neat
import random

def deserialize_highscore() -> int:
	with open("score.txt", 'r') as f:
		line = f.readline()
		try:
			return int(line)
		except:
			print("Failed to load high score from file!")
			serialize_highscore(0)
			return 0

def serialize_highscore(score: int):
	with open("score.txt", 'w') as f:
		f.write(str(score))

class GameState(Enum):
	START = 0,
	MAIN = 1

class Pipe:
	'''
	Represents one pipe in the world (bottom and top)
	'''

	SPEED = 300
	TOP: pygame.Surface = None
	BOTTOM: pygame.Surface = None
	GAPSIZE = 200
	SPACING = 180
	VISUALOFFSET = -100

	def __init__(self, position: Vector2) -> None:
		self.top_rect: pygame.Rect = Pipe.TOP.get_rect()
		self.bottom_rect: pygame.Rect = Pipe.BOTTOM.get_rect()
		self.position = position
		self.active = True
		
		
	def update(self, dt: float) -> None:
		self.move_x(-Pipe.SPEED*dt)

		if self.position.x < Pipe.VISUALOFFSET:
			self.position = Vector2(
				self.reset_dest_x, 
				self.position.y + random.randint(-150, 150)
			)
			self.active = True

	def draw(self, surface) -> None:
		surface.blit(Pipe.TOP, self.top_rect)
		surface.blit(Pipe.BOTTOM, self.bottom_rect)

	@property
	def position(self) -> Vector2:
		return self._position

	@position.setter
	def position(self, val: Vector2) -> None:
		self._position = val
		self.top_rect.bottomleft = val
		self.bottom_rect.topleft = (val.x, val.y + Pipe.GAPSIZE)

	@property
	def reset_dest_x(self) -> int:
		return Game.SCREENSIZE.x + Pipe.SPACING + Pipe.VISUALOFFSET

	def move_x(self, val):
		self._position.x += val
		self.top_rect.x += val
		self.bottom_rect.x += val

class Player:
	'''
	Represents the player in the world
	'''

	GRAVITY = 50
	JUMPPOWER = 600
	TVEL = 1500

	def __init__(self, image: pygame.Surface, position: Vector2) -> None:
		self.image: pygame.Surface = image
		self.rect: pygame.Rect = self.image.get_rect(topleft = position)
		self.velocity: pygame.Vector2 = Vector2()

	def jump(self):
		self.velocity.y = -Player.JUMPPOWER

	def update(self, dt: float):
		self.velocity.y += Player.GRAVITY

		self.velocity.y = max(-Player.TVEL, min(self.velocity.y, Player.TVEL))

		self.rect.x += self.velocity.x * dt
		self.rect.y += self.velocity.y * dt

	def draw(self, surface: pygame.Surface):
		surface.blit(self.image, self.rect)

class Game:
	SCREENSIZE: Vector2 = Vector2(360, 640)
	FPS = 60
	FONT: pygame.font.Font = None
	FONTLG = None
	STATE: GameState

	def __init__(self) -> None:
		# initially pygame
		pygame.init()
		# initialize the screen, clock and running state
		self.screen: pygame.Surface = pygame.display.set_mode(Game.SCREENSIZE)
		self.clock = pygame.time.Clock()
		self.running = True
		self.debug = False

		self.score: int = 0
		self.high_score: int = deserialize_highscore()

		# initialize the fonts and the game state
		Game.FONT = pygame.font.Font(None, 30)
		Game.FONTLG = pygame.font.Font(None, 60)
		Game.STATE = GameState.START

		# initialize text data
		self.text_pool: dict[str, dict[str, any]] = {}

		# create first text entry (image, position)
		self.text_pool["start_prompt"] = {}
		self.text_pool["start_prompt"]["surface"] = Game.FONT.render("Press Space to Start", True, "black", None)
		self.text_pool["start_prompt"]["rect"] = self.text_pool["start_prompt"]["surface"].get_rect(center = (Game.SCREENSIZE.x/2, Game.SCREENSIZE.y/2 - 100))

		# load the background image
		self.bg_img: pygame.Surface = pygame.image.load("assets/flappybirdbg.png").convert()

		Pipe.TOP = pygame.image.load('assets/toppipe.png').convert_alpha()
		Pipe.BOTTOM = pygame.image.load('assets/bottompipe.png').convert_alpha()

		Pipe.TOP = pygame.transform.scale_by(Pipe.TOP, 0.25)
		Pipe.BOTTOM = pygame.transform.scale_by(Pipe.BOTTOM, 0.25)

		# setup the game
		self.setup()

	def setup(self):

		# position the player and reset velocity
		# self.player.rect.center = (Game.SCREENSIZE.x/2, Game.SCREENSIZE.y/2)
		# self.player.velocity = Vector2()

		# empty the list of pipes
		self.pipes: list[Pipe] = []

		# insert 3 pipes
		self.pipes.append(Pipe(Vector2(Game.SCREENSIZE.x, 200)))
		self.pipes.append(Pipe(Vector2(Game.SCREENSIZE.x + Pipe.SPACING, 200)))
		self.pipes.append(Pipe(Vector2(Game.SCREENSIZE.x + Pipe.SPACING*2, 250)))

		self.high_score = max(self.high_score, self.score)

		self.text_pool["high_score"] = {}
		self.text_pool["high_score"]["surface"] = Game.FONT.render(f"High Score {self.high_score}", True, "black", None)
		self.text_pool["high_score"]["rect"] = self.text_pool["high_score"]["surface"].get_rect(center = (Game.SCREENSIZE.x/2, Game.SCREENSIZE.y/2 - 200))

		# reset the score
		self.score = 0
		self.score_text: pygame.Surface = Game.FONTLG.render(str(self.score), True, "white")

	def run(self, genomes, config) -> None:

		# load the player image and scale it
		player_img = pygame.image.load("assets/flappybird.png").convert_alpha()
		player_img = pygame.transform.scale_by(player_img, 0.1)

		player_spawn_pos = Vector2((Game.SCREENSIZE.x/2)-(player_img.get_width()/2), (Game.SCREENSIZE.y/2)-(player_img.get_height()/2))

		networks = []
		ges = []
		birds: list[Player] = []

		# loop over genomes
		for id, genome in genomes:
			genome.fitness = 0 # set the init fitness level
			network = neat.nn.FeedForwardNetwork.create(genome, config)
			networks.append(network)
			birds.append(Player(player_img, player_spawn_pos))
			ges.append(genome)

		# game loop
		while self.running and len(birds) > 0:

			# set a target fps
			dt: float = self.clock.tick(Game.FPS) / 1000.0

			# poll for all io events
			events = pygame.event.get()

			# check for the user quitting events
			for e in events:
				if e.type == pygame.QUIT:
					self.running = False
				elif e.type == pygame.KEYDOWN:
					if e.key == pygame.K_q:
						self.running = False
					elif e.key == pygame.K_d:
						self.debug = not self.debug

			# draw the background
			self.screen.blit(self.bg_img, (0,0))

			# current pipe (the leftmost pipe that is still active after iteration)
			active_pipe_index = 0

			for pipe in self.pipes:

				# update the pipe
				pipe.update(dt)
				
				# state var. if complete, pipe is now behind all birds
				complete = False

				kill_list = []

				# check if birds passed the pipe
				for bird in birds:
					if pipe.position.x < bird.rect.x and pipe.active:
						pipe.active = False
						complete = True

					# kill bird if it collides with pipe
					if bird.rect.colliderect(pipe.bottom_rect) or bird.rect.colliderect(pipe.top_rect):
						kill_list.append(bird)
					if bird.rect.bottom > Game.SCREENSIZE.y:
						kill_list.append(bird)

				# free all birds from kill_list
				for bird in kill_list:
					
					networks.pop(birds.index(bird))
					ges.pop(birds.index(bird))
					birds.remove(bird)

				if complete:
					self.score += 1
					active_pipe_index += 1

					for gen in ges:
						gen.fitness += 5

					print(f"Score: {self.score}")

				
					

				pipe.draw(self.screen)
				if self.debug:
					pygame.draw.rect(
						self.screen,
						"red",
						pipe.top_rect,
						2
					)
					pygame.draw.rect(
						self.screen,
						"red",
						pipe.bottom_rect,
						2
					)
			
			for index, bird in enumerate(birds):
				bird.update(dt)

				ges[index].fitness += 0.1

				# sending bird's position, bottom of the top pipe
				output = networks[birds.index(bird)].activate((
					(bird.rect.centery),
					self.pipes[active_pipe_index].top_rect.bottom,
					self.pipes[active_pipe_index].bottom_rect.top
				))

				# if output reaches threshold (intelligently placed at 0.5)
				if output[0] > 0.5:
					bird.jump()

				bird.draw(self.screen)

			if self.debug:

				for bird in birds:
					pygame.draw.rect(
						self.screen,
						"green",
						bird.rect,
						2
					)

			# update the display
			pygame.display.update()

	def close(self):
		serialize_highscore(self.high_score)
		pygame.quit()

NUM_GENERATIONS = 50

def run(config_path: str) -> None:

	# setup config container
	config = neat.config.Config(
		neat.DefaultGenome, 
		neat.DefaultReproduction,
		neat.DefaultSpeciesSet,
		neat.DefaultStagnation,
		config_path
	)

	# generate the population
	population = neat.Population(config)

	# have NEAT print to the stdout for debug info
	population.add_reporter(neat.StdOutReporter(True))
	population.add_reporter(neat.StatisticsReporter())

	game = Game()
	winner = population.run(game.run, NUM_GENERATIONS)

	print(f"Winner of the round: {winner}")

# ENTRY POINT OF THE APP
if __name__ == "__main__":
	
	local_dir = os.path.dirname(__file__) # get path to file
	config_path = os.path.join("config.txt") # get the config path
	run(config_path)

	pygame.quit()