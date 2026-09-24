#!/usr/bin/env python3
from __future__ import annotations
import json,sys,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];sys.path.insert(0,str(ROOT/'src'))
from prototype_core import compile_design,FACINGS
CONTROLS=ROOT/'control_assets';OUT=REPO/'experiments/photo_tailor_private_lab_01'
DESIGNS=[
 {'id':'beret_plaid_flower','control':'beret','description':'Plaid crown + contrast band + normalized flower shared across front/sides.',
  'semantic_pattern':'plaid','region_palettes':{'crown':['#8f5968','#d9a6b5','#f0cfca'],'band':['#4a3940','#e4c9b1']},
  'color_bands':[{'region':'band','top':.74,'bottom':1.0,'color':'#5d4650'}],
  'motifs':[{'type':'flower','x':.50,'y':.38,'scope':'FRONT_SIDES','color':'#f0d36b','scale':1}],'overlays':[]},
 {'id':'beanie_knit_badge','control':'beanie','description':'Normalized horizontal knit field, dark cuff region, front-only badge overlay.',
  'semantic_pattern':'horizontal_stripes','region_palettes':{'crown':['#617b9b','#93b4ce','#d4e0e5'],'band':['#293b4d','#6f8ca3']},
  'color_bands':[{'region':'band','top':.70,'bottom':1.0,'color':'#35495e'}],
  'motifs':[{'type':'badge','x':.50,'y':.49,'scope':'FRONT_ONLY','color':'#e4b85c','scale':1}],'overlays':[]},
 {'id':'straw_ribbon_leaf','control':'straw_hat','description':'Separate straw/ribbon/brim palettes, full-facing band and physically scoped side leaf.',
  'semantic_pattern':'solid','region_palettes':{'crown':['#d49b48','#f0c86c'],'band':['#426a58','#77a77e'],'brim':['#bd7d31','#e8b957']},
  'color_bands':[{'region':'band','top':.52,'bottom':.68,'color':'#557d63'}],
  'motifs':[{'type':'leaf','x':.72,'y':.58,'scope':'FRONT_SIDES','color':'#294d38','scale':1}],'overlays':[]},
 {'id':'boater_band_pin','control':'boater_hat','description':'Construction-derived crown/brim split with all-facing band and front-only pin.',
  'semantic_pattern':'solid','region_palettes':{'crown':['#d9ac5c','#f5d689'],'band':['#354b6b','#7189a5'],'brim':['#b77a32','#e5b85d']},
  'color_bands':[{'region':'band','top':.50,'bottom':.67,'color':'#405a7b'}],
  'motifs':[{'type':'diamond','x':.55,'y':.56,'scope':'FRONT_ONLY','color':'#e9d6a2','scale':1}],'overlays':[]},
 {'id':'mushroom_spotted','control':'mushroom_hat','description':'Semantic polka-dot field constrained to occupancy with cap/lower region palettes.',
  'semantic_pattern':'polka_dot','region_palettes':{'crown':['#8e4a4c','#e4b9a9','#f4dfb9'],'lower':['#7b654e','#d5bd91']},
  'color_bands':[],'motifs':[],'overlays':[]},
 {'id':'sun_floral_brim','control':'sun_hat','description':'Three-region sun hat with coherent floral motif propagation and separate brim palette.',
  'semantic_pattern':'diagonal','region_palettes':{'crown':['#637f92','#a9c0ca'],'band':['#d0a651','#f0d77f'],'brim':['#4d6574','#91abb8']},
  'color_bands':[{'region':'band','top':.48,'bottom':.62,'color':'#d4aa53'}],
  'motifs':[{'type':'flower','x':.50,'y':.56,'scope':'ALL_FACINGS','color':'#f0d66c','scale':1}],'overlays':[]},
 {'id':'tulip_vertical','control':'tulip_hat','description':'Normalized vertical stripe field cleaned against outline plus independently colored hem.',
  'semantic_pattern':'vertical_stripes','region_palettes':{'crown':['#657e60','#a8bd84','#d7ddb2'],'hem':['#3f5341','#7e9770']},
  'color_bands':[{'region':'hem','top':.83,'bottom':1.0,'color':'#4d624b'}],
  'motifs':[],'overlays':[]},
 {'id':'hood_two_tone_seams','control':'hood','description':'Two-tone hood preserving source shade topology with scoped front/back construction details.',
  'semantic_pattern':'colorblock','region_palettes':{'crown':['#6a597d','#aa8fb7'],'hem':['#40364d','#73617f']},
  'color_bands':[{'region':'crown','top':.48,'bottom':.78,'color':'#806792'}],
  'motifs':[{'type':'spark','x':.50,'y':.42,'scope':'BACK_ONLY','color':'#d6b65d','scale':1}],
  'overlays':[{'type':'vertical_seam','x':.50,'scope':'FRONT_ONLY','color':'#3e3249'}]},
]

def crop(im):
 b=im.getbbox();return im.crop(b) if b else im

