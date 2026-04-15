import pygame
import numpy as np
import sys

SZEROKOSC = 1200 
WYSOKOSC = 700


class VirtualCamera:
    def __init__(self):

        self.pozycja = np.array([0.0, 0.0, 0.0, 1.0])

        # lewo / prawo
        self.obrot = 0

        # góra / dół
        self.nachylenie = 0

        # przechylenie na boki 
        self.przechylenie = 0   

        self.f = 600

    def macierz_widoku(self):

        # macierz translacji 
        t_mat = np.array([
            [1, 0, 0, -self.pozycja[0]],
            [0, 1, 0, -self.pozycja[1]],
            [0, 0, 1, -self.pozycja[2]],
            [0, 0, 0, 1]])

        # macierze rotacji
        ro = self.obrot
        r_obrot = np.array([
            [np.cos(ro), 0, np.sin(ro), 0],
            [0, 1, 0, 0],
            [-np.sin(ro), 0, np.cos(ro), 0],
            [0, 0, 0, 1]])

        rn = self.nachylenie
        r_nachylenie = np.array([
            [1, 0, 0, 0],
            [0, np.cos(rn), -np.sin(rn), 0],
            [0, np.sin(rn), np.cos(rn), 0],
            [0, 0, 0, 1]])

        rp = self.przechylenie
        r_przechylenie = np.array([
            [np.cos(rp), -np.sin(rp), 0, 0],
            [np.sin(rp), np.cos(rp), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]])

        # połączona macierz widoku
        return r_przechylenie @ r_nachylenie @ r_obrot @ t_mat

    def project(self, punkt_3d):

        x, y, z, w = punkt_3d
        
        # nie rysujemy obiektów za kamerą
        if z <= 0.1:
            return None 
        
        # parametr f modyfikuje kąt widzenia
        x_2d = (x * self.f) / z + SZEROKOSC // 2
        y_2d = (-y * self.f) / z + WYSOKOSC // 2
        
        return int(x_2d), int(y_2d)

def wczytaj_obiekt(filename):

    wezly = []
    krawedzie = []

    try:
        with open(filename, 'r') as f:
            for line in f:

                parts = line.split()
                
                if not parts:
                    continue

                if parts[0] == 'w':
                # w id x y z -> dodajemy 1 dla współrzędnych jednorodnych 
                    wezly.append([float(parts[2]), float(parts[3]), float(parts[4]), 1.0])

                elif parts[0] == 'k':
                # krawedzie figur 
                    index = [int(i) for i in parts[1:]]

                    for i in range(len(index)):
                        krawedzie.append((index[i - 1], index[i]))

        return np.array(wezly), krawedzie

    except FileNotFoundError:
        print("Brak pliku!")
        return None

def main():

    pygame.init()

    screen = pygame.display.set_mode((SZEROKOSC, WYSOKOSC))
    clock = pygame.time.Clock()
    camera = VirtualCamera()
    
    wezly, krawedzie = wczytaj_obiekt('data/scena.txt')

    while True:

        screen.fill((255, 255, 255))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()

        dx, dy, dz = 0.0, 0.0, 0.0

        predkosc_ruchu = 0.1

        if keys[pygame.K_w]: 
            dz += predkosc_ruchu  # przód
        if keys[pygame.K_s]: 
            dz -= predkosc_ruchu  # tył
        if keys[pygame.K_a]: 
            dx -= predkosc_ruchu  # lewo
        if keys[pygame.K_d]: 
            dx += predkosc_ruchu # prawo
        if keys[pygame.K_SPACE]: 
            dy += predkosc_ruchu # góra
        if keys[pygame.K_LCTRL]: 
            dy -= predkosc_ruchu # dół

        '''
        if abs(dx) > 0 or abs(dy) > 0 or abs(dz) > 0:
            
            view_mat = camera.macierz_widoku()
            
            rot_mat_inv = view_mat[:3, :3].T

            #  wektor przemieszczenia
            lokalny_kierunek = np.array([dx, dy, dz])

            globalny_kierunek = rot_mat_inv @ lokalny_kierunek

            camera.pozycja[0] += globalny_kierunek[0]
            camera.pozycja[1] += globalny_kierunek[1]
            camera.pozycja[2] += globalny_kierunek[2]
        '''
        # ruch w globalnym układzie
        camera.pozycja[0] += dx
        camera.pozycja[1] += dy
        camera.pozycja[2] += dz

        predkosc_obrotu = 0.01

        if keys[pygame.K_LEFT]: 
            camera.obrot += predkosc_obrotu
        if keys[pygame.K_RIGHT]: 
            camera.obrot -= predkosc_obrotu

        if keys[pygame.K_q]: 
            camera.przechylenie -= predkosc_obrotu
        if keys[pygame.K_e]: 
            camera.przechylenie += predkosc_obrotu

        if keys[pygame.K_UP]: 
            camera.nachylenie += predkosc_obrotu
        if keys[pygame.K_DOWN]: 
            camera.nachylenie -= predkosc_obrotu
        
        # ZOOM (zmiana parametru f)
        zoom = 5
        
        if keys[pygame.K_EQUALS]: 
            camera.f += zoom
        if keys[pygame.K_MINUS]: 
            camera.f -= zoom

        # renderowanie 
        macierz_widoku = camera.macierz_widoku()
        
        # transformacja wszystkich punktów do układu kamery 
        przetransformowane_wezly = [macierz_widoku @ w for w in wezly]
        
        # rzutowanie na 2D i rysowanie krawędzi 
        zrzutowane_punkty = {}
        for index, wezel_kamera in enumerate(przetransformowane_wezly):
            punkt_2d = camera.project(wezel_kamera)
            if punkt_2d:
                zrzutowane_punkty[index] = punkt_2d

        for index_poczatkowy, index_koncowy in krawedzie:
            if index_poczatkowy in zrzutowane_punkty and index_koncowy in zrzutowane_punkty:

                pygame.draw.line(screen, (0, 0, 0), zrzutowane_punkty[index_poczatkowy], zrzutowane_punkty[index_koncowy], 2)

        pygame.display.flip()

        clock.tick(60) #fps

if __name__ == "__main__":
    main()