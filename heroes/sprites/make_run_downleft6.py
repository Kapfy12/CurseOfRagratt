"""Mirror each down-right run frame independently, preserving frame order and timing."""
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
src=Image.open(ROOT/'warrior_run_downright6.png').convert('RGBA')
w,h=144,114
sheet=Image.new('RGBA',(w*6,h))
preview=[]
for f in range(6):
    frame=src.crop((f*w,0,(f+1)*w,h)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    sheet.alpha_composite(frame,(f*w,0))
    bg=Image.new('RGB',(w,h),(31,34,39));bg.paste(frame,(0,0),frame)
    preview.append(bg.resize((w*4,h*4),Image.Resampling.NEAREST))
sheet.save(ROOT/'warrior_run_downleft6.png')
preview[0].save(ROOT/'warrior_run_downleft6.gif',save_all=True,append_images=preview[1:],duration=[140,140,140,150,140,150],loop=0,disposal=2)
