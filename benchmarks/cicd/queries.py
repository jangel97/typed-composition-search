QUERIES = [
    # ──────────────────────────────────────────────
    # Clean, well-structured queries
    # ──────────────────────────────────────────────
    {
        "id": "list_products",
        "category": "clean",
        "query": "List all tracked products",
        "source_type": "Dashboard",
        "target_type": "ProductList",
        "expected_tools": ["list_products"],
    },
    {
        "id": "product_details",
        "category": "clean",
        "query": "Show me the details for the Alpha Platform product",
        "source_type": "ProductKey",
        "target_type": "Product",
        "expected_tools": ["get_product_details"],
    },
    {
        "id": "latest_drop",
        "category": "clean",
        "query": "What is the latest drop for Beta Service?",
        "source_type": "Product",
        "target_type": "Drop",
        "expected_tools": ["list_drops", "select_drop"],
    },
    {
        "id": "drop_details",
        "category": "clean",
        "query": "Show me the details for drop alpha-platform-3.2.0",
        "source_type": "DropKey",
        "target_type": "Drop",
        "expected_tools": ["get_drop_details"],
    },
    {
        "id": "artifact_count",
        "category": "clean",
        "query": "How many artifacts does the Beta Service product have?",
        "source_type": "Product",
        "target_type": "ArtifactCount",
        "expected_tools": ["count_artifacts"],
    },
    {
        "id": "product_repos",
        "category": "clean",
        "query": "What git repositories are associated with Alpha Platform?",
        "source_type": "Product",
        "target_type": "RepositoryList",
        "expected_tools": ["list_git_repositories"],
    },
    {
        "id": "repo_branches",
        "category": "clean",
        "query": "Show me the branches for the core-runtime repository",
        "source_type": "RepositoryKey",
        "target_type": "BranchList",
        "expected_tools": ["get_repository_by_key", "get_repository_branches"],
    },
    {
        "id": "builder_releases",
        "category": "clean",
        "query": "What are the latest builder releases?",
        "source_type": "Dashboard",
        "target_type": "BuilderReleaseList",
        "expected_tools": ["list_builder_releases"],
    },
    {
        "id": "product_accelerators",
        "category": "clean",
        "query": "What accelerators does Beta Service support?",
        "source_type": "ProductKey",
        "target_type": "AcceleratorList",
        "expected_tools": ["get_product_details", "get_product_accelerators"],
    },
    {
        "id": "describe_model",
        "category": "clean",
        "query": "Describe the artifact data model",
        "source_type": "ModelName",
        "target_type": "DataModelDescription",
        "expected_tools": ["describe_data_model"],
    },

    # ──────────────────────────────────────────────
    # Ambiguous queries
    # ──────────────────────────────────────────────
    {
        "id": "ambiguous_new",
        "category": "ambiguous",
        "query": "Show me what's new",
        "source_type": "Dashboard",
        "target_type": "Drop",
        "expected_tools": ["list_all_drops", "select_drop"],
    },
    {
        "id": "ambiguous_build",
        "category": "ambiguous",
        "query": "Is the build passing?",
        "source_type": "Product",
        "target_type": "CIData",
        "expected_tools": ["get_ci_data_by_product"],
    },
    {
        "id": "ambiguous_release_status",
        "category": "ambiguous",
        "query": "What's the status of the latest release?",
        "source_type": "Product",
        "target_type": "Drop",
        "expected_tools": ["list_drops", "select_drop"],
    },

    # ──────────────────────────────────────────────
    # Multi-hop queries
    # ──────────────────────────────────────────────
    {
        "id": "multihop_artifact_sbom",
        "category": "multihop",
        "query": "Show me the SBOM for the latest CUDA artifact of Alpha Platform",
        "source_type": "Product",
        "target_type": "SBOMList",
        "expected_tools": [
            "search_artifacts",
            "select_artifact",
            "get_artifact_details",
            "get_artifact_sbom",
        ],
    },
    {
        "id": "multihop_release_commits",
        "category": "multihop",
        "query": "Show me the commits that went into the latest Beta Service release",
        "source_type": "Product",
        "target_type": "CommitList",
        "expected_tools": [
            "list_drops",
            "select_drop",
            "get_drop_changelog",
            "get_changelog_commits",
        ],
    },
    {
        "id": "multihop_builder_base_images",
        "category": "multihop",
        "query": "What base images are used in the latest builder release?",
        "source_type": "Dashboard",
        "target_type": "BaseImageList",
        "expected_tools": [
            "list_builder_releases",
            "select_builder_release",
            "get_builder_release_details",
            "get_builder_base_images",
        ],
    },
    {
        "id": "multihop_repo_tags",
        "category": "multihop",
        "query": "Show me the tags for repos that belong to Beta Service",
        "source_type": "Product",
        "target_type": "TagList",
        "expected_tools": [
            "list_git_repositories",
            "select_repository",
            "get_repository_details",
            "get_repository_tags",
        ],
    },
    {
        "id": "multihop_sha_digest",
        "category": "multihop",
        "query": "What is the SHA digest of the latest production ROCm artifact?",
        "source_type": "Product",
        "target_type": "SHADigest",
        "expected_tools": [
            "search_artifacts",
            "select_artifact",
            "get_artifact_details",
            "get_artifact_sha",
        ],
    },

    # ──────────────────────────────────────────────
    # Synonyms and alternative wording
    # ──────────────────────────────────────────────
    {
        "id": "synonym_images",
        "category": "synonym",
        "query": "What images are available for the CUDA accelerator?",
        "source_type": "Product",
        "target_type": "ArtifactList",
        "expected_tools": ["search_artifacts"],
    },
    {
        "id": "synonym_ci_status",
        "category": "synonym",
        "query": "Show me the CI status for this container",
        "source_type": "Artifact",
        "target_type": "CIData",
        "expected_tools": ["get_ci_data"],
    },
    {
        "id": "synonym_versions",
        "category": "synonym",
        "query": "What versions are supported for Alpha Platform?",
        "source_type": "Product",
        "target_type": "SeriesList",
        "expected_tools": ["list_series"],
    },

    # ──────────────────────────────────────────────
    # Noisy real-world language
    # ──────────────────────────────────────────────
    {
        "id": "noisy_drop_artifacts",
        "category": "noisy",
        "query": "Hey, we just cut a new drop for Beta Service, can you check how many artifacts made it in?",
        "source_type": "Drop",
        "target_type": "ArtifactCount",
        "expected_tools": ["count_artifacts_by_drop"],
    },
    {
        "id": "noisy_broken_build",
        "category": "noisy",
        "query": "The CUDA build seems broken, can you pull up the pipeline run and test results?",
        "source_type": "Product",
        "target_type": "IntegrationTestList",
        "expected_tools": ["get_ci_data_by_product", "get_ci_tests"],
    },
    {
        "id": "noisy_sha_digest",
        "category": "noisy",
        "query": "I need to find the production image for the latest ROCm artifact, what's the SHA?",
        "source_type": "Product",
        "target_type": "SHADigest",
        "expected_tools": [
            "search_artifacts",
            "select_artifact",
            "get_artifact_details",
            "get_artifact_sha",
        ],
    },

    # ──────────────────────────────────────────────
    # Multi-path queries (multiple valid paths)
    # ──────────────────────────────────────────────
    {
        "id": "multipath_drop_artifacts",
        "category": "multipath",
        "query": "What artifacts are in the latest Alpha Platform release?",
        "source_type": "Product",
        "target_type": "ArtifactList",
        "expected_tools": ["search_artifacts"],
    },
    {
        "id": "multipath_ci_data",
        "category": "multipath",
        "query": "Show me the CI/CD data for Beta Service",
        "source_type": "Product",
        "target_type": "CIData",
        "expected_tools": ["get_ci_data_by_product"],
    },
]
