import pygame
import sys
import math
import random

pygame.init()

# настройки экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Космический Курьер")

# цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# настройки игры
FPS = 60
clock = pygame.time.Clock()

# шрифты
font_large = pygame.font.SysFont('Arial', 48)
font_medium = pygame.font.SysFont('Arial', 36)
font_small = pygame.font.SysFont('Arial', 24)

# фоновая музыка
try:
    pygame.mixer.music.load('assets/sounds/background.mp3')
    pygame.mixer.music.set_volume(0.5)  #громкость 50%
    pygame.mixer.music.play(-1)  #бесконечное повторение
except pygame.error as e:
    print(f"Не удалось загрузить музыку: {e}")


# класс кнопки для меню
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=10)

        text_surf = font_medium.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False


# класс корабля игрока
class Spaceship(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.color = WHITE
        self.create_image()
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.speed = 0
        self.max_speed = 5
        self.acceleration = 0.1
        self.rotation = 0
        self.velocity = pygame.math.Vector2(0, 0)
        self.position = pygame.math.Vector2(self.rect.center)
        self.has_cargo = False

    def create_image(self):
        self.image = pygame.Surface((30, 20), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, self.color, [(0, 0), (30, 10), (0, 20)])
        self.original_image = self.image.copy()

    def set_color(self, color):
        self.color = color
        self.create_image()

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.rotation += 5
        if keys[pygame.K_d]:
            self.rotation -= 5

        if keys[pygame.K_w]:
            self.speed += self.acceleration
            if self.speed > self.max_speed:
                self.speed = self.max_speed
        else:
            self.speed -= self.acceleration / 2
            if self.speed < 0:
                self.speed = 0

        self.image = pygame.transform.rotate(self.original_image, self.rotation)
        self.rect = self.image.get_rect(center=self.rect.center)

        angle_rad = math.radians(self.rotation)
        direction = pygame.math.Vector2(math.cos(angle_rad), -math.sin(angle_rad))
        self.velocity = direction * self.speed
        self.position += self.velocity
        self.rect.center = self.position

        # проверка границ экрана

        if self.rect.left > WIDTH:
            self.rect.right = 0
            self.position.x = self.rect.centerx
        elif self.rect.right < 0:
            self.rect.left = WIDTH
            self.position.x = self.rect.centerx
        if self.rect.top > HEIGHT:
            self.rect.bottom = 0
            self.position.y = self.rect.centery
        elif self.rect.bottom < 0:
            self.rect.top = HEIGHT
            self.position.y = self.rect.centery


# класс планеты
class Planet(pygame.sprite.Sprite):
    def __init__(self, x, y, radius, color, gravity_radius, gravity_force):
        super().__init__()
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=(x, y))
        self.radius = radius
        self.gravity_radius = gravity_radius
        self.gravity_force = gravity_force
        self.has_cargo = False  # для планеты с флагом
        self.is_target = False  # планета — цель доставки?

    def apply_gravity(self, ship):
        # расчет расстояния между кораблем и планетой
        distance_vec = pygame.math.Vector2(self.rect.center) - ship.position
        distance = distance_vec.length()

        # если корабль в зоне гравитации
        if distance < self.gravity_radius:
            # нормализованный вектор направления
            if distance > 0:
                direction = distance_vec.normalize()
            else:
                direction = pygame.math.Vector2(1, 0)

            # расчет силы гравитации (обратно пропорционально расстоянию)
            force = self.gravity_force * (1 - distance / self.gravity_radius)
            ship.velocity += direction * force


# класс черной дыры
class BlackHole(Planet):
    def __init__(self, x, y):
        super().__init__(x, y, 20, BLACK, 200, 0.3)
        self.critical_distance = 50  # критическое расстояние для бонуса
        # анимация свечения
        self.glow_size = 0
        self.glow_growing = True

    def update(self):
        # анимация свечения
        if self.glow_growing:
            self.glow_size += 0.5
            if self.glow_size >= 10:
                self.glow_growing = False
        else:
            self.glow_size -= 0.5
            if self.glow_size <= 0:
                self.glow_growing = True

    def draw(self, surface):
        # рисуем свечение
        glow_surf = pygame.Surface((self.radius * 2 + self.glow_size * 2,
                                    self.radius * 2 + self.glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (100, 100, 255, 50),
                           (self.radius + self.glow_size, self.radius + self.glow_size),
                           self.radius + self.glow_size)
        surface.blit(glow_surf, (self.rect.x - self.glow_size, self.rect.y - self.glow_size))

        # рисуем саму черную дыру
        surface.blit(self.image, self.rect)

    def apply_gravity(self, ship):
        super().apply_gravity(ship)
        # проверка на критическое расстояние для бонуса
        distance_vec = pygame.math.Vector2(self.rect.center) - ship.position
        distance = distance_vec.length()

        if distance < self.critical_distance and distance > self.radius:
            # здесь будет логика начисления бонуса (+10 очков)
            pass


# класс груза
class Cargo(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((15, 15))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))


