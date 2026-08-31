"""NOAA SWPC space weather schemas using Pydantic v2."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class KpEntry(BaseModel):
    model_config = ConfigDict(frozen=True)
    time_tag: str
    kp: float


class SpaceWeatherTelemetry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    kp_index: float = 0.0
    geomagnetic_status: str = "Quiet (Normal)"
    solar_activity: str = "Normal"
    # NOAA's products feed serves dicts ({"time_tag", "Kp", ...}); older SWPC
    # endpoints serve row lists. Accept both so the chart never starves.
    raw_kp: list[list | dict] = Field(default_factory=list)
    # Strongest flare class in the 6h GOES window, e.g. "M1.0" ("" if none)
    flare_class: str = ""
    # GOES 0.1-0.8nm channel flux trace, downscaled ×10⁻⁹ W/m² (~72 points)
    xray_flux: list[float] = Field(default_factory=list)
    # Next ~24h predicted Kp: [{"time_tag", "kp", "observed"}...] (predicted only)
    kp_forecast: list[dict] = Field(default_factory=list)

    @computed_field
    @property
    def noaa_scale(
        self,
    ) -> Literal[
        "G0 (Quiet)",
        "G1 (Minor)",
        "G2 (Moderate)",
        "G3 (Strong)",
        "G4 (Severe)",
        "G5 (Extreme)",
    ]:
        if self.kp_index >= 9.0:
            return "G5 (Extreme)"
        if self.kp_index >= 8.0:
            return "G4 (Severe)"
        if self.kp_index >= 7.0:
            return "G3 (Strong)"
        if self.kp_index >= 6.0:
            return "G2 (Moderate)"
        if self.kp_index >= 5.0:
            return "G1 (Minor)"
        return "G0 (Quiet)"
