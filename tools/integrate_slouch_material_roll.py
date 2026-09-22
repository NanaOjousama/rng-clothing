#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path('/run/media/deck/USD00/RNG_clothing')
MATRIX=ROOT/'generator/data/headwear/slouch_beanie_roll_matrix.json'
OUT=ROOT/'authored/materials/slouch_beanie_v1/manifest.json'
OUT.parent.mkdir(parents=True,exist_ok=True)

semantic_root='experiments/spritefusion_beanie_material_test_01'
small_root='experiments/spritefusion_beanie_material_rescale_test_01/accepted_32_and_under'
small_evidence=[f'{small_root}/material_{i:02d}.png' for i in range(9)]

profiles={
 'rib_knit':{
   'partKind':'MATERIAL_PATTERN','role':'MATERIAL',
   'rollBindings':{'knitStructure':['fine_rib','wide_rib']},
   'semanticEvidence':[f'{semantic_root}/rib_knit/native/rib_knit_00.png',f'{semantic_root}/rib_knit/native/rib_knit_01.png'],
   'transfer':'vertical rib rhythm only; map through target surface zone; palette stays independent',
   'complexity':'low'
 },
 'cable_knit':{
   'partKind':'MATERIAL_PATTERN','role':'MATERIAL',
   'rollBindings':{'knitStructure':['cable']},
   'semanticEvidence':[f'{semantic_root}/cable_knit/native/cable_knit_00.png',f'{semantic_root}/cable_knit/native/cable_knit_01.png'],
   'transfer':'broad simplified cable rhythm only; never source coordinates or silhouette',
   'complexity':'medium'
 },
 'heather_knit':{
   'partKind':'MATERIAL_PATTERN','role':'MATERIAL_PATTERN',
   'rollBindings':{'knitStructure':['plain','fine_rib','brushed'],'pattern':['heather']},
   'semanticEvidence':[f'{semantic_root}/heather_knit/native/heather_knit_00.png',f'{semantic_root}/heather_knit/native/heather_knit_01.png'],
   'transfer':'sparse fleck/value rhythm; one-step local value variation; no alpha change',
   'complexity':'low'
 },
 'stripe_colorblock':{
   'partKind':'MATERIAL_PATTERN','role':'PATTERN',
   'rollBindings':{'pattern':['single_stripe','twin_stripe','contrast_cuff','two_tone_block']},
   'semanticEvidence':[f'{semantic_root}/stripe_colorblock/native/stripe_colorblock_00.png',f'{semantic_root}/stripe_colorblock/native/stripe_colorblock_01.png'],
   'transfer':'simple one- or two-band colour blocking; follow semantic band/body zones',
   'complexity':'low'
 },
 'plaid_woven':{
   'partKind':'MATERIAL_PATTERN','role':'PATTERN',
   'rollBindings':{'pattern':['plaid_woven']},
   'semanticEvidence':[f'{semantic_root}/plaid_woven/native/plaid_woven_00.png',f'{semantic_root}/plaid_woven/native/plaid_woven_01.png'],
   'transfer':'sparse 1px check rhythm; no full-width/full-height heavy grid; do not overwrite highlight structure',
   'complexity':'medium'
 },
 'fleece_wool':{
   'partKind':'MATERIAL_PATTERN','role':'MATERIAL',
   'rollBindings':{'knitStructure':['fleece_wool','brushed']},
   'semanticEvidence':[f'{semantic_root}/fleece_wool/native/fleece_wool_00.png',f'{semantic_root}/fleece_wool/native/fleece_wool_01.png'],
   'transfer':'soft clustered value blocks; hard pixel edges; no anti-aliasing or realistic fuzz',
   'complexity':'low'
 }
}

manifest={
 'schema':'slouch-beanie-material-pattern-library/v1',
 'family':'slouch_beanie',
 'status':'CANDIDATE_APPROVED',
 'source':'Sprite Fusion tests approved by user',
 'policy':{
   'constructionAuthority':'target template owns alpha/silhouette and directional geometry',
   'paletteAuthority':'palette is rolled separately; raw Sprite Fusion RGB is evidence only',
   'transfer':'donate material/pattern rhythm into declared surface/band/crown zones',
   'neverTransfer':['source silhouette','source alpha','blind source coordinates','raw high-colour palette'],
   'sizeEvidence':'semantic references may be oversized; approved small-scale evidence is 19-20px'
 },
 'profiles':profiles,
 'smallScaleEvidencePool':small_evidence
}
OUT.write_text(json.dumps(manifest,indent=2)+'\n')

m=json.loads(MATRIX.read_text())
m['materialPatternLibrary']='authored/materials/slouch_beanie_v1/manifest.json'
m['materialPatternBindings']={k:v['rollBindings'] for k,v in profiles.items()}

# Add new rollable values while retaining existing weights.
m['axes']['knitStructure'].setdefault('fleece_wool',6)
m['axes']['pattern'].setdefault('plaid_woven',4)

# Add explicit material/pattern exclusions if not already present.
rules=m['exclusions']
def add(rule):
    if rule not in rules:
        rules.append(rule)

add({
 'when':{'pattern':'plaid_woven'},
 'disallow':{
   'knitStructure':['cable','chunky','waffle'],
   'motif':['flower_cluster_small','animal_tiny','mushroom_tiny'],
   'decorationStyle':['knit_in']
 },
 'reduce':['busy_surface','motif_complexity'],
 'reason':'Plaid/woven already carries medium surface complexity; avoid stacking dense texture and busy motifs.'
})
add({
 'when':{'knitStructure':'fleece_wool'},
 'disallow':{
   'pattern':['simple_jacquard','cable_plus_stripe','twist_stripe'],
   'decorationStyle':['knit_in']
 },
 'reduce':['fine_surface_detail'],
 'reason':'Fleece/boiled-wool reads through clustered soft value blocks; dense knit-in patterning conflicts at Stardew scale.'
})
add({
 'when':{'knitStructure':'cable'},
 'disallow':{
   'pattern':['simple_jacquard','twist_stripe','plaid_woven']
 },
 'reason':'Cable is already a strong structural surface rhythm; dense plaid/jacquard/twist overlays are excluded.'
})
add({
 'when':{'pattern':'heather'},
 'disallow':{
   'decorationStyle':['contrast_stitch']
 },
 'reduce':['micro_fleck_density'],
 'reason':'Heather uses sparse fleck value rhythm; extra contrast-stitch noise is avoided.'
})

# Keep source-backed axis semantics explicit.
m['rollSemantics']={
 'construction':'template/construction selection; geometry authority',
 'knitStructure':'material/surface structure',
 'pattern':'surface overlay/colour rhythm',
 'motif':'small semantic decoration',
 'attachment':'approved alpha-adding component',
 'hardwareAccent':'small rigid accent',
 'palette':'independent recolour/value family'
}
MATRIX.write_text(json.dumps(m,indent=2)+'\n')
print('WROTE',OUT)
print('UPDATED',MATRIX)
print('profiles',len(profiles),'exclusions',len(rules))
