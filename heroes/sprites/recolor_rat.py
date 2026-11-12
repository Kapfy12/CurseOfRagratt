"""Cool ash-grey rat palette, preserving alpha, shading and saturated red eyes.
Run after rebuilding animations, before tools/embed_rat_runs.py.
Original brown sheets are retained separately.
"""
from pathlib import Path
from PIL import Image
import numpy as np
root=Path(__file__).resolve().parent
backup=root/'rat_brown_originals';backup.mkdir(exist_ok=True)
for direction in ('right','left','down','up'):
    path=root/f'rat_run_{direction}6.png'
    original=backup/path.name
    if not original.exists():original.write_bytes(path.read_bytes())
    a=np.array(Image.open(original).convert('RGBA'));rgb=a[:,:,:3].astype(float)
    r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    # Brown fur has appreciable green; only strongly saturated red is protected.
    red=(r>65)&(r>g*2.1)&(r>b*1.65)
    lum=rgb@np.array([.2126,.7152,.0722])
    shade=np.clip(lum*.86,0,255)
    grey=np.stack([shade*.94,shade*.99,shade*1.05],axis=-1)
    a[:,:,:3]=np.where(red[:,:,None],rgb,np.clip(grey,0,255)).astype('uint8')
    im=Image.fromarray(a);im.save(path)
    w,h=im.width//6,im.height
    zoom=3 if direction in ('right','left','up') else 2
    frames=[]
    for i in range(6):
        fr=im.crop((i*w,0,(i+1)*w,h));bg=Image.new('RGB',(w,h),(27,30,36));bg.paste(fr,(0,0),fr)
        frames.append(bg.resize((w*zoom,h*zoom),Image.Resampling.NEAREST))
    frames[0].save(path.with_suffix('.gif'),save_all=True,append_images=frames[1:],duration=100,loop=0,disposal=2)
    assert np.array_equal(a[:,:,3],np.array(Image.open(original))[:,:,3])
print('Four ash-grey sheets and previews updated; alpha unchanged.')
