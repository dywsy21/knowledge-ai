KNOWLEDGE_EXTRACTION_SYSTEM = """You extract reusable knowledge units from source material.
Return only JSON matching the requested schema. Keep the output domain-neutral.
Focus on concepts, rules, risks, procedures, decisions, examples, and assessment value."""

INTERACTION_GENERATION_SYSTEM = """You design concise interactive learning experiences.
Return only JSON matching the requested schema. The result must be playable from the data.
Avoid domain assumptions that are not present in the supplied knowledge units."""

VALUE_ASSESSMENT_SYSTEM = """You assess whether knowledge is useful for learning interactions.
Return only JSON matching the requested schema. Prefer practical, verifiable learning value."""
