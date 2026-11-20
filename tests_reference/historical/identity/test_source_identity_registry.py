from src.source_identity import (
    ApprovedSource,
    ApprovedSourceRegistry,
    SOURCE_IDENTITY_APPROVED,
    SOURCE_IDENTITY_UNKNOWN,
    identity_from_source,
    sources_match,
)


def registry() -> ApprovedSourceRegistry:
    return ApprovedSourceRegistry(
        (
            ApprovedSource(
                "modern_flames/fireplaces/spectrum/manual.pdf",
                "doc-modern",
            ),
            ApprovedSource(
                "grills/l_series/manual.pdf",
                "doc-grill",
            ),
        ),
        namespace_aliases=("legacy_catalog",),
    )


def test_approved_manifest_metadata_resolves_non_vendor_specific_identity() -> None:
    identity = identity_from_source(
        {
            "document_id": "doc-modern",
            "relative_path": "modern_flames/fireplaces/spectrum/manual.pdf",
        },
        registry=registry(),
    )

    assert identity.resolution_status == SOURCE_IDENTITY_APPROVED
    assert identity.canonical_path == "modern_flames/fireplaces/spectrum/manual.pdf"
    assert identity.source_namespace == "modern_flames"


def test_approved_namespace_alias_maps_only_to_manifest_path() -> None:
    match = sources_match(
        "legacy_catalog/grills/l_series/manual.pdf",
        "grills/l_series/manual.pdf",
        registry=registry(),
    )

    assert match.matched is True
    assert match.method == "document_id"
    assert match.reason_codes == ()


def test_unknown_root_does_not_silently_map_to_approved_source() -> None:
    unknown = identity_from_source(
        "unknown_vendor/grills/l_series/manual.pdf",
        registry=registry(),
    )
    match = sources_match(
        "unknown_vendor/grills/l_series/manual.pdf",
        "grills/l_series/manual.pdf",
        registry=registry(),
    )

    assert unknown.resolution_status == SOURCE_IDENTITY_UNKNOWN
    assert unknown.canonical_path == "unknown_vendor/grills/l_series/manual.pdf"
    assert match.matched is False
    assert SOURCE_IDENTITY_UNKNOWN in match.reason_codes


def test_unapproved_exact_path_remains_visibly_unresolved() -> None:
    match = sources_match(
        "synthetic/manual.pdf",
        "synthetic/manual.pdf",
        registry=registry(),
    )

    assert match.matched is True
    assert match.method == "canonical_path_unresolved"
    assert match.reason_codes == (SOURCE_IDENTITY_UNKNOWN,)
