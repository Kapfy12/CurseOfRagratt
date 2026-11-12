"""Mirror each right-running rat frame; keep timing and frame order."""
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
src=Image.open(ROOT/'rat_run_right6.png').convert('RGBA')
W,H,N=256,128,6
assert src.size==(W*N,H)
sheet=Image.new('RGBA',src.size);preview=[]
for i in range(N):
    frame=src.crop((i*W,0,(i+1)*W,H)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    sheet.alpha_composite(frame,(i*W,0))
    bg=Image.new('RGB',(W,H),(27,30,36));bg.paste(frame,(0,0),frame)
    preview.append(bg.resize((768,384),Image.Resampling.NEAREST))
sheet.save(ROOT/'rat_run_left6.png')
preview[0].save(ROOT/'rat_run_left6.gif',save_all=True,append_images=preview[1:],duration=[100]*N,loop=0,disposal=2)
print('6 mirrored frames, 10 fps, transparent 1536x128 sheet.')
