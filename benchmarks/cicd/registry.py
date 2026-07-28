from typed_composition_search import Registry


def build_registry() -> Registry:
    reg = Registry()

    # --- Products ---
    reg.register("list_products", ("Dashboard",), ("ProductList",))
    reg.register("select_product", ("ProductList",), ("Product",))
    reg.register("get_product_details", ("ProductKey",), ("Product",))
    reg.register("get_product_accelerators", ("Product",), ("AcceleratorList",))

    # --- Drops / Releases ---
    reg.register("list_drops", ("Product",), ("DropList",))
    reg.register("list_all_drops", ("Dashboard",), ("DropList",))
    reg.register("select_drop", ("DropList",), ("Drop",))
    reg.register("get_drop_details", ("DropKey",), ("Drop",))
    reg.register("get_drop_artifact_counts", ("Drop",), ("ArtifactCountByType",))
    reg.register("list_series", ("Product",), ("SeriesList",))
    reg.register("get_drop_timings", ("Drop",), ("ReleaseTimingList",))

    # --- Artifacts ---
    reg.register("search_artifacts", ("Product",), ("ArtifactList",))
    reg.register("search_artifacts_by_drop", ("Drop",), ("ArtifactList",))
    reg.register("search_artifacts_by_type", ("ArtifactType",), ("ArtifactList",))
    reg.register("select_artifact", ("ArtifactList",), ("Artifact",))
    reg.register("get_artifact_details", ("Artifact",), ("ArtifactDetails",))
    reg.register("get_artifact_by_key", ("ArtifactKey",), ("ArtifactDetails",))
    reg.register("get_artifact_sha", ("ArtifactDetails",), ("SHADigest",))
    reg.register("get_artifact_sbom", ("ArtifactDetails",), ("SBOMList",))
    reg.register("get_artifact_dependencies", ("ArtifactDetails",), ("DependencyList",))
    reg.register("get_artifact_related_images", ("ArtifactDetails",), ("RelatedImageList",))
    reg.register("count_artifacts", ("Product",), ("ArtifactCount",))
    reg.register("count_artifacts_by_drop", ("Drop",), ("ArtifactCount",))

    # --- Repositories ---
    reg.register("list_git_repositories", ("Product",), ("RepositoryList",))
    reg.register("list_all_git_repositories", ("Dashboard",), ("RepositoryList",))
    reg.register("select_repository", ("RepositoryList",), ("Repository",))
    reg.register("get_repository_details", ("Repository",), ("RepositoryDetails",))
    reg.register("get_repository_by_key", ("RepositoryKey",), ("RepositoryDetails",))
    reg.register("get_repository_branches", ("RepositoryDetails",), ("BranchList",))
    reg.register("get_repository_tags", ("RepositoryDetails",), ("TagList",))
    reg.register("get_repository_images", ("RepositoryDetails",), ("ImageList",))

    # --- Builder Releases ---
    reg.register("list_builder_releases", ("Dashboard",), ("BuilderReleaseList",))
    reg.register("select_builder_release", ("BuilderReleaseList",), ("BuilderRelease",))
    reg.register("get_builder_release_details", ("BuilderRelease",), ("BuilderReleaseDetails",))
    reg.register("get_builder_release_by_number", ("BuilderReleaseNumber",), ("BuilderReleaseDetails",))
    reg.register("get_builder_component_versions", ("BuilderReleaseDetails",), ("ComponentVersionList",))
    reg.register("get_builder_highlights", ("BuilderReleaseDetails",), ("HighlightList",))
    reg.register("get_builder_base_images", ("BuilderReleaseDetails",), ("BaseImageList",))

    # --- Changelogs ---
    reg.register("get_drop_changelog", ("Drop",), ("Changelog",))
    reg.register("get_changelog_commits", ("Changelog",), ("CommitList",))
    reg.register("select_commit", ("CommitList",), ("Commit",))

    # --- CI/CD Pipeline ---
    reg.register("get_ci_data", ("Artifact",), ("CIData",))
    reg.register("get_ci_data_by_product", ("Product",), ("CIData",))
    reg.register("get_ci_pipeline_run", ("CIData",), ("PipelineRun",))
    reg.register("get_ci_snapshot", ("CIData",), ("Snapshot",))
    reg.register("get_ci_releases", ("CIData",), ("CIReleaseList",))
    reg.register("get_ci_tests", ("CIData",), ("IntegrationTestList",))

    # --- Schema ---
    reg.register("describe_data_model", ("ModelName",), ("DataModelDescription",))

    # --- Cross-resource selectors ---
    reg.register("select_accelerator", ("AcceleratorList",), ("Accelerator",))
    reg.register("select_series", ("SeriesList",), ("Series",))
    reg.register("select_branch", ("BranchList",), ("Branch",))
    reg.register("select_tag", ("TagList",), ("Tag",))
    reg.register("select_ci_release", ("CIReleaseList",), ("CIRelease",))
    reg.register("select_integration_test", ("IntegrationTestList",), ("IntegrationTest",))

    return reg


