## ADDED Requirements

### Requirement: Mock visual retriever remains the default diagnostic backend
The visual retrieval baseline layer SHALL keep deterministic mock visual
retrieval as the default diagnostic backend and SHALL require explicit config
for any optional real visual zero-shot backend.

#### Scenario: Existing visual smoke remains local deterministic
- **WHEN** the visual smoke baseline or MVP pipeline uses default committed
  configs
- **THEN** it runs deterministic local mock visual retrieval without network
  access, model downloads, GPU hardware, or real ColPali / ColQwen execution

#### Scenario: Optional real backend does not change archived claims
- **WHEN** the optional real visual zero-shot backend is added
- **THEN** existing MVP metrics, reports, and claims remain diagnostic smoke
  evidence and are not rewritten as real visual retrieval results
