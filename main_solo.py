# imports
import pygame
from pygame.math import Vector2
from enum import Enum

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

    SPEED = 5
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
        
        
    def update(self, gametime: int = 0) -> None:
        self.move_x(-Pipe.SPEED)

        if self.position.x < Pipe.VISUALOFFSET:
            self.position = Vector2(self.reset_dest_x, self.position.y)
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

    GRAVITY = 1
    JUMPPOWER = 13
    TVEL = 20

    def __init__(self, image: pygame.Surface, position: Vector2) -> None:
        self.image: pygame.Surface = image
        self.rect: pygame.Rect = self.image.get_rect(topleft = position)
        self.velocity: pygame.Vector2 = Vector2()

    def update(self, events: list[pygame.event.Event]):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                self.velocity.y = -Player.JUMPPOWER

        self.velocity.y += Player.GRAVITY

        self.velocity.y = max(-Player.TVEL, min(self.velocity.y, Player.TVEL))

        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

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

        # load the player image and scale it
        player_img = pygame.image.load("assets/flappybird.png").convert_alpha()
        player_img = pygame.transform.scale_by(player_img, 0.1)

        # load the background image
        self.bg_img: pygame.Surface = pygame.image.load("assets/flappybirdbg.png").convert()

        Pipe.TOP = pygame.image.load('assets/toppipe.png').convert_alpha()
        Pipe.BOTTOM = pygame.image.load('assets/bottompipe.png').convert_alpha()

        Pipe.TOP = pygame.transform.scale_by(Pipe.TOP, 0.25)
        Pipe.BOTTOM = pygame.transform.scale_by(Pipe.BOTTOM, 0.25)

        # initialize the player (only done once, so not )
        self.player: Player = Player(player_img, Vector2((Game.SCREENSIZE.x/2)-(player_img.get_width()/2), (Game.SCREENSIZE.y/2)-(player_img.get_height()/2)))

        # setup the game
        self.setup()

    def setup(self):

        # position the player and reset velocity
        self.player.rect.center = (Game.SCREENSIZE.x/2, Game.SCREENSIZE.y/2)
        self.player.velocity = Vector2()

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

    def run(self) -> None:

        # game loop
        while self.running:

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

            match Game.STATE:

                case GameState.START:

                    # start the game on space
                    for e in events:
                        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                            Game.STATE = GameState.MAIN

                    # draw the text prompt
                    self.screen.blit(
                        self.text_pool["start_prompt"]["surface"], 
                        self.text_pool["start_prompt"]["rect"]
                    )

                    # draw the text prompt
                    self.screen.blit(
                        self.text_pool["high_score"]["surface"], 
                        self.text_pool["high_score"]["rect"]
                    )

                case GameState.MAIN:

                    for pipe in self.pipes:

                        # update the pipe
                        pipe.update()
                        
                        # when the player passes through a pipe
                        if pipe.position.x < self.player.rect.x and pipe.active:
                            pipe.active = False
                            self.score += 1
                            self.score_text: pygame.Surface = Game.FONTLG.render(str(self.score), True, "white")

                        # reset the game if the player hits a pipe
                        if self.player.rect.colliderect(pipe.bottom_rect) or self.player.rect.colliderect(pipe.top_rect):
                            Game.STATE = GameState.START
                            self.setup()

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
                    
                    self.player.update(events)
                    self.screen.blit(self.score_text, ((Game.SCREENSIZE.x/2 - (self.score_text.get_width()/2)), 50))

            self.player.draw(self.screen)
            if self.debug:
                pygame.draw.rect(
                    self.screen,
                    "green",
                    self.player.rect,
                    2
                )

            # update the display
            pygame.display.update()
            # set a target fps
            self.clock.tick(Game.FPS)

        # quit the app
        self.close()

    def close(self):
        serialize_highscore(self.high_score)
        pygame.quit()

# ENTRY POINT OF THE APP
if __name__ == "__main__":
    Game().run()