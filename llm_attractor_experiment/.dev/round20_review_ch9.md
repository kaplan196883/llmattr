# Review of §9 Data, code, and reproducibility

1. **Move one layer of audit detail out of the main text.**  
   The section is strong, but it currently reads partly like a repository audit report rather than a confident reproducibility statement. For the main paper, keep the high-level guarantees: raw trajectories are public; derived artefacts and aggregate tables are archived; claims are mapped to files and commands; tests and audit scripts are provided. The exact inventory — "37 × 60 matrix", "103 / 103 cells", "99 pytest tests", "60 artefacts" — is useful but better suited to a supplement, repository README, or Data Availability appendix. In the main text, one sentence is enough:  
   > "Repository audit tables document per-experiment artefact coverage and verify all numerical claims against the released aggregate tables."

2. **Keep one or two headline reproducibility numbers, not all of them.**  
   The current density of counts risks sounding defensive. I would retain:  
   - 37 experiments  
   - 3.3 GB raw trajectories  
   - perhaps 103 / 103 numerical checks if this is a central trust claim  
   
   But I would demote or remove from the main body:  
   - "37 × 60 matrix"  
   - "99 passing tests in approximately 13 seconds"  
   - "all 37 experiments are at 100% of applicable artefacts"  
   
   These are valuable audit facts, but the paper's main text should not become a CI report. A cleaner formulation would be:  
   > "A coverage table, evidence map, and numerical-claim audit are included with the release and can be regenerated from the repository scripts."

3. **Treat cost and compute estimates as a practical note, not a headline claim.**  
   The cost estimates are useful for readers deciding whether to rerun the pipeline, but they are potentially time-sensitive and vendor-specific. Keep them, but frame them explicitly as approximate and dated:  
   > "At the time of analysis, regenerating canonical OpenAI embeddings cost approximately US$30, while regenerating model generations cost approximately US$200; these estimates depend on provider pricing and model availability."  
   
   The "2 hours on a 40-core machine" estimate is also useful, but it should be described as a reference benchmark rather than a reproducibility guarantee. Consider moving all cost/runtime details to the end of §9.3 or to a "Computational requirements" supplement.

4. **Clarify exact versus approximate reproducibility.**  
   The section should distinguish three cases:  
   - exact re-analysis from released raw `steps.jsonl`;  
   - canonical regeneration of embeddings using the same embedding model;  
   - non-identical reruns of model generation, which may vary because hosted LLM APIs change over time.  
   
   This distinction is important for a high-profile journal. The current text says regeneration is possible, but it should be explicit that the released trajectories are the canonical substrate for exact reproduction of the paper's claims. Suggested addition:  
   > "Because hosted generation APIs may change, exact reproduction of the paper's numerical results should use the released `steps.jsonl` trajectories; regeneration of model outputs is provided as a procedural replication path rather than a bitwise reproduction path."

5. **Replace the inline GitHub URL with an archival code citation.**  
   The GitHub URL is acceptable in a Code Availability statement, but for the main article it should ideally be accompanied by a permanent archive: Zenodo DOI, Software Heritage identifier, or versioned release DOI. Nature/Science style generally prefers citable, immutable repository snapshots. Recommended wording:  
   > "Code is available in the public repository and archived at [DOI/accession], corresponding to release vX.Y used for this manuscript."  
   
   The GitHub URL can remain in the availability statement or footnote, but the paper should cite a frozen release, not just the mutable `main` branch.

6. **Consolidate licence and access language.**  
   The licensing paragraph is useful but slightly vague: "the data license specified in the repository" leaves readers uncertain. State the actual data licence in the manuscript, especially because trajectories, embeddings, and derived artefacts may have different reuse implications. For example:  
   > "Code is released under GPLv3. Trajectories, embeddings, and derived analysis artefacts are released under [specific licence], with attribution."  
   
   If any OpenAI-generated text, embeddings, or Hugging Face-hosted data have provider-specific terms, acknowledge that briefly.

7. **Make the regeneration pathway more schematic and less file-system-heavy.**  
   The four-stage pipeline — generate, embed, analyze, aggregate — is clear and should remain. But many path names make the section feel like documentation. Consider replacing several file-path details with a compact reproducibility chain:  
   > "The canonical reproduction path is: download raw trajectories; compute or load embeddings; run per-experiment analyses; aggregate cross-experiment tables; run the coverage and numerical-claim audits."  
   
   Then give only the two most important commands in the main text, with full command lists in the repository or supplement.

## Verdict

§9 is much improved by the round-19 restructuring and now provides a credible reproducibility statement. However, it still contains more repository-audit detail than a main-text section needs. I recommend retaining the core availability, pipeline, licence, and audit assurances, while moving most exact counts, file matrices, pytest timing, and cost benchmarks into a supplement or repository documentation. The main text should project confidence: the data are public, the code is archived, the claims are traceable, and the canonical analysis can be rerun from released trajectories.
