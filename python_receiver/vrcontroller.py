import pygame,math,queue,threading
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import cv2
#import xr

import numpy as np
from lib.UDPReceiver import UDP
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

  
# def init_vr():
#     # Initialize OpenXR instance
#     instanceinfo = xr.InstanceCreateInfo(application_info=xr.ApplicationInfo(application_name="FPV Viewer"))
#     instance = xr.create_instance(instanceinfo)
#     system = instance.system()

#     # Create OpenXR session
#     session = instance.create_session(system)

#     # Create swapchain for rendering
#     swapchain_format = xr.SwapchainFormat.RGBA8
#     swapchain = session.create_swapchain(swapchain_format)
#     return swapchain


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

def draw_box(isSecond=False):
    width = 2 * 4 / 3
    height = 1.0
    offset = width*-1 if isSecond else 0
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex3f(offset, -height, 0)
    glTexCoord2f(1, 0); glVertex3f(width+offset, -height, 0)
    glTexCoord2f(1, 1); glVertex3f(width+offset, height, 0)
    glTexCoord2f(0, 1); glVertex3f(offset, height, 0)
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

    UDP.Begin(args.listen)
    udp = UDP(args.target[0])
    udp.BeginStream()
    if len(args.target) >1:
        udp2 = UDP(args.target[1])
        udp2.BeginStream()
    else:
        udp2 = None

    pygame.init()
    display = (1600 if udp2 else 800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    #set_projection(display[0],display[1])
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)
    vr_system = init_vr()
    texture = load_texture()
    glEnable(GL_TEXTURE_2D)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        try:
            frame = udp.frame_queue.get(timeout=1)
            update_texture(texture, frame)
        except queue.Empty:
            pass
        glLoadIdentity()
        glTranslatef(0.0 if udp2 else -1.35, 0.0, -2.4)
        #samplebox()
        #glRotatef(10, 0.1, 3, 0.1)
        draw_box()
        if udp2:
            try:
                frame = udp2.frame_queue.get(timeout=1)
                update_texture(texture, frame)
            except queue.Empty:
                pass
            draw_box(True)
        pygame.display.flip()
        #pygame.time.wait(10)
    #stop the thread on exit
    UDP.listening = False

if __name__ == "__main__":
    main()
