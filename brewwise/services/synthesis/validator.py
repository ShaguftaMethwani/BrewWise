import re
from typing import List, Tuple
from brewwise.schemas.recipe import RecipeGenerationOutput


class RecipeValidator:
    @staticmethod
    def validate(output: RecipeGenerationOutput) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        # 1. Temperature check
        if not (85 <= output.water_temperature_c <= 99):
            errors.append(f"Water temperature {output.water_temperature_c}°C must be between 85°C and 99°C.")

        # 2. Ratio & Dose vs Total Water check
        # Parse ratio like "1:15" or "1:16.5"
        ratio_match = re.search(r"1\s*:\s*([\d\.]+)", output.ratio)
        if ratio_match:
            try:
                ratio_val = float(ratio_match.group(1))
                expected_water = round(output.dose_g * ratio_val, 1)
                if abs(expected_water - output.water_g) > 2.0:
                    errors.append(
                        f"Dose {output.dose_g}g with ratio {output.ratio} implies ~{expected_water}g water, but water_g is {output.water_g}g."
                    )
            except ValueError:
                pass

        # 3. Bloom check
        if output.bloom_water_g > output.water_g:
            errors.append(f"Bloom water ({output.bloom_water_g}g) cannot exceed total water ({output.water_g}g).")
        if output.bloom_water_g < output.dose_g:
            errors.append(f"Bloom water ({output.bloom_water_g}g) should be at least equal to dose ({output.dose_g}g).")

        # 4. Pour schedule sum check
        if not output.pour_schedule:
            errors.append("Pour schedule cannot be empty.")
        else:
            total_pour = sum(p.water_g for p in output.pour_schedule)
            if abs(total_pour - output.water_g) > 1.5:
                errors.append(
                    f"Sum of pours ({total_pour:.1f}g) does not equal total water ({output.water_g}g)."
                )

            # Cumulative and timing order check
            running_water = 0.0
            last_start = -1
            for p in output.pour_schedule:
                running_water += p.water_g
                if abs(running_water - p.cumulative_water_g) > 2.0:
                    errors.append(
                        f"Pour step {p.step_number} cumulative_water_g ({p.cumulative_water_g}g) does not match running total ({running_water:.1f}g)."
                    )
                if p.start_time_seconds < last_start:
                    errors.append(
                        f"Pour step {p.step_number} start time ({p.start_time_seconds}s) must be after previous step ({last_start}s)."
                    )
                last_start = p.start_time_seconds

        return len(errors) == 0, errors
