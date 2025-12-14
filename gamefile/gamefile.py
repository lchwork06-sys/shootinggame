from tkinter import *
import time
import random
import pygame
import os

BASE_DIR=os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

class Bullet:
    def __init__(self, canvas, x, y, dx, dy, team, image=None, color=None):
        self.c = canvas  # 캔버스 self.c로 저장
        self.dx = dx     # x축 이동 속도
        self.dy = dy     # y축 이동 속도
        self.team = team # 0:플레이어 총알 1:적 총알
        
        if image:
            self.id = self.c.create_image(x, y, image=image, tags="p_bullet")
        else:
            self.id = self.c.create_oval(x-5, y, x+5, y+10, fill=color, tags="e_bullet")
    
    # 총알을 이동시키는 함수
    def move(self):
        self.c.move(self.id, self.dx, self.dy) # 현재 위치에서 dx, dy만큼 이동
    
    # 현재 총알의 좌표를 알아내는 함수
    def coords(self):
        return self.c.coords(self.id)
    
    # 총알을 화면에서 지우는 함수
    def delete(self):
        self.c.delete(self.id)

class Enemy:
    def __init__(self, canvas, x, y, kind, image_kind):
        self.c = canvas
        self.kind = kind # 0:일반 적, 1:보스
        
        if kind == 1:
            self.hp = 30
            self.boss = image_kind
        else:
            self.hp = 1
            self.normal_enemy = image_kind
        
        # 적 생성 및 이동 속도 설정
        if kind == 1:
            self.id = self.c.create_image(x, y, image=self.boss, tags="boss")
            self.dx = 3 # 보스는 옆으로
        else:
            self.id = self.c.create_image(x, y, image=self.normal_enemy, tags="enemy")
            self.dx = 0 # 일반 적은 아래로
            
    def move(self):
        if self.kind == 1: # 보스일 때의 움직임
            self.c.move(self.id, self.dx, 0)
            
            # bbox는 이미지의 테두리 상자(좌,상,우,하) 좌표를 가져옵니다.
            pos = self.c.bbox(self.id)
            # 화면 왼쪽(0)이나 오른쪽(600) 끝에 닿으면 방향 반대로 전환
            if pos and (pos[0] <= 0 or pos[2] >= 600):
                self.dx *= -1 
        else: # 일반 적은 계속 아래로(y축 +2) 이동
            self.c.move(self.id, 0, 2)

