from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PropDefinition(BaseModel):
    type: Literal["string", "boolean", "number", "url", "enum", "object", "array"]
    required: bool = False
    default: Any = None
    values: list[Any] = Field(default_factory=list)
    minimum: float | None = None
    maximum: float | None = None


class SlotDefinition(BaseModel):
    accepts: list[str] = Field(default_factory=lambda: ["*"])
    minimum: int = 0
    maximum: int | None = None


class ComponentManifest(BaseModel):
    name: str
    version: str = "1.0.0"
    category: str
    icon: str
    editable: bool = True
    ai: bool = True
    draggable: bool = True
    droppable: bool = False
    props: dict[str, PropDefinition] = Field(default_factory=dict)
    slots: dict[str, SlotDefinition] = Field(default_factory=dict)
    actions: list[str] = Field(default_factory=list)
    ai_prompt: str = ""
    token_bindings: dict[str, str] = Field(default_factory=dict)


class ComponentInstance(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    type: str = Field(min_length=1, max_length=80)
    version: str = "1.0.0"
    props: dict[str, Any] = Field(default_factory=dict)
    styles: dict[str, Any] = Field(default_factory=dict)
    slots: dict[str, list["ComponentInstance"]] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)


class DesignDNA(BaseModel):
    style: str = "Modern SaaS"
    personality: str = "Professional"
    visual_density: Literal["compact", "comfortable", "spacious"] = "comfortable"
    corner_style: Literal["square", "soft", "rounded", "pill"] = "rounded"
    color_mood: str = "cool"
    animation_level: Literal["none", "subtle", "expressive"] = "subtle"
    contrast: Literal["low", "medium", "high"] = "high"
    icon_style: str = "outlined"
    illustration_style: str = "gradient"


class DesignSystem(BaseModel):
    version: str = "1.0.0"
    dna: DesignDNA = Field(default_factory=DesignDNA)
    colors: dict[str, str] = Field(default_factory=dict)
    typography: dict[str, str] = Field(default_factory=dict)
    spacing: dict[str, str] = Field(default_factory=dict)
    radius: dict[str, str] = Field(default_factory=dict)
    shadows: dict[str, str] = Field(default_factory=dict)
    animations: dict[str, str] = Field(default_factory=dict)


class PageDocument(BaseModel):
    schema_version: str = "1.0.0"
    type: Literal["Website"] = "Website"
    design_system: DesignSystem = Field(default_factory=DesignSystem)
    pages: list[ComponentInstance] = Field(default_factory=list)