ENTITY_TYPES = {
    # Root
    "Dashboard": "The CI/CD dashboard (root entry point for browsing products, drops, and repositories)",

    # Products
    "ProductKey": "A product identifier string (e.g. 'alpha-platform', 'beta-service')",
    "Product": "A tracked software product with versions and supported hardware",
    "ProductList": "A list of tracked products",
    "AcceleratorList": "Hardware accelerators supported by a product (CUDA, ROCm, Gaudi, etc.)",
    "Accelerator": "A specific hardware accelerator (e.g. cuda, rocm, gaudi, neuron)",

    # Drops / Releases
    "DropKey": "A drop/release identifier string (e.g. 'alpha-platform-3.2.0')",
    "Drop": "A product release/drop with version, dates, and environments",
    "DropList": "A list of drops/releases for a product",
    "ArtifactCountByType": "Artifact counts broken down by type for a drop",
    "SeriesList": "Available version series for a product (e.g. 3.0, 3.1, 3.2)",
    "Series": "A specific version series (e.g. 3.2)",
    "ReleaseTimingList": "Phase timestamps for a release (announced, built, tested, published)",

    # Artifacts
    "ArtifactKey": "A full artifact identifier (e.g. 'registry.example.com/org/cuda-base:3.2.5')",
    "ArtifactType": "A type of artifact (containers, disk-images, wheels, models)",
    "Artifact": "A build artifact (container image, disk image, wheel, or model)",
    "ArtifactList": "A list of artifacts matching search criteria",
    "ArtifactDetails": "Full artifact details including SHA, SBOMs, dependencies, and CI data",
    "ArtifactCount": "A count of artifacts matching filters",
    "SHADigest": "The SHA digest of a container image",
    "SBOMList": "Software Bill of Materials links for an artifact",
    "DependencyList": "Dependencies of an artifact",
    "RelatedImageList": "Related container images referenced by an artifact",

    # Repositories
    "RepositoryKey": "A git repository identifier (e.g. 'core-runtime')",
    "Repository": "A git repository with URL and product associations",
    "RepositoryList": "A list of git repositories",
    "RepositoryDetails": "Full repository details including branches, tags, and images",
    "BranchList": "Git branches in a repository",
    "Branch": "A git branch with name and last commit",
    "TagList": "Git tags in a repository",
    "Tag": "A git tag with name and commit SHA",
    "ImageList": "Container images built from a repository",

    # Builder Releases
    "BuilderReleaseNumber": "A builder/platform release number (e.g. 42)",
    "BuilderRelease": "A builder/platform release summary",
    "BuilderReleaseList": "A list of builder/platform releases",
    "BuilderReleaseDetails": "Full builder release details with component versions and highlights",
    "ComponentVersionList": "Component versions included in a builder release",
    "HighlightList": "Notable changes highlighted in a builder release",
    "BaseImageList": "Base images used in a builder release, grouped by accelerator",

    # Changelogs
    "Changelog": "Commit history between two drops for a repository",
    "CommitList": "A list of git commits",
    "Commit": "A single git commit with SHA, title, author, and date",

    # CI/CD Pipeline
    "CIData": "CI/CD build and release data for an artifact",
    "PipelineRun": "A CI pipeline run (build pipeline execution)",
    "Snapshot": "A CI snapshot (immutable artifact reference)",
    "CIReleaseList": "CI releases (stage and production promotions)",
    "CIRelease": "A single CI release entry with state and release plan",
    "IntegrationTestList": "CI integration test results for an artifact",
    "IntegrationTest": "A single integration test result with scenario and status",

    # Schema
    "ModelName": "A data model name (e.g. 'artifact', 'drop', 'product', 'repository')",
    "DataModelDescription": "Schema description of a data model's fields",
}