class ShootingGame:
    def __init__(self):
        self.window = Tk() # 윈도우 창 생성
        self.window.title("ShootingGame")
        self.window.geometry("600x800")
        self.window.resizable(0, 0) # 창 크기 조절 불가능하게 설정
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.c = Canvas(self.window, bg="black", width=600, height=800)
        self.c.pack(expand=True, fill=BOTH)
        
        # 눌린 키들을 저장할 집합, 동시에 여러 키를 누르는 것 처리 위해 사용
        self.keys = set()
        self.window.bind("<KeyPress>", self.key_down)
        self.window.bind("<KeyRelease>", self.key_up)
        
        self.normal_enemy_img = PhotoImage(file="image/normal_enemy.png.png")
        self.player_img = PhotoImage(file="image/ship.png.png").zoom(2)
        self.missile_img = PhotoImage(file="image/missile.png.png").zoom(2)
        self.boss_img = PhotoImage(file="image/boss.png.png")
        self.item_img = PhotoImage(file="image/item.png.png")
            
        # 플레이어 생성
        self.player = self.c.create_image(300, 700, image=self.player_img, tags="me")
        
        # 게임 변수 초기화
        self.p_hp = 3      # 플레이어 체력
        self.power = 1     # 미사일 파워
        self.score = 0     # 점수
        self.enemies = []  # 적 객체들을 담을 리스트
        self.bullets = []  # 총알 객체들을 담을 리스트
        self.items = []    # 아이템들을 담을 리스트
        self.boss_stage = False # 보스 등장 여부
        self.last_shot = 0 # 마지막으로 총을 쏜 시간 (연사 속도 조절용)
        self.is_over = False # 게임 종료 여부

        # 화면에 점수와 체력 표시
        self.txt_score = self.c.create_text(580, 20, text="SCORE: 0", fill="yellow", anchor=E, font=("Arial", 20))
        self.txt_hp = self.c.create_text(20, 20, text="HP: 3", fill="red", anchor=W, font=("Arial", 20))

        # 사운드 설정
        pygame.init()
        pygame.mixer.init()

        # 배경음악 로드
        try:
            pygame.mixer.music.load("sound/bg.mp3") 
            pygame.mixer.music.play(-1) #무한반복
        except:
            pass 

        # 효과음 로드
        try:
            self.s_effect1 = pygame.mixer.Sound("sound/destruction.mp3")
        except:
            self.s_effect1 = None # 파일 없으면 소리 안나게 설정

        # 게임 루프 시작
        self.run_game()

    def key_down(self, e): self.keys.add(e.keycode)
    
    def key_up(self, e):
        if e.keycode in self.keys: self.keys.remove(e.keycode)

    # 점수 텍스트 갱신
    def reset_score_text(self):
        self.c.itemconfig(self.txt_score, text="SCORE: " + str(self.score))

    # 피격 시 깜빡임 효과
    def show_player(self):
        self.c.itemconfig(self.player, state='normal')

    # 보스 경고 문구 삭제
    def delete_warning(self, text_id):
        self.c.delete(text_id)

    # 게임 종료 시 실행
    def on_close(self):
        self.is_over = True
        pygame.mixer.music.stop()
        pygame.quit()
        self.window.destroy()

    def run_game(self):
        while True:
            if self.is_over: # 게임 오버 상태면 화면 갱신
                self.window.update()
                continue
            try:
                if 37 in self.keys: self.c.move(self.player, -6, 0) # 왼쪽(37)
                if 39 in self.keys: self.c.move(self.player, 6, 0) # 오른쪽(38)
                if 38 in self.keys: self.c.move(self.player, 0, -6) # 위(39)
                if 40 in self.keys: self.c.move(self.player, 0, 6) # 아래(40)
                
                # 스페이스바(32) 처리 및 발사 속도 제한
                now = time.time()
                if 32 in self.keys and now - self.last_shot > 0.15:
                    self.last_shot = now
                    self.fire_player()

                # 객체관리
                self.manage_enemies() # 적 생성 및 이동
                self.move_objects()   # 총알, 아이템 이동
                self.check_collision() # 충돌 체크

                self.window.update() # 화면을 새로그림
                time.sleep(0.015)    # 게임 속도 조절 window.after는 게임 속도가 일정하지 않음
            
            except TclError:
                break

    # 플레이어 총알 발사 로직
    def fire_player(self):
        xy = self.c.coords(self.player)
        if not xy: return
        cx, cy = xy
        y = cy - 100
        speed = -15 
        fire_list = []

        # 파워에 따라 발사되는 총알 개수와 위치 변경
        if self.power == 1:
            fire_list.append((0, 0, speed))
        elif self.power == 2:
            fire_list.append((-10, 0, speed))
            fire_list.append((10, 0, speed))
        elif self.power == 3:
            fire_list.append((-20, 0, speed))
            fire_list.append((0, 0, speed))
            fire_list.append((20, 0, speed))
        elif self.power >= 4:
            fire_list.append((-30, 0, speed))
            fire_list.append((-10, 0, speed))
            fire_list.append((10, 0, speed))
            fire_list.append((30, 0, speed))

        # 계산된 위치에 총알 리스트에 추가
        for offset_x, dx, dy in fire_list:
            b = Bullet(self.c, cx+offset_x, y, dx, dy, 0, image=self.missile_img)
            self.bullets.append(b)

    def manage_enemies(self):
        # 점수가 2000점 넘으면 보스 등장
        if self.score >= 3000 and not self.boss_stage:
            for e in self.enemies: # 일반 적 삭제
                self.c.delete(e.id)
            self.enemies = []
            self.enemies.append(Enemy(self.c, 300, 150, 1, self.boss_img))
            self.boss_stage = True

            # 보스 등장 텍스트 표시
            warning = self.c.create_text(
                300, 400,
                text="BOSS APPEARED!",
                fill="red",
                font=("Arial", 40)
            )
            self.window.after(2000, self.delete_warning, warning) # 2초 뒤 텍스트 삭제
            
        # 보스가 없을 때는 랜덤하게 일반 적 생성
        if not self.boss_stage and random.randint(0, 50) == 0:
            x_rand = random.randint(50, 550)
            self.enemies.append(Enemy(self.c, x_rand, -50, 0, self.normal_enemy_img))

        # [:]를 사용해 리스트의 복사본으로 반복문을 돌림
        for e in self.enemies[:]:
            e.move()
            # 적 종류에 따라 공격 확률 다름
            attack_probability = 70 if e.kind == 0 else 15

            if random.randint(0, attack_probability) == 0:
                pos = self.c.coords(e.id)
                if not pos: continue
                cx, cy = pos
                if e.kind == 1: # 보스는 부채꼴 공격
                    for i in range(-4, 5):
                        self.fire_enemy(cx, cy, i * 3, 5, "red")
                else: # 일반 적은 직선 공격
                    self.fire_enemy(cx, cy, 0, 5, "red")

    # 적 총알 생성
    def fire_enemy(self, x, y, dx, dy, color):
        b = Bullet(self.c, x, y, dx, dy, 1, color=color)
        self.bullets.append(b)

    # 총알 및 아이템 이동 처리
    def move_objects(self):
        for b in self.bullets[:]:
            b.move()
            pos = self.c.bbox(b.id)
            # 화면 밖으로 나가면 삭제
            if pos is None or pos[1] < -10 or pos[3] > 810:
                b.delete()
                self.bullets.remove(b)
        
        # 아이템 이동 (위와 동일한 원리)
        for item_id in self.items[:]:
            self.c.move(item_id, 0, 3)
            pos = self.c.bbox(item_id)
            if pos is None or pos[1] > 810:
                self.c.delete(item_id)
                self.items.remove(item_id)

    # 아이템 드랍 (확률 10%)
    def drop_item(self, x, y):
        if random.randint(1, 20) <= 1:
            item_id = self.c.create_image(x, y, image=self.item_img, tags=("item", "power"))
            self.items.append(item_id)

    # 충돌 처리
    def check_collision(self):
        px_coords = self.c.coords(self.player)
        if not px_coords: return
        px, py = px_coords

        # 플레이어의 피격 범위(히트박스) 설정 - 몸체와 날개
        hitbox_body = (px - 10, py - 30, px + 10, py + 30)
        hitbox_wings = (px - 35, py - 10, px + 35, py + 10)
        
        # find_overlapping: 해당 사각형 영역에 겹친 모든 물체의 ID를 찾아줍니다.
        all_hits = set(self.c.find_overlapping(*hitbox_body)) | set(self.c.find_overlapping(*hitbox_wings))
        
        for t in all_hits:
            tags = self.c.gettags(t) # 충돌한 물체의 태그 확인
            
            # 1. 아이템을 먹었을 때
            if "item" in tags:
                self.c.delete(t)
                if t in self.items: self.items.remove(t)
                self.power = min(self.power + 1, 5) # 파워 최대 5로 제한
                self.c.itemconfig(self.txt_score, text="POWER UP!")
                self.window.after(1000, self.reset_score_text)

            # 2. 적 총알이나 적 몸체에 맞았을 때
            is_enemy_hit = False
            if "e_bullet" in tags:
                for b in self.bullets[:]:
                    if b.id == t: # 충돌한 총알을 찾아 삭제
                        b.delete()
                        self.bullets.remove(b)
                        is_enemy_hit = True
                        break
            elif "enemy" in tags or "boss" in tags:
                is_enemy_hit = True

            # 피격 처리
            if is_enemy_hit:
                self.p_hp -= 1
                self.c.itemconfig(self.txt_hp, text="HP: " + str(self.p_hp))
                if self.p_hp <= 0:
                    self.c.create_text(300, 400, text="GAME OVER", fill="white", font=("Arial", 40))
                    self.is_over = True
                else:
                    self.c.itemconfig(self.player, state='hidden') # 잠깐 숨겼다가
                    self.window.after(100, self.show_player)       # 다시 보여줌

        # 3. 내 총알이 적을 맞췄을 때
        for b in self.bullets[:]: # 여기도 리스트 복사 사용
            if b.team == 0:
                bx, by = b.coords()
                hitbox_b = (bx - 3, by - 10, bx + 3, by + 10)
                
                # 총알 위치에 겹친 물체 확인
                for t in self.c.find_overlapping(*hitbox_b):
                    # 적이나 보스를 맞췄다면
                    if "enemy" in self.c.gettags(t) or "boss" in self.c.gettags(t):
                        b.delete()
                        self.bullets.remove(b) # 총알 삭제
                        
                        # 어떤 적이 맞았는지 찾아서 체력 깎기
                        for e in self.enemies[:]:
                            if e.id == t:
                                e.hp -= 1
                                if e.hp <= 0: # 체력이 다 닳았다면
                                    if self.s_effect1:
                                        self.s_effect1.play() # 효과음 재생
                                    
                                    x, y = self.c.coords(e.id)
                                    self.c.delete(e.id) # 화면에서 삭제
                                    self.enemies.remove(e) # 리스트에서 삭제
                                    self.score += 100
                                    self.drop_item(x, y) # 아이템 드랍
                                    
                                    if e.kind == 1: # 보스를 잡으면 클리어
                                        self.c.create_text(300, 400, text="CLEAR!!", fill="yellow", font=("Arial", 40))
                                        self.is_over = True
                                break
                        self.c.itemconfig(self.txt_score, text="SCORE: " + str(self.score))

ShootingGame() # 게임 시작