"""
Pigment - Color and material definitions.

Defines pigments, color spaces, and material properties for realistic rendering.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from numpy.typing import NDArray


@dataclass
class Pigment:
    """
    Represents a physical pigment with optical properties.
    
    Pigments define how colors interact with light:
    - Spectral absorption
    - Transparency/opacity
    - Light scattering
    - Reflectance properties
    """
    
    id: str = field(default_factory=lambda: f"pigment_{uuid.uuid4().hex[:8]}")
    name: str = "Unnamed Pigment"
    
    # Color in sRGB
    color: Tuple[float, float, float] = (0.5, 0.5, 0.5)  # RGB [0, 1]
    
    # Physical properties
    transparency: float = 0.0      # 0 = opaque, 1 = fully transparent
    reflectance: float = 0.5       # Base reflectance
    scattering: float = 0.0        # Light scattering
    glossiness: float = 0.5       # Surface shininess
    
    # Oil paint specific
    oil_absorption: float = 0.5   # How much oil is absorbed
    hiding_power: float = 0.5      # How well it covers underlying layers
    
    # Color properties
    lightfastness: int = 7        # 1-8 rating (Archival)
    chromatic_strength: float = 1.0  # Tint strength
    
    # Metadata
    pigment_number: Optional[str] = None  # e.g., "PW6" for Titanium White
    manufacturer: Optional[str] = None
    
    @classmethod
    def create_preset(cls, preset_name: str) -> Pigment:
        """Create a common pigment preset."""
        presets = {
            # Whites
            "titanium_white": cls(
                name="Titanium White",
                color=(1.0, 1.0, 1.0),
                transparency=0.1,
                reflectance=0.95,
                hiding_power=1.0,
                pigment_number="PW6",
            ),
            "lead_white": cls(
                name="Lead White",
                color=(1.0, 1.0, 0.98),
                transparency=0.15,
                reflectance=0.9,
                hiding_power=0.95,
                pigment_number="PW1",
            ),
            
            # Blacks
            "ivory_black": cls(
                name="Ivory Black",
                color=(0.05, 0.05, 0.08),
                transparency=0.3,
                reflectance=0.05,
                hiding_power=0.8,
                pigment_number="PBk9",
            ),
            "lamp_black": cls(
                name="Lamp Black",
                color=(0.02, 0.02, 0.03),
                transparency=0.4,
                reflectance=0.03,
                hiding_power=0.75,
                pigment_number="PBk6",
            ),
            
            # Earth tones
            "raw_umber": cls(
                name="Raw Umber",
                color=(0.23, 0.18, 0.12),
                transparency=0.3,
                reflectance=0.15,
                hiding_power=0.85,
                pigment_number="PBr7",
            ),
            "burnt_umber": cls(
                name="Burnt Umber",
                color=(0.23, 0.14, 0.10),
                transparency=0.25,
                reflectance=0.12,
                hiding_power=0.9,
                pigment_number="PBr7",
            ),
            "raw_sienna": cls(
                name="Raw Sienna",
                color=(0.58, 0.38, 0.18),
                transparency=0.3,
                reflectance=0.3,
                hiding_power=0.7,
                pigment_number="PBr7",
            ),
            "burnt_sienna": cls(
                name="Burnt Sienna",
                color=(0.45, 0.25, 0.15),
                transparency=0.25,
                reflectance=0.25,
                hiding_power=0.85,
                pigment_number="PBr7",
            ),
            "yellow_ochre": cls(
                name="Yellow Ochre",
                color=(0.72, 0.55, 0.32),
                transparency=0.35,
                reflectance=0.4,
                hiding_power=0.75,
                pigment_number="PY43",
            ),
            
            # Blues
            "ultramarine": cls(
                name="Ultramarine Blue",
                color=(0.15, 0.25, 0.55),
                transparency=0.2,
                reflectance=0.25,
                hiding_power=0.7,
                lightfastness=8,
                pigment_number="PB29",
            ),
            "cobalt_blue": cls(
                name="Cobalt Blue",
                color=(0.10, 0.30, 0.60),
                transparency=0.25,
                reflectance=0.35,
                hiding_power=0.65,
                lightfastness=8,
                pigment_number="PB28",
            ),
            "cerulean": cls(
                name="Cerulean Blue",
                color=(0.30, 0.50, 0.65),
                transparency=0.4,
                reflectance=0.35,
                hiding_power=0.5,
                lightfastness=8,
                pigment_number="PB35",
            ),
            
            # Reds
            "cadmium_red": cls(
                name="Cadmium Red",
                color=(0.80, 0.10, 0.15),
                transparency=0.15,
                reflectance=0.35,
                hiding_power=0.9,
                lightfastness=8,
                pigment_number="PR108",
            ),
            "alizarin_crimson": cls(
                name="Alizarin Crimson",
                color=(0.50, 0.10, 0.20),
                transparency=0.2,
                reflectance=0.2,
                hiding_power=0.65,
                lightfastness=4,  # Not archival
                pigment_number="PR83",
            ),
            
            # Greens
            "viridian": cls(
                name="Viridian",
                color=(0.15, 0.45, 0.40),
                transparency=0.4,
                reflectance=0.3,
                hiding_power=0.5,
                lightfastness=8,
                pigment_number="PG18",
            ),
            "phthalo_green": cls(
                name="Phthalo Green",
                color=(0.05, 0.35, 0.30),
                transparency=0.25,
                reflectance=0.3,
                hiding_power=0.6,
                lightfastness=8,
                pigment_number="PG7",
            ),
            
            # Yellows
            "cadmium_yellow": cls(
                name="Cadmium Yellow",
                color=(0.95, 0.80, 0.10),
                transparency=0.2,
                reflectance=0.55,
                hiding_power=0.85,
                lightfastness=8,
                pigment_number="PY35",
            ),
            "naples_yellow": cls(
                name="Naples Yellow",
                color=(0.90, 0.75, 0.35),
                transparency=0.35,
                reflectance=0.5,
                hiding_power=0.7,
                lightfastness=8,
                pigment_number="PY35/PY41",
            ),
        }
        
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}")
            
        return presets[preset_name]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "color": list(self.color),
            "transparency": self.transparency,
            "reflectance": self.reflectance,
            "scattering": self.scattering,
            "glossiness": self.glossiness,
            "oil_absorption": self.oil_absorption,
            "hiding_power": self.hiding_power,
            "lightfastness": self.lightfastness,
            "chromatic_strength": self.chromatic_strength,
            "pigment_number": self.pigment_number,
            "manufacturer": self.manufacturer,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Pigment:
        """Deserialize from dictionary."""
        return cls(
            id=data.get("id", f"pigment_{uuid.uuid4().hex[:8]}"),
            name=data.get("name", "Pigment"),
            color=tuple(data.get("color", [0.5, 0.5, 0.5])),
            transparency=data.get("transparency", 0.0),
            reflectance=data.get("reflectance", 0.5),
            scattering=data.get("scattering", 0.0),
            glossiness=data.get("glossiness", 0.5),
            oil_absorption=data.get("oil_absorption", 0.5),
            hiding_power=data.get("hiding_power", 0.5),
            lightfastness=data.get("lightfastness", 7),
            chromatic_strength=data.get("chromatic_strength", 1.0),
            pigment_number=data.get("pigment_number"),
            manufacturer=data.get("manufacturer"),
        )


@dataclass
class PigmentSet:
    """
    A curated set of pigments for a palette.
    
    Represents a typical painter's palette with compatible pigments.
    """
    
    id: str = field(default_factory=lambda: f"palette_{uuid.uuid4().hex[:8]}")
    name: str = "Basic Palette"
    pigments: List[Pigment] = field(default_factory=list)
    
    @classmethod
    def create_preset(cls, preset_name: str) -> PigmentSet:
        """Create a standard palette preset."""
        presets = {
            "basic": cls._basic_palette(),
            "classical": cls._classical_palette(),
            "watercolor": cls._watercolor_palette(),
            "portrait": cls._portrait_palette(),
            "landscape": cls._landscape_palette(),
        }
        
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}")
            
        return presets[preset_name]
    
    @staticmethod
    def _basic_palette() -> PigmentSet:
        """A simple 6-pigment palette."""
        return PigmentSet(
            name="Basic Palette",
            pigments=[
                Pigment.create_preset("titanium_white"),
                Pigment.create_preset("ivory_black"),
                Pigment.create_preset("burnt_sienna"),
                Pigment.create_preset("ultramarine"),
                Pigment.create_preset("cadmium_yellow"),
                Pigment.create_preset("cadmium_red"),
            ],
        )
    
    @staticmethod
    def _classical_palette() -> PigmentSet:
        """Traditional Zorn-inspired palette."""
        return PigmentSet(
            name="Classical Palette",
            pigments=[
                Pigment.create_preset("titanium_white"),
                Pigment.create_preset("ivory_black"),
                Pigment.create_preset("yellow_ochre"),
                Pigment.create_preset("burnt_sienna"),
                Pigment.create_preset("cadmium_red"),
            ],
        )
    
    @staticmethod
    def _watercolor_palette() -> PigmentSet:
        """Watercolor-appropriate pigments."""
        return PigmentSet(
            name="Watercolor Palette",
            pigments=[
                Pigment.create_preset("titanium_white"),
                Pigment.create_preset("lamp_black"),
                Pigment.create_preset("raw_umber"),
                Pigment.create_preset("burnt_sienna"),
                Pigment.create_preset("yellow_ochre"),
                Pigment.create_preset("cadmium_yellow"),
                Pigment.create_preset("cadmium_red"),
                Pigment.create_preset("alizarin_crimson"),
                Pigment.create_preset("ultramarine"),
                Pigment.create_preset("cobalt_blue"),
                Pigment.create_preset("viridian"),
            ],
        )
    
    @staticmethod
    def _portrait_palette() -> PigmentSet:
        """Palette optimized for skin tones."""
        return PigmentSet(
            name="Portrait Palette",
            pigments=[
                Pigment.create_preset("titanium_white"),
                Pigment.create_preset("ivory_black"),
                Pigment.create_preset("yellow_ochre"),
                Pigment.create_preset("raw_sienna"),
                Pigment.create_preset("burnt_sienna"),
                Pigment.create_preset("cadmium_red"),
                Pigment.create_preset("alizarin_crimson"),
                Pigment.create_preset("ultramarine"),
            ],
        )
    
    @staticmethod
    def _landscape_palette() -> PigmentSet:
        """Palette optimized for landscapes."""
        return PigmentSet(
            name="Landscape Palette",
            pigments=[
                Pigment.create_preset("titanium_white"),
                Pigment.create_preset("ivory_black"),
                Pigment.create_preset("raw_umber"),
                Pigment.create_preset("burnt_umber"),
                Pigment.create_preset("raw_sienna"),
                Pigment.create_preset("yellow_ochre"),
                Pigment.create_preset("cadmium_yellow"),
                Pigment.create_preset("cadmium_yellow"),
                Pigment.create_preset("cadmium_red"),
                Pigment.create_preset("ultramarine"),
                Pigment.create_preset("cobalt_blue"),
                Pigment.create_preset("cerulean"),
                Pigment.create_preset("viridian"),
                Pigment.create_preset("phthalo_green"),
            ],
        )
    
    def get_pigment(self, name: str) -> Optional[Pigment]:
        """Get a pigment by name."""
        for p in self.pigments:
            if p.name.lower() == name.lower():
                return p
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "pigments": [p.to_dict() for p in self.pigments],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PigmentSet:
        """Deserialize from dictionary."""
        return cls(
            id=data.get("id", f"palette_{uuid.uuid4().hex[:8]}"),
            name=data.get("name", "Palette"),
            pigments=[Pigment.from_dict(p) for p in data.get("pigments", [])],
        )
