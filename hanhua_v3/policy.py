"""Shared source-preservation policies for scan and build stages."""


TBL_INTERNAL_TOKEN_DENYLIST = frozenset(
    {
        ("tbl0.pak", "AzureRenegade"),
        ("tbl0.pak", "BurningRenegade"),
    }
)


def is_tbl_internal_token(file_name: str, source_text: str) -> bool:
    return (file_name, source_text) in TBL_INTERNAL_TOKEN_DENYLIST
