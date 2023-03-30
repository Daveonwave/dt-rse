import pint
from typing import Union

from src.digital_twin.units import Unit
from src.digital_twin.utils import craft_data_unit, check_data_unit
from src.digital_twin.parameters.variables import Scalar, ParametricFunction, LookupTableFunction
from src.digital_twin.battery_models.ecm_components.generic_component import ECMComponent


class Resistor(ECMComponent):
    """
    Resistor element of Thevenin equivalent circuits.

    Parameters
    ----------
    :param name: identifier of the resistor
    :type name: str

    :param resistance: value of the resistance (Ohm)
    :type resistance: float or int or pint.Quantity

    # TODO: understand how resistance changes and other equations required to reproduce its behaviour
    """
    def __init__(self,
                 name:str,
                 resistance:Union[Scalar, ParametricFunction, LookupTableFunction],
                 units_checker:bool
                 ):
        super().__init__(name, units_checker)
        self._resistance = resistance

        # TODO: fix the unit through a yaml file
        self._r0_unit = Unit.OHM

        # Collections
        self._r0_series = []

    @property
    def resistance(self):
        """

        """
        input_vars = {}

        if not isinstance(self._resistance, Scalar):
            try:
                input_vars = {name: getattr(self, name) for name in self._resistance.x_names}
            except:
                raise Exception("Cannot retrieve required input variables to compute resistance for {}!".format(self.name))

        return self._resistance.get_value(input_vars=input_vars)

    @resistance.setter
    def resistance(self, value: Union[float, pint.Quantity]):
        # TODO: setter method to be updated (do we have to set a lookup table or a function?)
        if self.units_checker:
            self._resistance = craft_data_unit(value, Unit.OHM)
        else:
            self._resistance = value

    def get_r0_series(self, k=None):
        """
        Getter of the specific value at step K, if specified, otherwise of the entire collection
        """
        if k is not None:
            assert type(k) == int, \
                "Cannot retrieve resistance of {} at step K, since it has to be an integer".format(self._name)

            if len(self._r0_series) > k:
                if not self.units_checker:
                    return self._r0_series[k]
                else:
                    return self._r0_series[k].magnitude
            else:
                raise IndexError("Resistance R0 of {} at step K not computed yet".format(self._name))
        return self._r0_series

    def _update_r0_series(self, value: Union[float, pint.Quantity]):
        if self.units_checker:
            self._v_series.append(check_data_unit(value, self._r0_unit))
        else:
            self._v_series.append(value)

    def compute_v(self, i):
        """
        Compute the resistor potential V_r0, given in input the electric current I=I_r0
        #TODO: we will use 'k' when there will be the decay of resistance
        """
        if self.units_checker:
            i = check_data_unit(i, Unit.AMPERE).magnitude
            v_r0 = craft_data_unit(i * self.resistance, Unit.VOLT)
        else:
            v_r0 = i * self.resistance
        return v_r0

    def compute_i(self, v_r0):
        """
        Compute the flowing electric current I_r0=I, given in input the resistor potential V_r0
        """
        if self.units_checker:
            v_r0 = check_data_unit(v_r0, Unit.VOLT).magnitude
            i_r0 = craft_data_unit(v_r0 / self.resistance, Unit.AMPERE)
        else:
            i_r0 = v_r0 / self.resistance
        return i_r0

    def compute_dv(self, i, i_, dt):
        """
        Compute the derivative of (dv_r0/dt) using the backward finite differences approach.
        We consider (dr0/dt) constant, so we can erase the second term of the derivation by parts.

        Inputs:
        :param i: current at time t
        :param i_: current at previous sampling time t-dt
        :param dt: delta of time
        """
        if self.units_checker:
            i = check_data_unit(i, Unit.AMPERE).magnitude
            i_ = check_data_unit(i_, Unit.AMPERE).magnitude
            dv_r0 = craft_data_unit((i - i_) / dt * self.resistance, Unit.VOLT)
        else:
            dv_r0 = (i - i_) / dt * self.resistance
        return dv_r0

    def update_step_variables(self, r0, v_r0, dt, k):
        """
        Aggiorno le liste delle variabili calcolate
        """
        self._update_r0_series(r0)
        self.update_v(v_r0)
        self.update_t(self.get_t_series(k=k - 1) + dt)

    def compute_decay(self, temp, soc, soh):
        """
        # TODO: Update the resistance wrt the degradation of the resistor

        QUESTO METODO RICEVE LO STEP K, FA LE COMPUTAZIONI E AGGIORNA LE COLLECTIONS
        """
        pass




if __name__ == '__main__':
    resistor = Resistor('name', 5)
    curr = 10 * Unit.AMPERE
    print(resistor.compute_v(curr))