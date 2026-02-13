"""Clinical tracks and payment structures for CMS ACCESS model."""

from dataclasses import dataclass
from enum import Enum


class Track(Enum):
    """Clinical tracks available in ACCESS model."""
    ECKM = "eCKM"  # Enhanced Chronic Kidney Management
    CKM = "CKM"    # Chronic Kidney Management
    MSK = "MSK"    # Musculoskeletal
    BH = "BH"      # Behavioral Health


@dataclass(frozen=True)
class TrackPayment:
    """Payment structure for a clinical track.

    CMS ACCESS model uses 50/50 withhold:
    - 50% of payment is disbursed monthly
    - 50% is withheld and returned based on Outcome Attainment Threshold (OAT)
    """
    track: Track
    initial_payment: float  # First 12 months annual payment
    followon_payment: float | None  # Subsequent years (None = no follow-on)
    rural_addon: float  # Per-month add-on for rural patients
    has_followon: bool  # Whether track supports multi-year enrollment

    @property
    def initial_monthly(self) -> float:
        """Monthly payment in year 1."""
        return self.initial_payment / 12

    @property
    def followon_monthly(self) -> float:
        """Monthly payment in subsequent years."""
        if self.followon_payment is None:
            return 0.0
        return self.followon_payment / 12


# CMS payment amounts per track
TRACK_PAYMENTS: dict[Track, TrackPayment] = {
    Track.ECKM: TrackPayment(
        track=Track.ECKM,
        initial_payment=360.0,   # $30/month × 12
        followon_payment=180.0,  # $15/month × 12
        rural_addon=15.0,        # $15/month for rural
        has_followon=True,
    ),
    Track.CKM: TrackPayment(
        track=Track.CKM,
        initial_payment=420.0,   # $35/month × 12
        followon_payment=210.0,  # $17.50/month × 12
        rural_addon=15.0,        # $15/month for rural
        has_followon=True,
    ),
    Track.MSK: TrackPayment(
        track=Track.MSK,
        initial_payment=180.0,   # $15/month × 12
        followon_payment=None,   # Single episode only
        rural_addon=0.0,         # No rural add-on
        has_followon=False,
    ),
    Track.BH: TrackPayment(
        track=Track.BH,
        initial_payment=180.0,   # $15/month × 12
        followon_payment=90.0,   # $7.50/month × 12
        rural_addon=0.0,         # No rural add-on
        has_followon=True,
    ),
}


# Target requirements per track
# Each track requires meeting ALL targets to count toward OAT
TRACK_TARGETS: dict[Track, list[str]] = {
    Track.ECKM: ["bp_controlled", "hba1c_controlled", "kidney_stable"],
    Track.CKM: ["bp_controlled", "hba1c_controlled", "kidney_stable"],
    Track.MSK: ["functional_improved"],
    Track.BH: ["phq9_improved"],
}


def get_track_payment(track: Track, enrollment_year: int, current_year: int, is_rural: bool = False) -> float:
    """Calculate annual payment for a patient in a track.

    Args:
        track: The clinical track
        enrollment_year: When patient enrolled in track
        current_year: Current simulation year
        is_rural: Whether patient is in rural area

    Returns:
        Annual payment amount (before withhold)
    """
    payment_info = TRACK_PAYMENTS[track]
    years_enrolled = current_year - enrollment_year

    if years_enrolled == 0:
        # First year
        base = payment_info.initial_payment
    else:
        # Subsequent years
        if not payment_info.has_followon:
            return 0.0  # MSK: single episode only
        base = payment_info.followon_payment or 0.0

    # Add rural bonus
    if is_rural and payment_info.rural_addon > 0:
        base += payment_info.rural_addon * 12

    return base
