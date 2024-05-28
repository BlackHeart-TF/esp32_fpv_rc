import pygame,math,queue,threading
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL import shaders
import receiver,cv2
import numpy as np

def set_projection(w, h):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    fov = 45.0
    aspect_ratio = w / h
    near_clip = 0.1
    far_clip = 50.0
    f = 1.0 / math.tan(math.radians(fov) / 2.0)
    projection_matrix = [
        f / aspect_ratio, 0, 0, 0,
        0, f, 0, 0,
        0, 0, (far_clip + near_clip) / (near_clip - far_clip), -1,
        0, 0, 2 * far_clip * near_clip / (near_clip - far_clip), 0
    ]
    glLoadMatrixf(projection_matrix)
    glMatrixMode(GL_MODELVIEW)

    

vertices = (
    (1, -1, 0),
    (1, 1, 0),
    (-1, 1, 0),
    (-1, -1, 0),
    (1, -1, 0.1),
    (1, 1, 0.1),
    (-1, -1, 0.1),
    (-1, 1, 0.1)
)

edges = (
    (0, 1),
    (0, 3),
    (0, 4),
    (2, 1),
    (2, 3),
    (2, 7),
    (6, 3),
    (6, 4),
    (6, 7),
    (5, 1),
    (5, 4),
    (5, 7)
)

surfaces = (
    (0, 1, 2, 3),
    (3, 2, 7, 6),
    (6, 7, 5, 4),
    (4, 5, 1, 0),
    (1, 5, 7, 2),
    (4, 0, 3, 6)
)


def load_texture():
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    return texture

def update_texture(texture, frame_bytes):
    glBindTexture(GL_TEXTURE_2D, texture)
    frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image.get_width(), image.get_height(), 0, GL_RGB, GL_UNSIGNED_BYTE, pygame.image.tostring(image, "RGB", 1))

def draw_box():
    width = 4 / 3
    height = 1.0
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex3f(-width, -height, 0)
    glTexCoord2f(1, 0); glVertex3f(width, -height, 0)
    glTexCoord2f(1, 1); glVertex3f(width, height, 0)
    glTexCoord2f(0, 1); glVertex3f(-width, height, 0)
    glEnd()

def samplebox():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
    glRotatef(1, 0.1, 3, 0.1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glBegin(GL_QUADS)
    for surface in surfaces:
        for vertex in surface:
            glColor3fv((1, 0, 0))
            glVertex3fv(vertices[vertex])
    glEnd()

    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    
    parser.add_argument("target", type=str,nargs='+')
    parser.add_argument("--listen", type=str,default="0.0.0.0")
    parser.add_argument("--fullscreen", action='store_true')
    parser.add_argument("--write", type=str)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--grab-all", action='store_true', default=False)
    args = parser.parse_args()

    udp = receiver.udp_transitter(args.target[0],args.listen)
    udp.Begin()
    if len(args.target) >1:
        udp2 = receiver.udp_transitter(args.target[1],args.listen)
        udp2.Begin()
    else:
        udp2 = None

    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    set_projection(display[0],display[1])

    texture = load_texture()
    glEnable(GL_TEXTURE_2D)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        try:
            frame = udp.frame_q.get(timeout=1)
            update_texture(texture, frame)
        except queue.Empty:
            pass
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -2.5)
        #samplebox()
        #glRotatef(10, 0.1, 3, 0.1)
        draw_box()
        pygame.display.flip()
        #pygame.time.wait(10)
    #stop the thread on exit
    udp.running = False

if __name__ == "__main__":
    main()
