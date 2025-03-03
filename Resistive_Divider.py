# -*- coding: utf-8 -*-

import math

# E96 base resistor values
E96_BASE_VALUES = [
    1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18,
    1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40, 1.43,
    1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74,
    1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10,
    2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55,
    2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
    3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74,
    3.83, 3.92, 4.02, 4.12, 4.22, 4.32, 4.42, 4.53,
    4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49,
    5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65,
    6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06,
    8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76
]

# Multipliers for E96
MULTIPLIERS = [
    1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1,
    1, 10, 100, 1e3, 1e4, 1e5, 1e6, 1e7
]

# Debug flag
DEBUG = False

def calculate_error(Vin, Vo, Rb, Rt):
    """Calculate the fractional error between actual and desired output voltage."""
    actual_Vout = Vin * (Rb / (Rb + Rt))
    return abs((actual_Vout / Vo) - 1)

def find_two_e96_values(value):
    """Find the closest E96 resistor values below and above the given value."""
    if value <= 0:
        raise ValueError("Resistance value must be positive")
    log_value = math.log10(value)
    exponent = math.floor(log_value)
    mantissa = 10 ** (log_value - exponent)
    idx = 0
    while idx < len(E96_BASE_VALUES) and E96_BASE_VALUES[idx] < mantissa:
        idx += 1
    candidates = []
    if idx > 0:
        candidates.append(E96_BASE_VALUES[idx - 1] * 10**exponent)
    if idx < len(E96_BASE_VALUES):
        candidates.append(E96_BASE_VALUES[idx] * 10**exponent)
    return sorted(set(candidates))

def generate_extended_list(start_value, start_multiplier):
    """Generate 96 consecutive E96 resistor values starting from a base and multiplier."""
    extended_list = []
    base_index = E96_BASE_VALUES.index(start_value)
    multi_index = MULTIPLIERS.index(start_multiplier)
    for _ in range(96):
        if base_index >= len(E96_BASE_VALUES):
            base_index = 0
            multi_index += 1
            if multi_index >= len(MULTIPLIERS):
                break
        val = E96_BASE_VALUES[base_index] * MULTIPLIERS[multi_index]
        extended_list.append(val)
        base_index += 1
    return extended_list

def analyze_all_values(Vin, Vo, Imax, extended_list):
    """Find the optimal E96 resistor pair for a voltage divider."""
    best_error = float('inf')
    best_rb = None
    best_rt = None
    best_actual_vout = None
    best_i_string = None
    best_p_top = None
    best_p_bot = None
    for Rb in extended_list:
        Ibottom = Vo / Rb
        if Ibottom > Imax:
            if DEBUG:
                print(f"DEBUG: Rb={Rb:.2f} => SKIP: Ibottom {Ibottom:.6f} > Imax {Imax}")
            continue
        ideal_Rtop = (Vin - Vo) / Ibottom
        if ideal_Rtop <= 0:
            if DEBUG:
                print(f"DEBUG: Rb={Rb:.2f} => SKIP: ideal Rtop invalid (<=0)")
            continue
        try:
            top_candidates = find_two_e96_values(ideal_Rtop)
        except ValueError:
            continue
        for Rt in top_candidates:
            actual_Vout = Vin * (Rb / (Rb + Rt))
            if actual_Vout > Vo:
                if DEBUG:
                    print(f"DEBUG: Rb={Rb:.2f}Ω Rt={Rt:.2f}Ω => SKIP: Vout {actual_Vout:.4f}V > Vo {Vo:.3f}V")
                continue
            err = calculate_error(Vin, Vo, Rb, Rt)
            if DEBUG:
                print(f"DEBUG: Rb={Rb:.2f}Ω Rt={Rt:.2f}Ω => Vout={actual_Vout:.4f}V Error={err*100:.2f}%")
            if err < best_error:
                best_error = err
                best_rb = Rb
                best_rt = Rt
                best_actual_vout = actual_Vout
                best_i_string = Vin / (Rb + Rt)
                best_p_top = Rt * best_i_string ** 2
                best_p_bot = Rb * best_i_string ** 2
    return {
        "best_rb": best_rb,
        "best_rt": best_rt,
        "best_error": best_error,
        "best_actual_vout": best_actual_vout,
        "best_i_string": best_i_string,
        "best_p_top": best_p_top,
        "best_p_bot": best_p_bot
    }

def format_resistor_value(value):
    """
    Format resistor values using E96-style notation with appropriate units.
    
    Args:
        value (float): Resistor value in ohms.
    
    Returns:
        str: Formatted resistor value with correct unit and E96-style rounding.
    """
    if value < 1e-3:
        return f"{value * 1e6:.1f} mΩ"  # Milliohms
    elif value < 1:
        return f"{value * 1e3:.1f} Ω"   # Ohms (less than 1)
    elif value < 10:
        return f"{value:.2f} Ω"        # 2 decimal places for small Ω values
    elif value < 1e3:
        return f"{value:.1f} Ω"        # 1 decimal place for larger Ω values
    elif value < 10e3:
        return f"{value / 1e3:.2f} kΩ"  # 2 decimal places for small kΩ values
    elif value < 1e6:
        return f"{value / 1e3:.1f} kΩ"  # 1 decimal place for kΩ
    elif value < 10e6:
        return f"{value / 1e6:.2f} MΩ"  # 2 decimal places for small MΩ values
    else:
        return f"{value / 1e6:.1f} MΩ"  # 1 decimal place for MΩ


