import pygame.font
from pygame import *
import sys
from os.path import abspath, dirname
from random import choice
import json

SCREEN_SIZE = pygame.Vector2(800, 600)
screen = pygame.display.set_mode(SCREEN_SIZE)

BASE_PATH = abspath(dirname(__file__))
FONT_PATH = BASE_PATH + '/fonts/'
IMAGE_PATH = BASE_PATH + '/images/'
SOUND_PATH = BASE_PATH + '/sounds/'

WHITE = (255, 255, 255)
GREEN = (78, 255, 87)
YELLOW = (241, 255, 0)
BLUE = (80, 255, 239)
PURPLE = (203, 0, 255)
RED = (237, 28, 36)

FONT = FONT_PATH + 'space_invaders.ttf'

IMG_NAMES = ['ship', 'mystery',
             'enemy1_1', 'enemy1_2',
             'enemy2_1', 'enemy2_2',
             'enemy3_1', 'enemy3_2',
             'explosionblue', 'explosiongreen', 'explosionpurple',
             'laser', 'enemylaser']

IMAGES = {name: image.load(IMAGE_PATH + '{}.png'.format(name)).convert_alpha()
          for name in IMG_NAMES}

BLOCKERS_POSITION = 450
ENEMY_DEFAULT_POSITION = 65
ENEMY_MOVE_DOWN = 35


