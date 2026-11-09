"""NOAA SWPC space weather schemas — stdlib dataclasses, no pydantic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from models._coerce import opt_float, opt_float_list, opt_str
from models._model import DataModel


@dataclass(frozen=True, kw_only=True)
class KpEntry(DataModel):
    time_tag: str
    kp: float

    @classmethod
    def model_validate(cls, data) -> KpEntry:
        if not isinstance(data, dict):
            raise TypeError("KpEntry: expected object")
        return cls(
            time_tag=opt_str(data, "time_tag", ""), kp=opt_float(data, "kp", 0.0)
        )


@dataclass(frozen=True, kw_only=True)
class SpaceWeatherTelemetry(DataModel):
    _COMPUTED = ("noaa_scale",)

    kp_index: float = 0.0
    geomagnetic_status: str = "Quiet (Normal)"
    solar_activity: str = "Normal"
    # NOAA's products feed serves dicts ({"time_tag", "Kp", ...}); older SWPC
    # endpoints serve row lists. Accept both so the chart never starves.
    raw_kp: list = field(default_factory=list)
    # Strongest flare class in the 6h GOES window, e.g. "M1.0" ("" if none)
    flare_class: str = ""
    # GOES 0.1-0.8nm channel flux trace, downscaled ×10⁻⁹ W/m² (~72 points)
    xray_flux: list = field(default_factory=list)
    # Next ~24h predicted Kp: [{"time_tag", "kp", "observed"}...] (predicted only)
    kp_forecast: list = field(default_factory=list)

    @classmethod
    def model_validate(cls, data) -> SpaceWeatherTelemetry:
        if not isinstance(data, dict):
            raise TypeError("SpaceWeatherTelemetry: expected object")
        raw_kp = data.get("raw_kp")
        if raw_kp is not None and not isinstance(raw_kp, list):
            raise TypeError("raw_kp: expected list")
        kp_forecast = data.get("kp_forecast")
        if kp_forecast is not None:
            if not isinstance(kp_forecast, list):
                raise TypeError("kp_forecast: expected list")
            for row in kp_forecast:
                if not isinstance(row, dict):
                    raise TypeError("kp_forecast: expected objects")
        return cls(
            kp_index=opt_float(data, "kp_index", 0.0),
            geomagnetic_status=opt_str(data, "geomagnetic_status", "Quiet (Normal)"),
            solar_activity=opt_str(data, "solar_activity", "Normal"),
            raw_kp=raw_kp if raw_kp is not None else [],
            flare_class=opt_str(data, "flare_class", ""),
            xray_flux=opt_float_list(data, "xray_flux"),
            kp_forecast=kp_forecast if kp_forecast is not None else [],
        )

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
