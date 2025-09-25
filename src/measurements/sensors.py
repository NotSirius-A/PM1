class SensorProbe():
    @staticmethod
    def celsius_to_fahrenheit(T_c: float) -> float:
        return (T_c * 1.8) + 32
    
    @staticmethod
    def celsius_to_kelvin(T_c: float) -> float:
        return T_c + 273.15

class SensorPt100(SensorProbe):

    @staticmethod
    def calculate_temperature_celsius(probe_resistance: float) -> float:
        A = 3.9083e-3
        B = -5.7750e-7
        R0 = 100
        R = probe_resistance

        if R < 90:
            return (-242.09 + 2.2276 * R + 2.5178 * 1e-3 * R**2 - 5.8620 * 1e-6 * R**3) 
        else:
            return (-R0 * A + (R0**2 * A**2 - 4*R0*B * (R0 - R ))**0.5) / (2*R0*B)



class SensorPt1000(SensorProbe):
    @staticmethod
    def calculate_temperature_celsius(probe_resistance: float) -> float:
        A = 3.9083e-3
        B = -5.7750e-7
        R0 = 1000
        R = probe_resistance

        if R < 900:
            R = R/10
            return (-242.09 + 2.2276 * R + 2.5178 * 1e-3 * R**2 - 5.8620 * 1e-6 * R**3) 
        else:
            return (-R0 * A + (R0**2 * A**2 - 4*R0*B * (R0 - R ))**0.5) / (2*R0*B)
    
class SensorNTC(SensorProbe):
    pass