class Button:
    def __init__(self, text, pos, size, callback):
        self.rect = pygame.Rect(pos, size)
        self.text = Text(FONT, 30, text, WHITE, pos[0] + 15, pos[1] + 10)
        self.callback = callback
        self.hover = False

    def draw(self, surface):
        color = YELLOW if self.hover else GREEN
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        self.text.draw(surface)

    def check_hover(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

    def click(self):
        if self.hover:
            self.callback()


class Ship(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['ship']
        self.rect = self.image.get_rect(topleft=(375, 540))
        self.speed = 5

    def update(self, keys, *args):
        if keys[K_LEFT] and self.rect.x > 10:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.x < 740:
            self.rect.x += self.speed
        game.screen.blit(self.image, self.rect)


class Bullet(sprite.Sprite):
    def __init__(self, xpos, ypos, direction, speed, filename, side):
        sprite.Sprite.__init__(self)
        self.image = IMAGES[filename]
        self.rect = self.image.get_rect(topleft=(xpos, ypos))
        self.speed = speed
        self.direction = direction
        self.side = side
        self.filename = filename

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)
        self.rect.y += self.speed * self.direction
        if self.rect.y < 15 or self.rect.y > 600:
            self.kill()


class Enemy(sprite.Sprite):
    def __init__(self, row, column):
        sprite.Sprite.__init__(self)
        self.row = row
        self.column = column
        self.images = []
        self.load_images()
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()

    def toggle_image(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    def update(self, *args):
        game.screen.blit(self.image, self.rect)

    def load_images(self):
        images = {0: ['1_2', '1_1'],
                  1: ['2_2', '2_1'],
                  2: ['2_2', '2_1'],
                  3: ['3_1', '3_2'],
                  4: ['3_1', '3_2'],
                  }
        img1, img2 = (IMAGES['enemy{}'.format(img_num)] for img_num in images[self.row])
        self.images.append(transform.scale(img1, (40, 35)))
        self.images.append(transform.scale(img2, (40, 35)))


class EnemiesGroup(sprite.Group):
    def __init__(self, columns, rows):
        sprite.Group.__init__(self)
        self.enemies = [[None] * columns for _ in range(rows)]
        self.columns = columns
        self.rows = rows
        self.leftAddMove = 0
        self.rightAddMove = 0
        self.moveTime = 600
        self.direction = 1
        self.rightMoves = 30
        self.leftMoves = 30
        self.moveNumber = 15
        self.timer = time.get_ticks()
        self.bottom = game.enemyPosition + ((rows - 1) * 45) + 35
        self._aliveColumns = list(range(columns))
        self._leftAliveColumn = 0
        self._rightAliveColumn = columns - 1

    def update(self, current_time):
        if current_time - self.timer > self.moveTime:
            if self.direction == 1:
                max_move = self.rightMoves + self.rightAddMove
            else:
                max_move = self.leftMoves + self.leftAddMove

            if self.moveNumber >= max_move:
                self.leftMoves = 30 + self.rightAddMove
                self.rightMoves = 30 + self.leftAddMove
                self.direction *= -1
                self.moveNumber = 0
                self.bottom = 0
                for enemy in self:
                    enemy.rect.y += ENEMY_MOVE_DOWN
                    enemy.toggle_image()
                    if self.bottom < enemy.rect.y + 35:
                        self.bottom = enemy.rect.y + 35
            else:
                velocity = 10 if self.direction == 1 else -10
                for enemy in self:
                    enemy.rect.x += velocity
                    enemy.toggle_image()
                self.moveNumber += 1
            self.timer += self.moveTime

    def add_internal(self, *sprites):
        super(EnemiesGroup, self).add_internal(*sprites)
        for s in sprites:
            self.enemies[s.row][s.column] = s

    def remove_internal(self, *sprites):
        super(EnemiesGroup, self).remove_internal(*sprites)
        for s in sprites:
            self.kill(s)
        self.update_speed()

    def is_column_dead(self, column):
        return not any(self.enemies[row][column] for row in range(self.rows))

    def random_bottom(self):
        col = choice(self._aliveColumns)
        col_enemies = (self.enemies[row - 1][col] for row in range(self.rows, 0, -1))
        return next((en for en in col_enemies if en is not None), None)

    def update_speed(self):
        if len(self) == 1:
            self.moveTime = 200
        elif len(self) <= 10:
            self.moveTime = 400

    def kill(self, enemy):
        self.enemies[enemy.row][enemy.column] = None
        is_column_dead = self.is_column_dead(enemy.column)
        if is_column_dead:
            self._aliveColumns.remove(enemy.column)

        if enemy.column == self._rightAliveColumn:
            while self._rightAliveColumn > 0 and is_column_dead:
                self._rightAliveColumn -= 1
                self.rightAddMove += 5
                is_column_dead = self.is_column_dead(self._rightAliveColumn)

        elif enemy.column == self._leftAliveColumn:
            while self._leftAliveColumn < self.columns and is_column_dead:
                self._leftAliveColumn += 1
                self.leftAddMove += 5
                is_column_dead = self.is_column_dead(self._leftAliveColumn)


class Blocker(sprite.Sprite):
    def __init__(self, size, color, row, column):
        sprite.Sprite.__init__(self)
        self.height = size
        self.width = size
        self.color = color
        self.image = Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)


class Mystery(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['mystery']
        self.image = transform.scale(self.image, (75, 35))
        self.rect = self.image.get_rect(topleft=(-80, 45))
        self.row = 5
        self.moveTime = 25000
        self.direction = 1
        self.timer = time.get_ticks()
        self.mysteryEntered = mixer.Sound(SOUND_PATH + 'mysteryentered.wav')
        self.mysteryEntered.set_volume(0.3)
        self.playSound = True

    def update(self, keys, currentTime, *args):
        resetTimer = False
        passed = currentTime - self.timer
        if passed > self.moveTime:
            if (self.rect.x < 0 or self.rect.x > 800) and self.playSound:
                self.mysteryEntered.play()
                self.playSound = False
            if self.rect.x < 840 and self.direction == 1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x += 2
                game.screen.blit(self.image, self.rect)
            if self.rect.x > -100 and self.direction == -1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x -= 2
                game.screen.blit(self.image, self.rect)
        if self.rect.x > 830:
            self.playSound = True
            self.direction = -1
            resetTimer = True
        if self.rect.x < -90:
            self.playSound = True
            self.direction = 1
            resetTimer = True
        if passed > self.moveTime and resetTimer:
            self.timer = currentTime


class EnemyExplosion(sprite.Sprite):
    def __init__(self, enemy, *groups):
        super(EnemyExplosion, self).__init__(*groups)
        self.image = transform.scale(self.get_image(enemy.row), (40, 35))
        self.image2 = transform.scale(self.get_image(enemy.row), (50, 45))
        self.rect = self.image.get_rect(topleft=(enemy.rect.x, enemy.rect.y))
        self.timer = time.get_ticks()

    @staticmethod
    def get_image(row):
        img_colors = ['purple', 'blue', 'blue', 'green', 'green']
        return IMAGES['explosion{}'.format(img_colors[row])]

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 100:
            game.screen.blit(self.image, self.rect)
        elif passed <= 200:
            game.screen.blit(self.image2, (self.rect.x - 6, self.rect.y - 6))
        elif 400 < passed:
            self.kill()


class MysteryExplosion(sprite.Sprite):
    def __init__(self, mystery, score, *groups):
        super(MysteryExplosion, self).__init__(*groups)
        self.text = Text(FONT, 20, str(score), WHITE, mystery.rect.x + 20, mystery.rect.y + 6)
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 200 or 400 < passed <= 600:
            self.text.draw(game.screen)
        elif 600 < passed:
            self.kill()


class ShipExplosion(sprite.Sprite):
    def __init__(self, ship, *groups):
        super(ShipExplosion, self).__init__(*groups)
        self.image = IMAGES['ship']
        self.rect = self.image.get_rect(topleft=(ship.rect.x, ship.rect.y))
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if 300 < passed <= 600:
            game.screen.blit(self.image, self.rect)
        elif 900 < passed:
            self.kill()


class Life(sprite.Sprite):
    def __init__(self, xpos, ypos):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['ship']
        self.image = transform.scale(self.image, (23, 23))
        self.rect = self.image.get_rect(topleft=(xpos, ypos))

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class Text(object):
    def __init__(self, textFont, size, message, color, xpos, ypos):
        self.font = font.Font(textFont, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)


class Pause:
    def __init__(self):
        self.paused = False
        font = pygame.font.Font(FONT, 48)
        self.pause_text = font.render("Pause", True, WHITE)

    def toggle_pause(self):
        self.paused = not self.paused

    def draw(self, screen):
        if self.paused:
            overlay = pygame.Surface((800, 600))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            text_rect = self.pause_text.get_rect(center=(400, 300))
            screen.blit(self.pause_text, text_rect)

    def handle_event(self, event):
        if event.type == KEYDOWN:
            if event.key == K_p:
                self.toggle_pause()


class SpaceInvaders(object):
    def __init__(self):
        mixer.pre_init(44100, -16, 1, 4096)
        init()
        self.clock = time.Clock()
        self.caption = display.set_caption('Space Invaders')
        self.screen = screen
        self.backgrounds = [
            image.load(IMAGE_PATH + "background.jpg").convert(),
            image.load(IMAGE_PATH + "background1.jpg").convert(),
            image.load(IMAGE_PATH + "background2.jpg").convert(),
        ]
        self.current_background_image_index = 0
        self.background = self.backgrounds[self.current_background_image_index]
        self.startGame = False
        self.mainScreen = True
        self.settingsScreen = False
        self.gameOver = False
        self.pause = Pause()
        self.enemyPosition = ENEMY_DEFAULT_POSITION
        self.shipAlive = False
        self.wave = 1
        self.volume = 0.5
        self.difficulty = 1

        self.titleText = Text(FONT, 50, 'Space Invaders', WHITE, 164, 155)
        self.highScoreText = Text(FONT, 25, 'High Scores', WHITE, 300, 50)
        self.gameOverText = Text(FONT, 50, 'Game Over', WHITE, 250, 270)
        self.nextRoundText = Text(FONT, 50, 'Next Round', WHITE, 240, 270)
        self.scoreText = Text(FONT, 20, 'Score', WHITE, 5, 5)
        self.livesText = Text(FONT, 20, 'Lives ', WHITE, 640, 5)

        self.life1 = Life(715, 3)
        self.life2 = Life(742, 3)
        self.life3 = Life(769, 3)
        self.livesGroup = sprite.Group(self.life1, self.life2, self.life3)

        self.startButton = Button("Start", (300, 300), (200, 60), self.start_game)
        self.settingsButton = Button("Settings", (300, 380), (200, 60), self.show_settings)
        self.exitButton = Button("Exit", (300, 460), (200, 60), sys.exit)
        self.backButton = Button("Back", (300, 460), (150, 60), self.back_to_menu)
        self.volumeUpButton = Button("+", (450, 300), (50, 50), self.increase_volume)
        self.volumeDownButton = Button("-", (350, 300), (50, 50), self.decrease_volume)
        self.difficultyUpButton = Button("+", (450, 360), (50, 50), self.increase_difficulty)
        self.difficultyDownButton = Button("-", (350, 360), (50, 50), self.decrease_difficulty)

        self.backgroundNextButton = Button(">", (450, 420), (50, 50), self.next_background)
        self.backgroundPrevButton = Button("<", (350, 420), (50, 50), self.prev_background)

        self.buttons = [self.startButton, self.settingsButton, self.exitButton]

    def next_background(self):
        self.current_background_image_index = (self.current_background_image_index + 1) % len(self.backgrounds)
        self.background = self.backgrounds[self.current_background_image_index]

    def prev_background(self):
        self.current_background_image_index = (self.current_background_image_index - 1) % len(self.backgrounds)
        self.background = self.backgrounds[self.current_background_image_index]

    def load_scores(self):
        try:
            with open('scores.txt', 'r') as f:
                return json.load(f)
        except:
            return [0, 0, 0, 0, 0]

    def save_scores(self, score):
        scores = self.load_scores()
        scores.append(score)
        scores = sorted(scores, reverse=True)[:5]
        with open('scores.txt', 'w') as f:
            json.dump(scores, f)
        return scores

    def reset(self, score):
        self.player = Ship()
        self.playerGroup = sprite.Group(self.player)
        self.explosionsGroup = sprite.Group()
        self.bullets = sprite.Group()
        self.mysteryShip = Mystery()
        self.mysteryGroup = sprite.Group(self.mysteryShip)
        self.enemyBullets = sprite.Group()
        self.make_enemies()
        self.allSprites = sprite.Group(self.player, self.enemies, self.livesGroup, self.mysteryShip)
        self.keys = key.get_pressed()
        self.timer = time.get_ticks()
        self.noteTimer = time.get_ticks()
        self.shipTimer = time.get_ticks()
        self.score = score
        self.create_audio()
        self.makeNewShip = False
        self.shipAlive = True
        self.waveText = Text(FONT, 20, f'Wave {self.wave}', WHITE, 350, 5)
        self.background = self.backgrounds[self.current_background_image_index]

    def make_blockers(self, number):
        blockerGroup = sprite.Group()
        for row in range(4):
            for column in range(9):
                blocker = Blocker(10, GREEN, row, column)
                blocker.rect.x = 50 + (200 * number) + (column * blocker.width)
                blocker.rect.y = BLOCKERS_POSITION + (row * blocker.height)
                blockerGroup.add(blocker)
        return blockerGroup

    def create_audio(self):
        self.sounds = {}
        for sound_name in ['shoot', 'shoot2', 'invaderkilled', 'mysterykilled', 'shipexplosion']:
            self.sounds[sound_name] = mixer.Sound(SOUND_PATH + '{}.wav'.format(sound_name))
            self.sounds[sound_name].set_volume(self.volume)
        self.musicNotes = [mixer.Sound(SOUND_PATH + '{}.wav'.format(i)) for i in range(4)]
        for sound in self.musicNotes:
            sound.set_volume(self.volume)
        self.noteIndex = 0

    def play_main_music(self, currentTime):
        if currentTime - self.noteTimer > self.enemies.moveTime:
            self.note = self.musicNotes[self.noteIndex]
            if self.noteIndex < 3:
                self.noteIndex += 1
            else:
                self.noteIndex = 0
            self.note.play()
            self.noteTimer += self.enemies.moveTime

    @staticmethod
    def should_exit(evt):
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    def start_game(self):
        self.allBlockers = sprite.Group(self.make_blockers(0), self.make_blockers(1),
                                        self.make_blockers(2), self.make_blockers(3))
        self.livesGroup.add(self.life1, self.life2, self.life3)
        self.reset(0)
        self.startGame = True
        self.mainScreen = False
        self.settingsScreen = False

    def show_settings(self):
        self.settingsScreen = True
        self.mainScreen = False

    def back_to_menu(self):
        self.mainScreen = True
        self.settingsScreen = False

    def increase_volume(self):
        if self.volume < 1.0:
            self.volume += 0.1
            for sound in self.sounds.values():
                sound.set_volume(self.volume)
            for note in self.musicNotes:
                note.set_volume(self.volume)

    def decrease_volume(self):
        if self.volume > 0.0:
            self.volume -= 0.1
            for sound in self.sounds.values():
                sound.set_volume(self.volume)
            for note in self.musicNotes:
                note.set_volume(self.volume)

    def increase_difficulty(self):
        if self.difficulty < 3:
            self.difficulty += 1

    def decrease_difficulty(self):
        if self.difficulty > 1:
            self.difficulty -= 1

    def check_input(self):
        self.keys = key.get_pressed()
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            self.pause.handle_event(e)

            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                pos = pygame.mouse.get_pos()
                if self.mainScreen:
                    for button in self.buttons:
                        button.click()
                elif self.settingsScreen:
                    self.backButton.click()
                    self.volumeUpButton.click()
                    self.volumeDownButton.click()
                    self.difficultyUpButton.click()
                    self.difficultyDownButton.click()
                    self.backgroundNextButton.click()
                    self.backgroundPrevButton.click()

            if e.type == KEYDOWN:
                if e.key == K_SPACE and self.startGame and self.shipAlive and not self.pause.paused:
                    if len(self.bullets) == 0:
                        if self.score < 1000:
                            bullet = Bullet(self.player.rect.x + 23, self.player.rect.y + 5, -1, 15, 'laser', 'center')
                            self.bullets.add(bullet)
                            self.allSprites.add(self.bullets)
                            self.sounds['shoot'].play()
                        else:
                            leftbullet = Bullet(self.player.rect.x + 8, self.player.rect.y + 5, -1, 15, 'laser', 'left')
                            rightbullet = Bullet(self.player.rect.x + 38, self.player.rect.y + 5, -1, 15, 'laser',
                                                 'right')
                            self.bullets.add(leftbullet)
                            self.bullets.add(rightbullet)
                            self.allSprites.add(self.bullets)
                            self.sounds['shoot2'].play()

    def make_enemies(self):
        enemies = EnemiesGroup(10, 5)
        for row in range(5):
            for column in range(10):
                enemy = Enemy(row, column)
                enemy.rect.x = 157 + (column * 50)
                enemy.rect.y = self.enemyPosition + (row * 45)
                enemies.add(enemy)
        self.enemies = enemies
        self.enemies.moveTime = 600 // self.difficulty

    def make_enemies_shoot(self):
        if (time.get_ticks() - self.timer) > (700 // self.difficulty) and self.enemies:
            enemy = self.enemies.random_bottom()
            self.enemyBullets.add(Bullet(enemy.rect.x + 14, enemy.rect.y + 20, 1, 5, 'enemylaser', 'center'))
            self.allSprites.add(self.enemyBullets)
            self.timer = time.get_ticks()

    def calculate_score(self, row):
        scores = {0: 30, 1: 20, 2: 20, 3: 10, 4: 10, 5: choice([50, 100, 150, 300])}
        score = scores[row]
        self.score += score
        return score

    def check_collisions(self):
        sprite.groupcollide(self.bullets, self.enemyBullets, True, True)
        for enemy in sprite.groupcollide(self.enemies, self.bullets, True, True).keys():
            self.sounds['invaderkilled'].play()
            self.calculate_score(enemy.row)
            EnemyExplosion(enemy, self.explosionsGroup)
            self.gameTimer = time.get_ticks()
        for mystery in sprite.groupcollide(self.mysteryGroup, self.bullets, True, True).keys():
            mystery.mysteryEntered.stop()
            self.sounds['mysterykilled'].play()
            score = self.calculate_score(mystery.row)
            MysteryExplosion(mystery, score, self.explosionsGroup)
            newShip = Mystery()
            self.allSprites.add(newShip)
            self.mysteryGroup.add(newShip)
        for player in sprite.groupcollide(self.playerGroup, self.enemyBullets, True, True).keys():
            if self.life3.alive():
                self.life3.kill()
            elif self.life2.alive():
                self.life2.kill()
            elif self.life1.alive():
                self.life1.kill()
            else:
                self.gameOver = True
                self.startGame = False
            self.sounds['shipexplosion'].play()
            ShipExplosion(player, self.explosionsGroup)
            self.makeNewShip = True
            self.shipTimer = time.get_ticks()
            self.shipAlive = False
        if self.enemies.bottom >= 540:
            sprite.groupcollide(self.enemies, self.playerGroup, True, True)
            if not self.player.alive() or self.enemies.bottom >= 600:
                self.gameOver = True
                self.startGame = False
        sprite.groupcollide(self.bullets, self.allBlockers, True, True)
        sprite.groupcollide(self.enemyBullets, self.allBlockers, True, True)
        if self.enemies.bottom >= BLOCKERS_POSITION:
            sprite.groupcollide(self.enemies, self.allBlockers, False, True)

    def create_new_ship(self, createShip, currentTime):
        if createShip and (currentTime - self.shipTimer > 900):
            self.player = Ship()
            self.allSprites.add(self.player)
            self.playerGroup.add(self.player)
            self.makeNewShip = False
            self.shipAlive = True

    def create_game_over(self, currentTime):
        self.screen.blit(self.background, (0, 0))
        scores = self.save_scores(self.score)
        passed = currentTime - self.timer

        if passed < 750:
            self.gameOverText.draw(self.screen)
        elif 750 < passed < 1500:
            self.screen.blit(self.background, (0, 0))
            self.highScoreText.draw(self.screen)
            for i, score in enumerate(scores):
                score_text = Text(FONT, 20, f"{i + 1}. {score}", WHITE, 350, 100 + i * 30)
                score_text.draw(self.screen)
        elif 1500 < passed < 2250:
            self.gameOverText.draw(self.screen)
        elif 2250 < passed < 2750:
            self.screen.blit(self.background, (0, 0))
        elif passed > 3000:
            self.mainScreen = True
            self.gameOver = False
            self.wave = 1

    def main(self):
        while True:
            currentTime = time.get_ticks()
            self.check_input()
            mouse_pos = pygame.mouse.get_pos()

            if self.pause.paused:
                self.screen.blit(self.background, (0, 0))
                if self.startGame:
                    self.allBlockers.update(self.screen)
                    self.scoreText2 = Text(FONT, 20, str(self.score), GREEN, 85, 5)
                    self.scoreText.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.waveText.draw(self.screen)
                    self.livesText.draw(self.screen)
                    self.allSprites.update(self.keys, currentTime)
                    self.explosionsGroup.update(currentTime)
                self.pause.draw(self.screen)
                display.update()
                self.clock.tick(60)
                continue

            if self.mainScreen:
                self.screen.blit(self.background, (0, 0))
                self.titleText.draw(self.screen)
                for button in self.buttons:
                    button.check_hover(mouse_pos)
                    button.draw(self.screen)

            elif self.settingsScreen:
                self.screen.blit(self.background, (0, 0))
                volume_text = Text(FONT, 10, f"Volume: {int(self.volume * 100)}%", WHITE, 200, 310)
                difficulty_text = Text(FONT, 10, f"Difficulty: {self.difficulty}", WHITE, 200, 370)
                volume_text.draw(self.screen)
                difficulty_text.draw(self.screen)
                self.backButton.check_hover(mouse_pos)
                self.backButton.draw(self.screen)
                self.volumeUpButton.check_hover(mouse_pos)
                self.volumeUpButton.draw(self.screen)
                self.volumeDownButton.check_hover(mouse_pos)
                self.volumeDownButton.draw(self.screen)
                self.difficultyUpButton.check_hover(mouse_pos)
                self.difficultyUpButton.draw(self.screen)
                self.difficultyDownButton.check_hover(mouse_pos)
                self.difficultyDownButton.draw(self.screen)
                self.backgroundNextButton.check_hover(mouse_pos)
                self.backgroundNextButton.draw(self.screen)

            elif self.startGame:
                if not self.enemies and not self.explosionsGroup:
                    if currentTime - self.gameTimer < 3000:
                        self.screen.blit(self.background, (0, 0))
                        self.scoreText2 = Text(FONT, 20, str(self.score), GREEN, 85, 5)
                        self.scoreText.draw(self.screen)
                        self.scoreText2.draw(self.screen)
                        self.waveText.draw(self.screen)
                        self.nextRoundText.draw(self.screen)
                        self.livesText.draw(self.screen)
                        self.livesGroup.update()
                    elif currentTime - self.gameTimer > 3000:
                        self.wave += 1
                        self.waveText = Text(FONT, 20, f'Wave {self.wave}', WHITE, 350, 5)
                        self.enemyPosition += ENEMY_MOVE_DOWN
                        self.reset(self.score)
                        self.gameTimer += 3000
                else:
                    self.screen.blit(self.background, (0, 0))
                    self.play_main_music(currentTime)
                    self.allBlockers.update(self.screen)
                    self.scoreText2 = Text(FONT, 20, str(self.score), GREEN, 85, 5)
                    self.scoreText.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.waveText.draw(self.screen)
                    self.livesText.draw(self.screen)
                    self.enemies.update(currentTime)
                    self.allSprites.update(self.keys, currentTime)
                    self.explosionsGroup.update(currentTime)
                    self.check_collisions()
                    self.create_new_ship(self.makeNewShip, currentTime)
                    self.make_enemies_shoot()

            elif self.gameOver:
                self.enemyPosition = ENEMY_DEFAULT_POSITION
                self.create_game_over(currentTime)

            display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    game = SpaceInvaders()
    game.main()