# класс бустера
class Booster(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(center=(x, y))


# игровой класс
class Game:
    def __init__(self):
        self.state = "menu"  # menu, game, game_over
        self.create_menu()
        self.reset()

    def create_menu(self):
        # создаем кнопки меню
        button_width, button_height = 200, 50
        center_x = WIDTH // 2 - button_width // 2

        self.start_button = Button(center_x, 250, button_width, button_height,
                                   "Начать игру", BLUE, PURPLE)
        self.quit_button = Button(center_x, 350, button_width, button_height,
                                  "Выход", RED, PURPLE)

    def reset(self):
        # группы спрайтов
        self.all_sprites = pygame.sprite.Group()
        self.planets = pygame.sprite.Group()
        self.blackholes = pygame.sprite.Group()
        self.cargos = pygame.sprite.Group()
        self.boosters = pygame.sprite.Group()

        # создание корабля
        self.ship = Spaceship()
        self.all_sprites.add(self.ship)

        # игровые параметры
        self.lives = 3
        self.score = 0
        self.level = 1
        self.game_over = False
        self.cargo_delivered = False

        # создание уровня
        self.create_level()

    def create_level(self):
        # очистка предыдущих объектов
        self.planets.empty()
        self.blackholes.empty()
        self.cargos.empty()
        self.boosters.empty()

        # количество объектов зависит от уровня
        num_planets = 2 + self.level
        num_blackholes = 1 + self.level // 2

        # создание планет
        for _ in range(num_planets):
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)
            radius = random.randint(20, 40)
            color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            planet = Planet(x, y, radius, color, radius * 4, 0.1)
            self.planets.add(planet)
            self.all_sprites.add(planet)

        # одна планета с флагом (цель доставки)
        if self.planets:
            self.target_planet = random.choice(self.planets.sprites())
            self.target_planet.has_cargo = True
            # добавляем флаг на планету
            pygame.draw.circle(self.target_planet.image, RED,
                               (self.target_planet.radius, self.target_planet.radius // 2), 5)
            self.target_planet.is_target = True  # пометили как целевую

        # создание черных дыр
        for _ in range(num_blackholes):
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)
            blackhole = BlackHole(x, y)
            self.blackholes.add(blackhole)
            self.all_sprites.add(blackhole)

        # создание груза
        while True:
            x = random.randint(100, WIDTH - 100)
            y = random.randint(100, HEIGHT - 100)
            # проверяем, чтобы груз не появился слишком близко к целевой планете
            if self.planets and pygame.math.Vector2(x, y).distance_to(
                    pygame.math.Vector2(self.target_planet.rect.center)) > 150:
                break

        cargo = Cargo(x, y)
        self.cargos.add(cargo)
        self.all_sprites.add(cargo)

        # создание бустеров (1 на уровень)
        booster = Booster(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50))
        self.boosters.add(booster)
        self.all_sprites.add(booster)
        self.all_sprites.add(self.ship)  # убедимся, что корабль снова в группе

    def update(self):
        if self.state != "game":
            return

        # обновление всех спрайтов
        self.all_sprites.update()

        # применение гравитации
        for planet in self.planets:
            planet.apply_gravity(self.ship)

        for blackhole in self.blackholes:
            blackhole.apply_gravity(self.ship)

        # проверка столкновений с планетами и черными дырами
        planet_collisions = pygame.sprite.spritecollide(self.ship, self.planets, False)
        blackhole_collisions = pygame.sprite.spritecollide(self.ship, self.blackholes, False)

        crashed = False

        # Столкновение с планетами
        for planet in planet_collisions:
            if not (planet.is_target and self.ship.has_cargo):
                crashed = True

        # Столкновение с черными дырами (всегда снимает жизнь)
        if blackhole_collisions:
            crashed = True

        if crashed:
            self.lives -= 1
            if self.lives <= 0:
                self.state = "game_over"
            else:
                # респавн
                self.ship.position = pygame.math.Vector2(WIDTH // 2, HEIGHT // 2)
                self.ship.velocity = pygame.math.Vector2(0, 0)
                self.ship.speed = 0
                self.ship.has_cargo = False

        # проверка сбора груза
        if not self.ship.has_cargo:
            cargo_collision = pygame.sprite.spritecollide(self.ship, self.cargos, True)
            if cargo_collision:
                self.ship.has_cargo = True
                self.ship.set_color(YELLOW)

        # проверка доставки груза на планету с флагом
        if self.ship.has_cargo and self.target_planet:
            if pygame.sprite.collide_rect(self.ship, self.target_planet):
                self.score += 3
                self.ship.has_cargo = False

                # возвращаем обычный цвет корабля
                self.ship.set_color(WHITE)
                self.ship.has_cargo = False

                # удаляем все объекты, кроме корабля
                for sprite in self.all_sprites:
                    if sprite != self.ship:
                        sprite.kill()

                self.planets.empty()
                self.blackholes.empty()
                self.cargos.empty()
                self.boosters.empty()
                self.target_planet = None

                # переход на следующий уровень
                self.level += 1
                if self.level > 5:
                    self.state = "game_over"
                else:
                    self.create_level()

        # проверка сбора бустера
        booster_collision = pygame.sprite.spritecollide(self.ship, self.boosters, True)
        if booster_collision:
            self.score += 5
            # увелич макс скорость на 1
            self.ship.max_speed += 1

    def draw(self):
        # черный фон (космос)
        screen.fill(BLACK)

        # рисуем звезды (просто случайные точки)
        for _ in range(100):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            brightness = random.randint(100, 255)
            pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), 1)

        if self.state == "menu":
            self.draw_menu()
        elif self.state == "game":
            self.draw_game()
        elif self.state == "game_over":
            self.draw_game()
            self.draw_game_over()

    def draw_menu(self):
        # заголовок игры
        title = font_large.render("КОСМИЧЕСКИЙ КУРЬЕР", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        # инструкция
        instruction = font_small.render("Доставьте груз на планету с красным флагом", True, WHITE)
        screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, 180))

        # кнопки
        self.start_button.draw(screen)
        self.quit_button.draw(screen)

    def draw_game(self):
        # рисуем все спрайты
        for sprite in self.all_sprites:
            if isinstance(sprite, BlackHole):
                sprite.draw(screen)
            else:
                screen.blit(sprite.image, sprite.rect)

        # интерфейс
        lives_text = font_medium.render(f'Жизни: {self.lives}', True, WHITE)
        score_text = font_medium.render(f'Очки: {self.score}', True, WHITE)
        level_text = font_medium.render(f'Уровень: {self.level}', True, WHITE)
        cargo_text = font_medium.render(f'Груз: {"ЕСТЬ" if self.ship.has_cargo else "НЕТ"}', True, YELLOW)

        screen.blit(lives_text, (10, 10))
        screen.blit(score_text, (10, 50))
        screen.blit(level_text, (10, 90))
        screen.blit(cargo_text, (10, 130))

    def draw_game_over(self):
        # затемнение экрана
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # текст Game Over
        if self.level > 5:
            game_over_text = font_large.render('ПОБЕДА!', True, GREEN)
        else:
            game_over_text = font_large.render('ИГРА ОКОНЧЕНА', True, RED)

        score_text = font_medium.render(f'Ваш счет: {self.score}', True, WHITE)
        restart_text = font_medium.render('Нажмите R для рестарта', True, WHITE)
        menu_text = font_medium.render('Нажмите M для выхода в меню', True, WHITE)

        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 30))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 30))
        screen.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, HEIGHT // 2 + 80))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "game":
                        self.state = "menu"
                    else:
                        return False

                if event.key == pygame.K_r and self.state == "game_over":
                    self.reset()
                    self.state = "game"

                if event.key == pygame.K_m and self.state == "game_over":
                    self.state = "menu"

            if event.type == pygame.MOUSEMOTION and self.state == "menu":
                mouse_pos = pygame.mouse.get_pos()
                self.start_button.check_hover(mouse_pos)
                self.quit_button.check_hover(mouse_pos)

            if event.type == pygame.MOUSEBUTTONDOWN and self.state == "menu":
                mouse_pos = pygame.mouse.get_pos()
                if self.start_button.is_clicked(mouse_pos, event):
                    self.reset()
                    self.state = "game"
                elif self.quit_button.is_clicked(mouse_pos, event):
                    return False

        return True


# основной игровой цикл
def main():
    game = Game()
    running = True

    while running:
        running = game.handle_events()
        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
