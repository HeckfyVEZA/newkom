import json
nusselt = lambda reynolds_criteria: 0.02006 * (reynolds_criteria ** .8)
def pkt_heat_calculation(
        supply_flow_rate:float,
        exhaust_flow_rate:float,
        temperature_inlet_supply:float,
        temperature_outlet_supply:float,
        temperature_inlet_exhaust:float,
        temperature_outlet_exhaust:float,
        lamel_width:float,
        lamel_length:float,
        quantity_of_lamels:int,
        distance_between_lamels:float,
        lamel_thickness:float=1e-3,
        viscosity:float=1.78e-5,
        lmbd_material:float=209.3,
        lmbd_air:float=0.022,
        air_dencity_supply:float=1.2,
        air_dencity_exhaust:float=1.2,
        heat_capacity:float=1006.5,
        heat_flow=None,
        **kwargs
    ):
    del locals()['kwargs']
    delta_T = abs(
        (temperature_inlet_supply + temperature_outlet_supply) / 2 - (temperature_inlet_exhaust + temperature_outlet_exhaust) / 2
        )
    area = lamel_width * lamel_length * quantity_of_lamels
    equivalent_diameter = 4 * (lamel_width * distance_between_lamels) / (lamel_width + distance_between_lamels)
    intersection = distance_between_lamels * lamel_width * (quantity_of_lamels / 2)
    supply_velocity = supply_flow_rate / (3600 * intersection)
    exhaust_velocity = exhaust_flow_rate / (3600 * intersection)
    reynolds_supply = air_dencity_supply * supply_velocity * distance_between_lamels / viscosity
    reynolds_exhaust = air_dencity_exhaust * exhaust_velocity * distance_between_lamels / viscosity
    supply_alpha = nusselt(reynolds_supply) * lmbd_air / distance_between_lamels
    exhaust_alpha = nusselt(reynolds_exhaust) * lmbd_air / distance_between_lamels
    heat_transfer_coefficient = ((supply_alpha ** (-1)) + (exhaust_alpha ** (-1)) + (lamel_thickness / lmbd_material)) ** (-1)
    heat_flow = area * heat_transfer_coefficient * delta_T
    required_heat_supply = supply_flow_rate * heat_capacity * air_dencity_supply * abs(temperature_inlet_supply - temperature_outlet_supply) / 3600
    required_heat_exhaust = exhaust_flow_rate * heat_capacity * air_dencity_exhaust * abs(temperature_outlet_exhaust - temperature_inlet_exhaust) / 3600
    temperature_outlet_supply = temperature_inlet_supply + ((3600 * heat_flow) / (heat_capacity * air_dencity_supply * supply_flow_rate))
    temperature_outlet_exhaust = temperature_inlet_exhaust - ((3600 * heat_flow) / (heat_capacity * air_dencity_exhaust * exhaust_flow_rate))
    return locals()
def pkt_calculation(
        **kwargs,
    ):
    calc = pkt_heat_calculation(
            **kwargs
    )
    count = 0
    while (
        ((calc['required_heat_supply'] - calc['heat_flow']) / calc['heat_flow'] > 1e-5 and (calc['required_heat_exhaust'] - calc['heat_flow']) / calc['heat_flow'] > 1e-5) 
        # or
        # (4.5 >= calc['delta_T'] or calc['delta_T'] >= 6)
        or
        (calc['temperature_inlet_supply'] >= calc['temperature_outlet_exhaust'] or calc['temperature_inlet_exhaust'] <= calc['temperature_outlet_supply'])
        ):
        count += 1
        if count > 125:
            return json.dumps({'error': 'Too many iterations'}, indent=4)
        calc = pkt_heat_calculation(**calc)
    del calc['kwargs']
    calc['count'] = count
    return json.dumps(calc, indent=4)

calculation = pkt_calculation(
        supply_flow_rate=500,
        exhaust_flow_rate=600,
        temperature_inlet_supply=-5,
        temperature_outlet_supply=10,
        temperature_inlet_exhaust=25,
        temperature_outlet_exhaust=15,
        lamel_width=.6,
        lamel_length=.04,
        quantity_of_lamels=22,
        distance_between_lamels=.002
        )
print(calculation)


