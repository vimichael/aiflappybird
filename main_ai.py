# imports
import neat.config
import pygame
from pygame.math import Vector2
from enum import Enum
import os
import neat
import random

HIGHSCORE_SAVE_FILE = "score_ai.txt"

# for saving and loading. Serializes and deserializes the high score

def deserialize_highscore() -> int:
	with open(HIGHSCORE_SAVE_FILE, 'r') as f:
		line = f.readline()
		try:
			return int(line)
		except:
			print("Failed to load high score from file!")
			serialize_highscore(0)
			return 0

def serialize_highscore(score: int):
	with open(HIGHSCORE_SAVE_FILE, 'w') as f:
		f.write(str(score))

class Pipe:
	'''
	Represents one pipe in the world (bottom and top)
	'''

	SPEED = 300
	TOP: pygame.Surface = None
	BOTTOM: pygame.Surface = None
	GAPSIZE = 300
	SPACING = 180
	VISUALOFFSET = -100

	def __init__(self, position: Vector2) -> None:
		self.top_rect: pygame.Rect = Pipe.TOP.get_rect(bottom = position.y - Pipe.GAPSIZE/2)
		self.bottom_rect: pygame.Rect = Pipe.BOTTOM.get_rect(top = position.y + Pipe.GAPSIZE/2)
		self._position = position
		self.active = True
		
	def update(self, dt: float) -> None:
		self.move_x(-Pipe.SPEED*dt)

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
		# self.top_rect.bottom -= Pipe.GAPSIZE/2
		self.bottom_rect.topleft = (val.x, val.y + Pipe.GAPSIZE)
		# self.bottom_rect.top += Pipe.GAPSIZE/2

	@property
	def reset_dest_x(self) -> int:
		return Game.SCREENSIZE.x + Pipe.SPACING + Pipe.VISUALOFFSET

	def move_x(self, val):
		self._position.x += val
		self.top_rect.x = self._position.x
		self.bottom_rect.x = self._position.x

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
		# applying gravity (with a max of TVEL)
		self.velocity.y += Player.GRAVITY
		self.velocity.y = max(-Player.TVEL, min(self.velocity.y, Player.TVEL))

		self.rect.x += self.velocity.x * dt
		self.rect.y += self.velocity.y * dt
		self.rect.y = max(0, self.rect.y)

	def draw(self, surface: pygame.Surface):
		surface.blit(self.image, self.rect)