def paste_scaled(can,im,box):
 x,y,w,h=box;im=crop(im.convert('RGBA'));scale=max(1,min(12,w//max(1,im.width),h//max(1,im.height)))
 im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);can.alpha_composite(im,(x+(w-im.width)//2,y+(h-im.height)//2))

def contact(rows):
 cw=210;labelw=280;rh=190;W=labelw+cw*6;H=rh*len(rows)+36
 can=Image.new('RGBA',(W,H),(238,236,229,255));dr=ImageDraw.Draw(can);f=ImageFont.load_default()
 heads=['CONTROL','FRONT','RIGHT','LEFT','BACK','REGIONS']
 for i,h in enumerate(heads):dr.text((labelw+i*cw+6,10),h,fill=(20,20,20),font=f)
 for ri,row in enumerate(rows):
  y=36+ri*rh;d=OUT/row['design_id'];dr.text((8,y+8),row['design_id'],fill=(20,20,20),font=f)
  dr.multiline_text((8,y+25),row['description'],fill=(40,40,40),font=f,spacing=3)
  paste_scaled(can,Image.open(CONTROLS/row['control_id']/'front.png'),(labelw,y+28,cw,145))
  for ci,v in enumerate(FACINGS,1):paste_scaled(can,Image.open(d/f'{v}.png'),(labelw+ci*cw,y+28,cw,145))
  paste_scaled(can,Image.open(d/'front_regions.png'),(labelw+5*cw,y+28,cw,145))
 can.save(OUT/'PHOTO_TAILOR_PRIVATE_LAB_CONTACT.png')

def layer_sheet(rows):
 cw=255;rh=175;W=cw*4;H=rh*len(rows)+32;can=Image.new('RGBA',(W,H),(238,236,229,255));dr=ImageDraw.Draw(can);f=ImageFont.load_default()
 for i,h in enumerate(['CONTROL FRONT','BASE FIELD','OVERLAY','FINAL FRONT']):dr.text((i*cw+6,8),h,fill=(20,20,20),font=f)
 for ri,row in enumerate(rows):
  y=32+ri*rh;d=OUT/row['design_id'];ims=[Image.open(CONTROLS/row['control_id']/'front.png'),Image.open(d/'front_base.png'),Image.open(d/'front_overlay.png'),Image.open(d/'front.png')]
  for ci,im in enumerate(ims):paste_scaled(can,im,(ci*cw,y+18,cw,145))
  dr.text((6,y+4),row['design_id'],fill=(20,20,20),font=f)
 can.save(OUT/'PHOTO_TAILOR_PRIVATE_LAB_BASE_OVERLAY.png')

def mask_sheet(rows):
 cw=160;rh=155;W=70+cw*8;H=rh*len(rows)+30;can=Image.new('RGBA',(W,H),(238,236,229,255));dr=ImageDraw.Draw(can);f=ImageFont.load_default()
 for i,v in enumerate(FACINGS):dr.text((70+i*cw+4,8),v.upper()+' OCC',fill=(20,20,20),font=f);dr.text((70+(i+4)*cw+4,8),v.upper()+' REG',fill=(20,20,20),font=f)
 for ri,row in enumerate(rows):
  y=30+ri*rh;d=OUT/row['design_id'];dr.text((4,y+5),row['control_id'],fill=(20,20,20),font=f)
  for i,v in enumerate(FACINGS):paste_scaled(can,Image.open(d/f'{v}_occupancy.png'),(70+i*cw,y+16,cw,125));paste_scaled(can,Image.open(d/f'{v}_regions.png'),(70+(i+4)*cw,y+16,cw,125))
 can.save(OUT/'PHOTO_TAILOR_PRIVATE_LAB_MASKS.png')

def main():
 if OUT.exists():shutil.rmtree(OUT)
 OUT.mkdir(parents=True);rows=[]
 for d in DESIGNS:
  od=OUT/d['id'];payload=compile_design(CONTROLS,d['control'],d,od);rows.append(payload)
  print(d['id'],payload['pattern_cells_after_cleanup'])
 manifest={'schema':'photo-tailor-private-lab/v1','privateDisposablePrototype':True,'productionImports':False,
  'productionGeneratorModified':False,'borrowedSourceSnapshot':'prototypes/photo_tailor_private_lab/vendor/photo_tailor_decompiled',
  'controlSnapshot':'prototypes/photo_tailor_private_lab/control_assets','featureCoverage':['4_view_projection','construction_template_drafting','normalized_motif_placement','facing_scopes','base_overlay_layers','occupancy_region_masks','normalized_pattern_coordinates','color_bands','semantic_pattern_fields','separate_region_palettes','shading_topology','texture_pattern_cleanup','coherent_detail_propagation'],
  'designs':rows}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');contact(rows);layer_sheet(rows);mask_sheet(rows)
 print('PASS',len(rows),'designs')
 print('CONTACT',OUT/'PHOTO_TAILOR_PRIVATE_LAB_CONTACT.png')
 print('LAYERS',OUT/'PHOTO_TAILOR_PRIVATE_LAB_BASE_OVERLAY.png')
 print('MASKS',OUT/'PHOTO_TAILOR_PRIVATE_LAB_MASKS.png')
if __name__=='__main__':main()
