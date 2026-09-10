from __future__ import annotations

import unittest

from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.projector import DirectionalProjector
from generator.hybrid_v3.compiler.pixel_grammar_v4 import (
    PixelGrammarCompilerV4,V4_VANILLA_PLUS_LIBRARY_VERSION,V4_VANILLA_PLUS_PROFILE,
    V42_PROOF_PROFILE,V42_SAILOR_OUTLINE_PROFILE,
)
from generator.hybrid_v3.compiler.shape_library_v42 import ShapeLibraryV42,VANILLA_PLUS_SHAPES


CASES=(
    ("POLO_SHIRT","POLO_CLASSIC","MASC_TAILORED",420201,"COASTAL_MIST",{"POLO_COLLAR_VANILLA_A","POLO_PLACKET_VANILLA_A"}),
    ("SWEATER_VEST","VEST_ACADEMIC","MASC_TAILORED",420203,"CREAM_ACADEMIC",{"VEST_V_BINDING_VANILLA_A","VEST_CUTIN_ARMHOLE_VANILLA_A","VEST_INNER_SHIRT_VANILLA_A","VEST_HEM_VANILLA_A"}),
    ("SAILOR_TOP","SAILOR_DECK_CLASSIC","UNISEX_REGULAR",420205,"SAILOR_NAVY",{"SAILOR_COLLAR_VANILLA_A","SAILOR_BOW_SMALL_A","SAILOR_REAR_FLAP_VANILLA_A"}),
    ("T_SHIRT","TEE_CLEAN_ESSENTIAL","UNISEX_REGULAR",420207,"SPRING_ORCHARD",{"TEE_CREW_BINDING_VANILLA_A"}),
)


class VanillaPlusProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder=CanonicalGarmentBuilder(); projector=DirectionalProjector()
        cls.results={}
        for family,intent,fit,seed,palette,expected in CASES:
            canonical=builder.build(family=family,design_intent=intent,fit_profile=fit,root_seed=seed,rarity_budget="V4_VANILLA_PLUS_PROOF")
            projections=projector.project(canonical)
            current_profile=V42_SAILOR_OUTLINE_PROFILE if family=="SAILOR_TOP" else V42_PROOF_PROFILE
            current=PixelGrammarCompilerV4(execution_profile=current_profile).compile(canonical,projections,palette_story=palette)
            plus=PixelGrammarCompilerV4(execution_profile=V4_VANILLA_PLUS_PROFILE).compile(
                canonical,projections,palette_story=palette,required_shape_library_version=V4_VANILLA_PLUS_LIBRARY_VERSION,
                expected_shape_variants=expected,
            )
            cls.results[family]=(current,plus,expected)

    def test_approved_micro_shape_library_is_complete(self):
        library=ShapeLibraryV42(document_path=VANILLA_PLUS_SHAPES)
        required=set(library.document["variantContract"]["required"])
        self.assertEqual(V4_VANILLA_PLUS_LIBRARY_VERSION,library.schema_version)
        for variant in library.variants.values():
            self.assertFalse(required-set(variant),variant["variantId"])

    def test_all_fixed_cases_route_and_pass(self):
        for family,(_,plus,expected) in self.results.items():
            self.assertEqual("PASS",plus.validation["status"],(family,plus.validation["issues"]))
            self.assertEqual(V4_VANILLA_PLUS_PROFILE,plus.metrics["executionProfile"])
            self.assertEqual(expected,set(plus.metrics["shapeVariants"]))

    def test_vanilla_plus_never_changes_current_alpha_geometry(self):
        for family,(current,plus,_) in self.results.items():
            for direction in ("front","right","back","left"):
                current_alpha={(x,y) for y,row in enumerate(current.frames[direction]) for x,p in enumerate(row) if p[3]}
                plus_alpha={(x,y) for y,row in enumerate(plus.frames[direction]) for x,p in enumerate(row) if p[3]}
                self.assertEqual(current_alpha,plus_alpha,(family,direction))

    def test_compressed_identity_anchors(self):
        polo=self.results["POLO_SHIRT"][1].semantic_regions["systems"]
        self.assertEqual(6,len(polo["collar"]["front"])); self.assertEqual(4,len(polo["placket"]["front"]))
        vest=self.results["SWEATER_VEST"][1]
        self.assertTrue(all(len(vest.semantic_regions["systems"]["hem"][d])==4 for d in ("front","right","back","left")))
        self.assertFalse(any(vest.semantic_regions["systems"][s][d] for s in ("waistband","ribbing") for d in ("front","right","back","left")))
        sailor=self.results["SAILOR_TOP"][1].semantic_regions["systems"]
        self.assertEqual(10,len(sailor["collar"]["front"])); self.assertEqual(4,len(sailor["tie"]["front"])); self.assertEqual(14,len(sailor["rear_panel"]["back"]))
        tee=self.results["T_SHIRT"][1].semantic_regions["systems"]
        self.assertEqual(6,len(tee["collar"]["front"]))


if __name__=="__main__": unittest.main()