class Game:

	SCREENSIZE: Vector2 = Vector2(360, 640)
	FPS = 60
	FONT: pygame.font.Font = None
	FONTLG = None

	def __init__(self) -> None:

		# initially pygame
		pygame.init()
		pygame.font.init()
		pygame.mixer.init()

		# load sounds
		self.sfx_hit = pygame.mixer.Sound("assets/hit.mp3")
		self.sfx_jump = pygame.mixer.Sound("assets/flap.mp3")
		self.sfx_die = pygame.mixer.Sound("assets/die.mp3")
		self.sfx_score = pygame.mixer.Sound("assets/score.mp3")

		self.sounds = [
			self.sfx_hit,
			self.sfx_jump,
			self.sfx_die,
			self.sfx_score
		]
		
		for sound in self.sounds:
			sound.set_volume(0.2)

		pygame.mixer.music.set_volume(0.2)

		# keeps track of the current neural network generation
		self.generation = 0

		# initialize the screen, clock and running state
		self.screen: pygame.Surface = pygame.display.set_mode(Game.SCREENSIZE)
		self.clock = pygame.time.Clock()
		
		# initiailize state vars
		self.running = True
		self.debug = False
		self.muted = False

		self.score: int = 0
		self.high_score: int = deserialize_highscore()

		# initialize the fonts and the game state
		Game.FONT = pygame.font.Font(None, 30)
		Game.FONTLG = pygame.font.Font(None, 60)

		# load the background image
		self.bg_img: pygame.Surface = pygame.image.load("assets/flappybirdbg.png").convert()

		# load pipe assets
		Pipe.TOP = pygame.image.load('assets/toppipe.png').convert_alpha()
		Pipe.BOTTOM = pygame.image.load('assets/bottompipe.png').convert_alpha()

		Pipe.TOP = pygame.transform.scale_by(Pipe.TOP, 0.25)
		Pipe.BOTTOM = pygame.transform.scale_by(Pipe.BOTTOM, 0.25)

		# setup the game
		self.setup()

	def setup(self):

		# empty the list of pipes
		self.pipes: list[Pipe] = []

		# insert 3 pipes
		self.pipes.append(Pipe(Vector2(Game.SCREENSIZE.x, 200)))
		self.pipes.append(Pipe(Vector2(Game.SCREENSIZE.x + Pipe.SPACING, 200)))
		self.pipes.append(Pipe(Vector2(Game.SCREENSIZE.x + Pipe.SPACING*2, 250)))

		self.high_score = max(self.high_score, self.score)

		# reset the score
		self.score = 0

	def run(self, genomes, config) -> None:

		# for quitting before generations are finished
		# early return if the game is not running
		if not self.running:
			return

		self.generation += 1

		# load the player image and scale it
		player_img = pygame.image.load("assets/flappybird.png").convert_alpha()
		player_img = pygame.transform.scale_by(player_img, 0.1)

		player_spawn_pos = Vector2((Game.SCREENSIZE.x/2)-(player_img.get_width()/2), (Game.SCREENSIZE.y/2)-(player_img.get_height()/2))

		# create parallel lists to keep track of the birds and their respective networks + genomes
		networks = []
		ges = []
		birds: list[Player] = []

		# loop over genomes and init birds
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
					elif e.key == pygame.K_m:

						if self.muted:
							for sound in self.sounds:
								sound.set_volume(0.2)
						else:
							for sound in self.sounds:
								sound.set_volume(0)
						self.muted = not self.muted
						

			# draw the background
			self.screen.blit(self.bg_img, (0,0))
			
			# if a pipe is offscreen, it is assigned to this var
			dead_pipe = None
			
			# keeps track of the target pipe
			active_pipe_index = 1
			for pipe in self.pipes:

				# update the pipe
				pipe.update(dt)

				# if pipe is offscreen
				if pipe.position.x < -pipe.top_rect.width:
					dead_pipe = pipe

				kill_list = []

				# check if birds passed the pipe
				for bird in birds:
					# check if bird passes the pipe
					if pipe.position.x < bird.rect.x and pipe.active:

						# if it does, add to the score
						if pipe.active:
							# set pipe to inactive so it can only add to the score once
							pipe.active = False

							# reward the birds
							for gen in ges:
								gen.fitness += 5
							
							self.sfx_score.play()
							self.score += 1
							print(f"Score: {self.score}")

						active_pipe_index += 1
						

					# kill bird if it collides with pipe
					if bird.rect.colliderect(pipe.bottom_rect) or bird.rect.colliderect(pipe.top_rect):
						kill_list.append(bird)
						self.sfx_hit.play()

					# kill bird if it his the ground
					if bird.rect.bottom > Game.SCREENSIZE.y:
						kill_list.append(bird)
						self.sfx_die.play()

				# free all birds from kill_list
				for bird in kill_list:
					
					print(f"Bird died. {len(birds)} left")

					networks.pop(birds.index(bird))
					ges.pop(birds.index(bird))
					birds.remove(bird)
					
				# draw the pipe
				pipe.draw(self.screen)

				# draw hitbox around target pipe, circle for its pos + more
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
					pygame.draw.circle(
						self.screen,
						"blue",
						pipe.position,
						15.0,
						1
					)
					pygame.draw.line(
						self.screen,
						"blue",
						(
							pipe.top_rect.centerx,
							pipe.top_rect.bottom
						),
						(
							pipe.bottom_rect.centerx,
							pipe.bottom_rect.top
						),
						2
					)
			
			# remove dead pipe and create a new one in the back
			if dead_pipe != None:
				self.pipes.remove(dead_pipe)

				last_pipe_pos = self.pipes[len(self.pipes)-1].position

				self.pipes.append(
					Pipe(
						Vector2(
							last_pipe_pos.x + Pipe.SPACING,
							random.randint(200, 400)
					  	)
					)
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
					self.sfx_jump.play()

				bird.draw(self.screen)

			if self.debug:

				# draw the thicker red around current pipe being fed to networks
				if self.debug:
					pygame.draw.rect(
						self.screen,
						"red",
						self.pipes[active_pipe_index].top_rect,
						6
					)
					pygame.draw.rect(
						self.screen,
						"red",
						self.pipes[active_pipe_index].bottom_rect,
						6
					)

				# draw hitbox of the birds
				for bird in birds:
					pygame.draw.rect(
						self.screen,
						"green",
						bird.rect,
						2
					)

				self.screen.blit(
					Game.FONT.render(f"Num Birds: {len(birds)}", True, "black"),
					(10,10)
				)
				self.screen.blit(
					Game.FONT.render(f"Generation: {self.generation}", True, "black"),
					(10,50)
				)
				self.screen.blit(
					Game.FONT.render(f"Score: {self.score}", True, "black"),
					(10,90)
				)
				self.screen.blit(
					Game.FONT.render(f"Muted: {self.muted}", True, "black"),
					(10,130)
				)

			else:

				text = Game.FONTLG.render(f"Score: {self.score}", True, "black")
				self.screen.blit(
					text,
					((Game.SCREENSIZE.x - text.get_width()) / 2, 50)
				)

			# update the display
			pygame.display.update()
		
		if self.score > self.high_score:
			serialize_highscore(self.score)
		self.score = 0

	def close(self):
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

	game.close()	

	print(f"Winner of the round: {winner}")

# ENTRY POINT OF THE APP
if __name__ == "__main__":
	
	local_dir = os.path.dirname(__file__) # get path to file
	config_path = os.path.join("config.txt") # get the config path
	run(config_path)