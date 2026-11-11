from typing import Union
from brewwise.models.brew_log import BrewLogModel
from brewwise.schemas.brew import BrewLogCreate, AdjustmentRecommendation


class FeedbackAnalyser:
    @classmethod
    def analyse(cls, brew: Union[BrewLogModel, BrewLogCreate]) -> AdjustmentRecommendation:
        sour = brew.sourness
        bitter = brew.bitterness
        sweet = brew.sweetness
        body = brew.body
        satisfaction = brew.overall_satisfaction
        drawdown = (brew.drawdown_speed or "normal").lower()
        time_sec = brew.actual_brew_time_seconds
        current_temp = brew.actual_temp_c

        # Case 1: Channelling (Both sour and bitter are elevated)
        if sour >= 4 and bitter >= 4:
            return AdjustmentRecommendation(
                diagnosis="Channelling & Uneven Extraction",
                primary_adjustment="Improve pour distribution and lower pour height",
                secondary_adjustment="Swirl gently once during bloom, avoid excessive agitation in main pours",
                suggested_parameters={
                    "water_temperature_c": current_temp,
                    "pouring_technique": "Gentle spiral pours 5cm above bed",
                    "bloom_technique": "Gentle swirl to wet all grounds evenly"
                },
                rationale="Simultaneous sharp sourness and astringent bitterness indicate water created micro-channels, under-extracting dense clumps while over-extracting the channel paths."
            )

        # Case 2: Stalled Drawdown
        if drawdown == "stalled" or time_sec >= 270:
            return AdjustmentRecommendation(
                diagnosis="Filter Clogging / Excess Fines Migration",
                primary_adjustment="Grind 2 clicks coarser and eliminate aggressive swirls",
                secondary_adjustment="Pour steadily in the center without washing fines down the filter walls",
                suggested_parameters={
                    "grind_adjustment": "2 clicks coarser",
                    "target_brew_time_seconds": max(150, time_sec - 60),
                },
                rationale="Fines migrated to the bottom of the filter, choking the flow and prolonging contact time, leading to astringency."
            )

        # Case 3: Under-extraction (Sour, hollow, fast)
        if (sour >= 4 and bitter <= 2) or (drawdown == "fast" and time_sec < 135):
            return AdjustmentRecommendation(
                diagnosis="Under-Extraction",
                primary_adjustment="Grind 1–2 clicks finer to increase extraction surface area",
                secondary_adjustment=f"Increase water temperature from {current_temp}°C to {min(98, current_temp + 2)}°C",
                suggested_parameters={
                    "water_temperature_c": min(98, current_temp + 2),
                    "grind_adjustment": "1–2 clicks finer",
                    "target_brew_time_seconds": time_sec + 30
                },
                rationale="The coffee's sweetness and deeper flavors have not dissolved yet, leaving sharp unbuffered organic acids. Finer grind or hotter water will unlock full sweetness."
            )

        # Case 4: Over-extraction (Bitter, dry, harsh)
        if bitter >= 4 and sour <= 2:
            return AdjustmentRecommendation(
                diagnosis="Over-Extraction",
                primary_adjustment="Grind 1–2 clicks coarser to reduce contact resistance",
                secondary_adjustment=f"Decrease water temperature from {current_temp}°C to {max(86, current_temp - 2)}°C",
                suggested_parameters={
                    "water_temperature_c": max(86, current_temp - 2),
                    "grind_adjustment": "1–2 clicks coarser",
                    "target_brew_time_seconds": max(150, time_sec - 25)
                },
                rationale="Extraction ran too deep, pulling bitter, dry polyphenols from the cell walls of the coffee beans. A slightly coarser grind or cooler water will clean up the finish."
            )

        # Case 5: Weak / Watery (Low body, low sweetness)
        if body <= 2 and sweet <= 2:
            suggested_water = round(brew.actual_dose_g * 15.0, 1)
            return AdjustmentRecommendation(
                diagnosis="Low Extraction Yield / Watery Cup",
                primary_adjustment=f"Tighten brew ratio to 1:15 (reduce water to {suggested_water}g)",
                secondary_adjustment="Grind 1 click finer for higher TDS",
                suggested_parameters={
                    "water_g": suggested_water,
                    "ratio": "1:15",
                    "grind_adjustment": "1 click finer"
                },
                rationale="The concentration is too diluted. Tightening the ratio slightly will increase tactile body and mouthfeel without compromising clarity."
            )

        # Case 6: Sweet & Balanced (Ideal Cup!)
        if satisfaction >= 4:
            return AdjustmentRecommendation(
                diagnosis="Dialed-In Extraction Balance",
                primary_adjustment="Maintain exact parameters — this brew achieved peak sweetness and balance!",
                secondary_adjustment=None,
                suggested_parameters={
                    "water_temperature_c": current_temp,
                    "dose_g": brew.actual_dose_g,
                    "water_g": brew.actual_water_g
                },
                rationale="Sweetness, pleasant fruit acidity, and clean finish are well harmonized. Save this profile as your golden reference for this bean."
            )

        # General minor adjustment
        return AdjustmentRecommendation(
            diagnosis="Slight Under-Development",
            primary_adjustment="Grind 1 click finer or raise brew temp by 1°C",
            secondary_adjustment=None,
            suggested_parameters={"water_temperature_c": min(96, current_temp + 1)},
            rationale="A gentle nudge in extraction yield will lift residual sweetness and fruit clarity."
        )
