"""Schema and attribute checks."""

import re

import geopandas as gpd

from ..config import GeodoctorConfig
from ..registry import register_check
from ..report import Issue


@register_check("missing_required_field", severity="error", description="Required field is missing")
def check_missing_required_field(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    issues = []
    for field, spec in config.schema_config.fields.items():
        if spec.required and field not in gdf.columns:
            issues.append(
                Issue(
                    rule_id="missing_required_field",
                    severity="error",
                    message=f"Required field '{field}' is missing",
                )
            )
    return issues


@register_check("wrong_field_type", severity="warning", description="Field type doesn't match expected")
def check_wrong_field_type(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    issues = []
    type_map = {"int": "integer", "float": "floating", "str": "object", "bool": "bool"}
    for field, spec in config.schema_config.fields.items():
        if field not in gdf.columns:
            continue
        dtype = str(gdf[field].dtype)
        expected_kind = type_map.get(spec.type, "object")
        if expected_kind == "integer" and "int" not in dtype or expected_kind == "floating" and "float" not in dtype:
            issues.append(
                Issue(
                    rule_id="wrong_field_type",
                    severity="warning",
                    message=f"Field '{field}' is {dtype}, expected {spec.type}",
                )
            )
    return issues


@register_check("null_in_non_nullable", severity="error", description="Null values in non-nullable field")
def check_null_in_non_nullable(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    issues = []
    for field, spec in config.schema_config.fields.items():
        if spec.nullable or field not in gdf.columns:
            continue
        null_ids = gdf.index[gdf[field].isna()].tolist()
        if null_ids:
            issues.append(
                Issue(
                    rule_id="null_in_non_nullable",
                    severity="error",
                    message=f"Field '{field}' has {len(null_ids)} null values",
                    feature_ids=null_ids,
                )
            )
    return issues


@register_check("value_out_of_range", severity="warning", description="Numeric value outside allowed range")
def check_value_out_of_range(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    issues = []
    for field, spec in config.schema_config.fields.items():
        if field not in gdf.columns:
            continue
        if spec.min_value is not None:
            below = gdf.index[gdf[field] < spec.min_value].tolist()
            if below:
                issues.append(
                    Issue(
                        rule_id="value_out_of_range",
                        severity="warning",
                        message=f"Field '{field}': {len(below)} values below min={spec.min_value}",
                        feature_ids=below,
                    )
                )
        if spec.max_value is not None:
            above = gdf.index[gdf[field] > spec.max_value].tolist()
            if above:
                issues.append(
                    Issue(
                        rule_id="value_out_of_range",
                        severity="warning",
                        message=f"Field '{field}': {len(above)} values above max={spec.max_value}",
                        feature_ids=above,
                    )
                )
    return issues


@register_check("value_not_allowed", severity="error", description="Value not in allowed list")
def check_value_not_allowed(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    issues = []
    for field, spec in config.schema_config.fields.items():
        if field not in gdf.columns or not spec.allowed:
            continue
        allowed_set = set(spec.allowed)
        bad = gdf.index[~gdf[field].isin(allowed_set) & gdf[field].notna()].tolist()
        if bad:
            issues.append(
                Issue(
                    rule_id="value_not_allowed",
                    severity="error",
                    message=f"Field '{field}': {len(bad)} values not in allowed set: {sorted(allowed_set)}",
                    feature_ids=bad,
                )
            )
    return issues


@register_check(
    "non_unique_values", severity="warning", description="Field expected to have unique values has duplicates"
)
def check_non_unique_values(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    issues = []
    for field, spec in config.schema_config.fields.items():
        if not spec.unique or field not in gdf.columns:
            continue
        duped = gdf[field].duplicated()
        if duped.any():
            issues.append(
                Issue(
                    rule_id="non_unique_values",
                    severity="warning",
                    message=f"Field '{field}' has {duped.sum()} duplicate values",
                    feature_ids=gdf.index[duped].tolist(),
                )
            )
    return issues


@register_check("regex_mismatch", severity="warning", description="String value doesn't match expected pattern")
def check_regex_mismatch(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    issues = []
    for field, spec in config.schema_config.fields.items():
        if not spec.regex or field not in gdf.columns:
            continue
        pattern = re.compile(spec.regex)
        bad = gdf.index[
            gdf[field].apply(
                lambda v, p=pattern: not p.match(str(v))
                if v is not None and not isinstance(v, float)
                else False
            )
        ].tolist()
        if bad:
            issues.append(
                Issue(
                    rule_id="regex_mismatch",
                    severity="warning",
                    message=f"Field '{field}': {len(bad)} values don't match pattern '{spec.regex}'",
                    feature_ids=bad,
                )
            )
    return issues


@register_check("whitespace_in_string", severity="info", description="String fields have leading/trailing whitespace")
def check_whitespace_in_string(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    issues = []
    for col in gdf.select_dtypes(include=["object"]).columns:
        if col == "geometry":
            continue
        bad = gdf.index[gdf[col].apply(lambda v: isinstance(v, str) and v != v.strip())].tolist()
        if bad:
            issues.append(
                Issue(
                    rule_id="whitespace_in_string",
                    severity="info",
                    message=f"Field '{col}': {len(bad)} values with whitespace",
                    feature_ids=bad,
                    fix_available=True,
                )
            )
    return issues
