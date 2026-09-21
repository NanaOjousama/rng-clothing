import unittest
from pathlib import Path
from v5.source.template_transfer import ContractError, assert_geometry_preserved, compile_recipe, decision, load_contract, verify_contract
from v5.pngio import blank_image
ROOT=Path(__file__).resolve().parents[2]

class TemplateTransferTests(unittest.TestCase):
    def setUp(self): self.tpl=load_contract(ROOT/'generator/data/templates/slouch_pl24.json')
    def test_contract(self):
        rep=verify_contract(self.tpl)
        self.assertEqual({'front','right','left','back'},set(rep['views']))
        self.assertTrue(self.tpl.geometry_lock['forbidResample'])
        self.assertTrue(self.tpl.geometry_lock['forbidGenericNormalization'])
    def test_allowed(self):
        a={'name':'x','partKind':'STYLE_PROFILE','transferScope':'STYLE_DONOR'}
        b={'name':'leaf','partKind':'MOTIF','transferScope':'FAMILY_REUSABLE','requiresZone':'surface'}
        self.assertEqual('ALLOW',decision(a,self.tpl)['decision'])
        self.assertEqual('ALLOW',decision(b,self.tpl)['decision'])
    def test_denied(self):
        a={'name':'x','partKind':'BASE_SPECIFIC','transferScope':'SAME_BASE_ONLY','sourceBaseIdentity':{'pack':'other'}}
        b={'name':'y','partKind':'ALTERNATE_CONSTRUCTION','transferScope':'ALTERNATE_CONSTRUCTION'}
        c={'name':'z','partKind':'MOTIF','transferScope':'FAMILY_REUSABLE','requiresZone':'not_a_zone'}
        self.assertEqual('DENY',decision(a,self.tpl)['decision'])
        self.assertEqual('DENY',decision(b,self.tpl)['decision'])
        self.assertEqual('DENY',decision(c,self.tpl)['decision'])
    def test_recipe_compiler(self):
        style={'id':'donor','name':'donor','partKind':'STYLE_PROFILE','transferScope':'STYLE_DONOR'}
        leaf={'name':'leaf','partKind':'MOTIF','transferScope':'FAMILY_REUSABLE','requiresZone':'surface','pack':'p','author':'a','family':'f'}
        recipe=compile_recipe(self.tpl,style,[leaf])
        self.assertEqual('slouch_pl24',recipe['template'])
        self.assertEqual('LOCKED_TEMPLATE_ALPHA',recipe['geometryPolicy'])
        self.assertEqual('leaf',recipe['parts'][0]['name'])

    def test_geometry_guard(self):
        a=blank_image(4,4); b=blank_image(4,4); a[1][1]=(1,1,1,255); b[1][2]=(1,1,1,255)
        with self.assertRaises(ContractError): assert_geometry_preserved(a,b)
        assert_geometry_preserved(a,[row[:] for row in a])

if __name__=='__main__': unittest.main()