def main():
    """Main function to calculate resistor divider values based on user input."""
    try:
        Vin = float(input("Enter Vin (Input Voltage, V): "))
        Vo = float(input("Enter Vo (Output Voltage, V): "))
        Imax = float(input("Enter Imax (Maximum Current through Rbottom, A): "))
        if Vin <= 0 or Vo <= 0 or Imax <= 0:
            raise ValueError("Vin, Vo, and Imax must be positive")
        if Vo >= Vin:
            raise ValueError("Vo must be less than Vin")
        Rb_min = Vo / Imax
        log_val = math.log10(Rb_min)
        exponent = math.floor(log_val)
        mantissa = 10 ** (log_val - exponent)
        closest_base = min(E96_BASE_VALUES, key=lambda x: abs(x - mantissa))
        closest_mult = 10 ** exponent
        extended_list = generate_extended_list(closest_base, closest_mult)
        results = analyze_all_values(Vin, Vo, Imax, extended_list)
        if results["best_rb"] is not None and results["best_rt"] is not None:
            print("\n--- Final Results ---")
            print(f"Rbottom = {format_resistor_value(results['best_rb'])}")
            print(f"Rtop = {format_resistor_value(results['best_rt'])}")
            print(f"Actual Vout = {results['best_actual_vout']:.4f} V")
            print(f"Error = {results['best_error'] * 100:.2f}%")
            print(f"String Current = {results['best_i_string']:.6f} A")
            print(f"Power (Rtop) = {results['best_p_top']:.6f} W")
            print(f"Power (Rbottom) = {results['best_p_bot']:.6f} W")
        else:
            print("\nNo valid resistor pair found under these constraints.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    input("\nPress any key to exit.")

def run_tests():
    """Run unit tests for critical functions, including resistor selection."""
    print("\nRunning Unit Tests...\n")

    # Test: Error Calculation
    assert math.isclose(calculate_error(10, 5, 1000, 1000), 0.0, rel_tol=1e-6), "Error calculation failed"

    # Test: Closest E96 Values
    vals = find_two_e96_values(150)
    assert len(vals) > 0, "E96 value finder failed"

    # Test: Generate Extended List
    ext_list = generate_extended_list(1.00, 100)
    assert len(ext_list) >= 96, "Extended list generation failed"

    # Test 1: High Voltage, Moderate Current (Vin=12V, Vo=5V, Imax=10mA)
    closest_base1 = 4.99  # Closest to 499Ω
    ext_list1 = generate_extended_list(closest_base1, 100) + generate_extended_list(closest_base1, 1000)
    result1 = analyze_all_values(12, 5, 0.01, ext_list1)

    assert result1["best_rb"] is not None, "Test 1: No valid resistor found for Rb"
    assert result1["best_rt"] is not None, "Test 1: No valid resistor found for Rt"
    assert math.isclose(result1["best_actual_vout"], 5, rel_tol=0.05), "Test 1: Vout too far from expected"
    assert result1["best_i_string"] <= 0.01, "Test 1: Current exceeds Imax"

    # Test 2: Low Voltage, High Current (Vin=3.3V, Vo=1.8V, Imax=100mA)
    Rb_min2 = 1.8 / 0.1
    log_val2 = math.log10(Rb_min2)
    exponent2 = math.floor(log_val2)
    mantissa2 = 10 ** (log_val2 - exponent2)
    closest_base2 = min(E96_BASE_VALUES, key=lambda x: abs(x - mantissa2))
    ext_list2 = generate_extended_list(closest_base2, 10 ** exponent2) + generate_extended_list(closest_base2, 10 ** (exponent2 + 1))
    result2 = analyze_all_values(3.3, 1.8, 0.1, ext_list2)

    assert result2["best_rb"] is not None, "Test 2: No valid resistor found for Rb"
    assert result2["best_rt"] is not None, "Test 2: No valid resistor found for Rt"
    assert math.isclose(result2["best_actual_vout"], 1.8, rel_tol=0.05), "Test 2: Vout too far from expected"
    assert result2["best_i_string"] <= 0.1, "Test 2: Current exceeds Imax"

    # Test 3: Tight Constraints (Vin=5V, Vo=2V, Imax=1mA)
    Rb_min3 = 2 / 0.001
    log_val3 = math.log10(Rb_min3)
    exponent3 = math.floor(log_val3)
    mantissa3 = 10 ** (log_val3 - exponent3)
    closest_base3 = min(E96_BASE_VALUES, key=lambda x: abs(x - mantissa3))
    ext_list3 = generate_extended_list(closest_base3, 10 ** exponent3) + generate_extended_list(closest_base3, 10 ** (exponent3 + 1))
    result3 = analyze_all_values(5, 2, 0.001, ext_list3)

    assert result3["best_rb"] is not None, "Test 3: No valid resistor found for Rb"
    assert result3["best_rt"] is not None, "Test 3: No valid resistor found for Rt"
    assert math.isclose(result3["best_actual_vout"], 2, rel_tol=0.05), "Test 3: Vout too far from expected"
    assert result3["best_i_string"] <= 0.001, "Test 3: Current exceeds Imax"

    print("✅ All tests passed!\n")

if __name__ == "__main__":
    run_tests()
    main()