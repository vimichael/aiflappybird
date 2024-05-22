# Expanation

## "What did you use to make this?"

The __windowing__, __graphics__, and __audio__ were made using PyGame, a python wrapper over SDL2 with additional functionality.

The __A.I.__ playing the game comes from __neat-python__, a reinforcement neural network library that's easy to setup and use in python projects.

## Architecture

The application starts at the bottom of the file:

```python
if __name__ == "__main__":
    ...
```

This basically says "only run me when I am being called directly". This means no other program can start an instance of the flappy bird program.

You'll also notice everything is encapsulated. I chose a procedural organization of objects given the limited scope of the game. The classes `Player` and `Pipe` simply house the data and functionality of the __birds__ and __pipes__ respectively.

The `Game` class is a monolithic class that starts, manages, and disposes of the application. While it isn't a singleton, it is treated like one. *Since the state of the game is encapsulated, multiple instances __could__ be executed at once, but it hasn't been tested.*

The game houses a `run` method, where the entire game is processed. Every frame, the sprites are updated and drawn. The entire display is redrawn to a back buffer, and then flipped to be the main buffer at the end.

In order to get this to work with A.I., I removed the start menu and added a second condition to the game loop. The game will only run as long as there is at least 1 bird alive. I did this because we want the game to continually run between generations.

## PyGame Specifics

You'll notice a heavy use of `self.screen.blit` throughout the code. This literally means "block transfer" and is the Pygame API's way of saying "draw something at this location". The function takes in a Surface (image) and a position (x, y).

There are some other pieces of code that only make sense if you're used to working with game frameworks. Again, the game loop runs every frame and writes to a back buffer. The buffer is updated with `pygame.display.update()`. *Technically, you could flip the buffers multiple times per game loop, but that is not recommended.* There is also this line:

```python
dt = self.clock.tick(Game.FPS) / 1000.0
```

This line sets the target FPS (frames per second of the app). Additionally, it returns the time between the last frame and this one. We divide this by 1000.0 to get the amount of time (in seconds). Why does this matter?

Well, you'll notice we use `dt` whenever anything in the game moves. It means that on __any__ machine, the game will run at the same speed, regardless of the CPU power. *In older games, dt was not as commonplace, which lead to certain exploits being possible on some versions and not others*.

## NEAT Specifics

In the `main_ai.py` version, the game first goes through an external `run` function before starting the app. This initializes __NEAT__ with the `config.txt` file. Some changes had to be made to the `Game`'s `run` method aswell (Yes, having two functions called `run` is confusing, sorry.). The run function now take in the genomes and the config file. before starting the game, it stores the genomes and creates a network for each of them. It also creates an instance of `Player` for each, and stores them in a list. These 3 lists: `ges`, `networks`, and `birds` are __parallel__, meaning that `ges[index] = networks[index] = birds[index]`. This is important for the architecture of the program. For a more robust implimentation, I'd recommend making a data structure to hold these, to ensure that edge cases do not disrupt this parallelism.

The genome's __fitness__ measures the performance of each node. The more fitness, the better. The program will run until the target fitness is met, or all generations die out. There are 2 ways to gain fitness:

- Surviving for a frame
- Passing a pipe

These __incentivize__ the network to keep pushing forward. It will try to find a way to stay alive for more frames and pass more pipes.

Of course, the birds can't see, which means we need to give them vision. It would be far too much information to give them the entire back buffer and have them decode the world and make a decision... 60 times a second. Instead, give it only what we need.

```python
output = networks[birds.index(bird)].activate((
    (bird.rect.centery),
    self.pipes[active_pipe_index].top_rect.bottom,
    self.pipes[active_pipe_index].bottom_rect.top
))
```

Here we are passing 3 arguments (as specified in `config.txt`). We pass in the player's `y` position, the bottom `y` position of the top pipe, and the top `y` position of the bottom pipe. This gives the networks plenty of data to work with.

What is very interesting is that there is no identifying what the network *is*. We aren't saying, "you are here. The pipes are here". We aren't even specifying which of the 3 args are pipes. It doesn't even know what a pipe is. All it knows is: If i give this output, it changes the values in a way that gives me more fitness.

Since there are only 3 parameters passed, and the game is very repetitive, it is trivial for a neural network to learn to play Flappy Bird. In my personal tests, it generally learns to play the game within the first dozen generations, sometimes even on the second or third.