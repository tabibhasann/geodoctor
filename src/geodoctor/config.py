"""Configuration model for geodoctor.yml."""

from typing import Any, cast

from pydantic import BaseModel, Field

from .report import Severity


class FieldSpec(BaseModel):
    type: str = "str"
    required: bool = False
    unique: bool = False
    nullable: bool = True
    max_length: int | None = None
    min_value: float | None = None
    max_value: float | None = None
    allowed: list[Any] | None = None
    regex: str | None = None


class CRSConfig(BaseModel):
    expected: str | None = "EPSG:4326"
    require: bool = True


class GeometryConfig(BaseModel):
    allow_invalid: bool = False
    allow_empty: bool = False
    allow_null: bool = False
    allow_duplicates: bool = False
    single_geometry_type: bool = True
    min_area_m2: float = 1.0
    expected_ring_orientation: str | None = None


class SchemaConfig(BaseModel):
    fields: dict[str, FieldSpec] = Field(default_factory=dict)


class GeodoctorConfig(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    crs: CRSConfig = Field(default_factory=CRSConfig)
    geometry: GeometryConfig = Field(default_factory=GeometryConfig)
    schema_config: SchemaConfig = Field(default_factory=SchemaConfig)
    severity_overrides: dict[str, str] = Field(default_factory=dict)

    def effective_severity(self, rule_id: str, default: Severity) -> Severity:
        return cast(Severity, self.severity_overrides.get(rule_id, default))


def load_config(path: str | None = None) -> GeodoctorConfig:
    """Load configuration from a geodoctor.yml file."""
    import os

    import yaml

    if path and os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    # Remap "schema" key from YAML to "schema_config" in the model
    if isinstance(data, dict) and "schema" in data:
        data["schema_config"] = data.pop("schema")

    return GeodoctorConfig(**data)
