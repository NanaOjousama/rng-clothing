from __future__ import annotations

import unittest

from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.projector import DirectionalProjector
from generator.hybrid_v3.compiler.pixel_grammar_v4 import PixelGrammarCompilerV4,V41_BASELINE_PROFILE,V42_SAILOR_OUTLINE_PROFILE,V42_SAILOR_TECHNICAL_PROFILE,V42_SHAPE_LIBRARY_VERSION
from generator.hybrid_v3.compiler.shape_library_v42 import ShapeLibraryV42


CASES=(
    ("POLO_SHIRT","POLO_CLASSIC","MASC_TAILORED",420201,"COASTAL_MIST",{"ADD":2,"REMOVE":0}),
    ("SWEATER_VEST","VEST_ACADEMIC","MASC_TAILORED",420203,"CREAM_ACADEMIC",{"ADD":0,"REMOVE":4}),
    ("SAILOR_TOP","SAILOR_DECK_CLASSIC","UNISEX_REGULAR",420205,"SAILOR_NAVY",{"ADD":2,"REMOVE":0}),
)


class ShapeLibraryV42Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder=CanonicalGarmentBuilder(); projector=DirectionalProjector(); compiler=PixelGrammarCompilerV4()
        cls.results={}
        for family,intent,fit,seed,palette,_ in CASES:
            canonical=builder.build(family=family,design_intent=intent,fit_profile=fit,root_seed=seed,rarity_budget="V4_2_SHAPE_PROOF")
            projections=projector.project(canonical)
            cls.results[family]=compiler.compile(canonical,projections,palette_story=palette,required_shape_library_version=V42_SHAPE_LIBRARY_VERSION)

    def test_all_fourteen_required_variants_are_versioned_and_complete(self):
        library=ShapeLibraryV42(); required=set(library.document["variantContract"]["required"])
        expected={
            "FOLDED_POLO_COLLAR_FRONT_V1","FOLDED_POLO_COLLAR_SIDE_V1","FOLDED_POLO_COLLAR_BACK_V1","SHORT_POLO_PLACKET_FRONT_V1",
            "V_BINDING_FRONT_V1","V_BINDING_SIDE_V1","V_BINDING_BACK_V1","CUTIN_ARMHOLE_SIDE_V1","INNER_SHIRT_EXPOSURE_SIDE_V1","KNIT_HEM_TERMINATION_V1",
            "SAILOR_COLLAR_FRONT_V1","SAILOR_COLLAR_SIDE_V1","SAILOR_REAR_PANEL_V1","SAILOR_FRONT_OPENING_OR_INSERT_V1",
        }
        self.assertTrue(expected.issubset(set(library.variants)))
        for variant in library.variants.values(): self.assertFalse(required-set(variant),variant["variantId"])

    def test_three_fixed_proofs_pass_structural_qc(self):
        for family,result in self.results.items():
            self.assertEqual("PASS",result.validation["status"],(family,result.validation["issues"]))
            self.assertEqual("PENDING",result.validation["humanVisualQC"]["status"])
            self.assertTrue(result.validation["ownershipConflicts"]["allRejected"])

    def test_topology_displacement_is_real_and_survives(self):
        for family,_,_,_,_,expected in CASES:
            validation=self.results[family].validation
            self.assertEqual(expected,validation["topology"]["counts"])
            self.assertFalse(validation["topology"]["safeEnvelopeFailures"])
            self.assertFalse(validation["topology"]["survivalFailures"])
            self.assertEqual("PASS",validation["visualChangeContract"]["status"])
            self.assertFalse(validation["visualChangeContract"]["roleOnlyRecolorsReportedAsGeometry"])

    def test_directional_identity_contracts(self):
        polo=self.results["POLO_SHIRT"].semantic_regions["systems"]
        self.assertGreaterEqual(len(polo["collar"]["front"]),8)
        self.assertGreaterEqual(len(polo["placket"]["front"]),4)
        self.assertFalse(polo["placket"]["right"] or polo["placket"]["back"] or polo["placket"]["left"])
        vest=self.results["SWEATER_VEST"].semantic_regions["systems"]
        self.assertGreaterEqual(len(vest["inner_layer"]["right"]),3)
        self.assertGreaterEqual(len(vest["inner_layer"]["left"]),3)
        sailor=self.results["SAILOR_TOP"].semantic_regions["systems"]
        self.assertGreaterEqual(len(sailor["collar"]["front"]),18)
        self.assertGreaterEqual(len(sailor["rear_panel"]["back"]),24)
        self.assertFalse(sailor["rear_panel"]["front"])

    def test_v42_proof_fails_closed_on_baseline_route(self):
        family,intent,fit,seed,palette,_=CASES[0]
        builder=CanonicalGarmentBuilder(); canonical=builder.build(family=family,design_intent=intent,fit_profile=fit,root_seed=seed,rarity_budget="V4_2_SHAPE_PROOF")
        projections=DirectionalProjector().project(canonical)
        result=PixelGrammarCompilerV4(execution_profile=V41_BASELINE_PROFILE).compile(
            canonical,projections,palette_story=palette,required_shape_library_version=V42_SHAPE_LIBRARY_VERSION)
        self.assertEqual("FAIL",result.validation["status"])
        codes={issue["code"] for issue in result.validation["issues"]}
        self.assertIn("V4_2_SHAPE_LIBRARY_VERSION_MISMATCH",codes)
        self.assertIn("REQUIRED_SHAPE_VARIANT_NOT_EXECUTED",codes)

    def test_sailor_technical_reference_profile(self):
        expected={"SAILOR_COLLAR_FRONT_TECHNICAL_V1","SAILOR_COLLAR_SIDE_TECHNICAL_V1","SAILOR_REAR_FLAP_TECHNICAL_V1","SAILOR_COLLAR_BORDER_TECHNICAL_V1","SAILOR_FRONT_OPENING_OR_INSERT_V1"}
        builder=CanonicalGarmentBuilder(); canonical=builder.build(family="SAILOR_TOP",design_intent="SAILOR_DECK_CLASSIC",fit_profile="UNISEX_REGULAR",root_seed=420205,rarity_budget="V4_2_SAILOR_REFERENCE_EXPERIMENT",material="WOVEN_SHIRT")
        projections=DirectionalProjector().project(canonical)
        result=PixelGrammarCompilerV4(execution_profile=V42_SAILOR_TECHNICAL_PROFILE).compile(
            canonical,projections,palette_story="SAILOR_NAVY",required_shape_library_version=V42_SHAPE_LIBRARY_VERSION,expected_shape_variants=expected)
        self.assertEqual("PASS",result.validation["status"],result.validation["issues"])
        self.assertEqual(expected,set(result.metrics["shapeVariants"]))
        self.assertEqual({("ADD","right",12,1),("ADD","left",3,1)},
            {(op["op"],op["direction"],op["cell"][0],op["cell"][1]) for op in result.topology_map})
        border=result.semantic_regions["systems"]["collar_border"]
        self.assertGreaterEqual(len(border["front"]),8); self.assertGreaterEqual(len(border["back"]),20)

    def test_sailor_outline_refinement_preserves_architecture_and_owns_bow(self):
        technical_expected={"SAILOR_COLLAR_FRONT_TECHNICAL_V1","SAILOR_COLLAR_SIDE_TECHNICAL_V1","SAILOR_REAR_FLAP_TECHNICAL_V1","SAILOR_COLLAR_BORDER_TECHNICAL_V1","SAILOR_FRONT_OPENING_OR_INSERT_V1"}
        outline_expected={"SAILOR_COLLAR_FRONT_TECHNICAL_V1","SAILOR_COLLAR_SIDE_TECHNICAL_V1","SAILOR_REAR_FLAP_TECHNICAL_V1","SAILOR_COLLAR_FLAP_OUTLINE_REFINED_V1","SAILOR_FRONT_BOW_TIE_OUTLINE_REFINED_V1"}
        builder=CanonicalGarmentBuilder(); canonical=builder.build(family="SAILOR_TOP",design_intent="SAILOR_DECK_CLASSIC",fit_profile="UNISEX_REGULAR",root_seed=420205,rarity_budget="V4_2_SAILOR_OUTLINE_REFINEMENT",material="WOVEN_SHIRT")
        projections=DirectionalProjector().project(canonical)
        technical=PixelGrammarCompilerV4(execution_profile=V42_SAILOR_TECHNICAL_PROFILE).compile(
            canonical,projections,palette_story="SAILOR_NAVY",required_shape_library_version=V42_SHAPE_LIBRARY_VERSION,expected_shape_variants=technical_expected)
        outline=PixelGrammarCompilerV4(execution_profile=V42_SAILOR_OUTLINE_PROFILE).compile(
            canonical,projections,palette_story="SAILOR_NAVY",required_shape_library_version=V42_SHAPE_LIBRARY_VERSION,expected_shape_variants=outline_expected)
        self.assertEqual("PASS",outline.validation["status"],outline.validation["issues"])
        self.assertEqual(outline_expected,set(outline.metrics["shapeVariants"]))
        for direction in ("front","right","back","left"):
            self.assertEqual(
                {(x,y) for y,row in enumerate(technical.frames[direction]) for x,pixel in enumerate(row) if pixel[3]},
                {(x,y) for y,row in enumerate(outline.frames[direction]) for x,pixel in enumerate(row) if pixel[3]},
            )
            self.assertEqual(technical.semantic_regions["systems"]["collar"][direction],outline.semantic_regions["systems"]["collar"][direction])
            self.assertEqual(technical.semantic_regions["systems"]["rear_panel"][direction],outline.semantic_regions["systems"]["rear_panel"][direction])
            self.assertEqual(technical.semantic_regions["systems"]["collar_border"][direction],outline.semantic_regions["systems"]["collar_border"][direction])
        tie={tuple(cell) for cell in outline.semantic_regions["systems"]["tie"]["front"]}
        self.assertEqual({(7,2),(8,2),(7,3),(8,3)},tie)
        owners=[item for item in outline.semantic_regions["ownership"]["cells"]["front"] if tuple(item["cell"]) in tie]
        self.assertEqual(4,len(owners))
        self.assertTrue(all(item["component_owner"]=="sailor_bow_tie" and item["system"]=="tie" for item in owners))


if __name__=="__main__": unittest.main()
