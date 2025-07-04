import os
from PIL import Image
from pipecat.frames.frames import OutputImageRawFrame, SpriteFrame

def load_robot_sprites(asset_dir: str):
    sprites = []
    for i in range(1, 26):
        path = os.path.join(asset_dir, f"robot0{i}.png")
        with Image.open(path) as img:
            sprites.append(OutputImageRawFrame(image=img.tobytes(), size=img.size, format=img.format))
    return sprites + sprites[::-1] 
def get_static_and_talking_frames(asset_dir: str):
    sprites = load_robot_sprites(asset_dir)
    return sprites[0], SpriteFrame(images=sprites)
