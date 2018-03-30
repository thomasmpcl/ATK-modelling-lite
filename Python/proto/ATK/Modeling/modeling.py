#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function

import numpy as np
import math

EPS = 1.e-8
MAX_ITER = 200 # should probabl have one for steady state and one for non steady state

def retrieve_voltage(state, pin):
    return state[pin[0]][pin[1]]

class Voltage(object):
    """
    Class that sets a pin to a specific voltage
    """
    nb_pins = 1
    
    def __init__(self, V):
        self.V = V
        
    def __repr__(self):
        return "%.0fV at pin %s" % (self.V, self.pins[0])
    
    def update_model(self, model):
        pass

    def update_steady_state(self, state, dt):
        state[self.pins[0][0]][self.pins[0][1]] = self.V

    def update_state(self, state):
        pass

    def precompute(self, state):
        pass


class Resistor(object):
    """
    Class that implements a resistor between two pins
    """
    nb_pins = 2
    
    def __init__(self, R):
        self.R = R
        self.G = 1 / R

    def __repr__(self):
        return "%.0fohms between pins (%s,%s)" % (self.R, self.pins[0], self.pins[1])

    def update_model(self, model):
        pass

    def update_steady_state(self, state, dt):
        pass

    def update_state(self, state):
        pass

    def get_current(self, pin_index, state, steady_state):
        return (retrieve_voltage(state, self.pins[1]) - retrieve_voltage(state, self.pins[0])) * self.G * (1 if 0 == pin_index else -1)

    def get_gradient(self, pin_index_ref, pin_index, state, steady_state):
        return (1 if 1 == pin_index else -1) * (1 if 0 == pin_index_ref else -1) * self.G

    def precompute(self, state):
        pass


class Capacitor(object):
    """
    Class that implements a capacitor between two pins
    """
    nb_pins = 2
    
    def __init__(self, C):
        self.C = C

    def __repr__(self):
        return "%.0fF between pins (%s,%s)" % (self.C, self.pins[0], self.pins[1])
    
    def update_model(self, model):
        pass

    def update_steady_state(self, state, dt):
        self.dt = dt
        self.c2t = (2 * self.C) / dt
        
        self.iceq = self.c2t * (retrieve_voltage(state, self.pins[1]) - retrieve_voltage(state, self.pins[0]))

    def update_state(self, state):
        self.iceq = 2 * self.c2t * (retrieve_voltage(state, self.pins[1]) - retrieve_voltage(state, self.pins[0])) - self.iceq

    def get_current(self, pin_index, state, steady_state):
        if steady_state:
            return 0
        return ((retrieve_voltage(state, self.pins[1]) - retrieve_voltage(state, self.pins[0])) * self.c2t - self.iceq) * (1 if 0 == pin_index else -1)

    def get_gradient(self, pin_index_ref, pin_index, state, steady_state):
        if steady_state:
            return 0
        return (1 if 1 == pin_index else -1) * (1 if 0 == pin_index_ref else -1) * self.c2t

    def precompute(self, state):
        pass


class Coil(object):
    """
    Class that implements a coilbetween two pins
    """
    nb_pins = 2
    
    def __init__(self, L):
        self.L = L

    def __repr__(self):
        return "%.0fH between pins (%s,%s)" % (self.L, self.pins[0], self.pins[1])
    
    def update_model(self, model):
        assert(len(self.pins) == 2)
        self.pins.append(('P', len(model.pins['P'])))
        model.pins['P'].append([])

    def update_steady_state(self, state, dt):
        self.dt = dt
        self.c2t = (2 * self.C) / dt
        
        self.iceq = self.c2t * (retrieve_voltage(state, self.pins[1]) - retrieve_voltage(state, self.pins[0]))

    def update_state(self, state):
        self.iceq = 2 * self.c2t * (retrieve_voltage(state, self.pins[1]) - retrieve_voltage(state, self.pins[0])) - self.iceq

    def get_current(self, pin_index, state, steady_state):
        if steady_state:
            return 0
        return ((retrieve_voltage(state, self.pins[1]) - retrieve_voltage(state, self.pins[0])) * self.c2t - self.iceq) * (1 if 0 == pin_index else -1)

    def get_gradient(self, pin_index_ref, pin_index, state, steady_state):
        if steady_state:
            return 0
        return (1 if 1 == pin_index else -1) * (1 if 0 == pin_index_ref else -1) * self.c2t

    def precompute(self, state):
        pass


class Diode(object):
    """
    Class that implements a diode between two pins
    """
    nb_pins = 2
    
    def __init__(self, Is=1e-14, n=1.24, Vt = 26e-3):
        self.Is = Is
        self.n = n
        self.Vt = Vt

    def __repr__(self):
        return "Diode between pins (%s,%s)" % (self.pins[0], self.pins[1])

    def update_model(self, model):
        pass

    def update_steady_state(self, state, dt):
        pass

    def update_state(self, state):
        pass

    def get_current(self, pin_index, state, steady_state):
        return self.Is * (self.one_diode - 1) * (1 if 1 == pin_index else -1)

    def get_gradient(self, pin_index_ref, pin_index, state, steady_state):
        return self.Is / (self.n * self.Vt) * self.one_diode * (1 if 0 == pin_index else -1) * (1 if 1 == pin_index_ref else -1)

    def precompute(self, state):
        self.one_diode = math.exp((retrieve_voltage(state, self.pins[0]) - retrieve_voltage(state, self.pins[1])) / (self.n * self.Vt))


class AntiParallelDiode(object):
    """
    Class that implements a diode between two pins
    """
    nb_pins = 2
    
    def __init__(self, Is=1e-14, n=1.24, Vt = 26e-3):
        self.Is = Is
        self.n = n
        self.Vt = Vt

    def __repr__(self):
        return "Antiparallel diodes between pins (%s,%s)" % (self.pins[0], self.pins[1])
    
    def update_model(self, model):
        pass

    def update_steady_state(self, state, dt):
        pass

    def update_state(self, state):
        pass

    def get_current(self, pin_index, state, steady_state):
        return self.Is * (self.one_diode - 1 / self.one_diode) * (1 if 1 == pin_index else -1)

    def get_gradient(self, pin_index_ref, pin_index, state, steady_state):
        return self.Is / (self.n * self.Vt) * (self.one_diode + 1/ self.one_diode ) * (1 if 0 == pin_index else -1) * (1 if 1 == pin_index_ref else -1)

    def precompute(self, state):
        self.one_diode = math.exp((retrieve_voltage(state, self.pins[0]) - retrieve_voltage(state, self.pins[1])) / (self.n * self.Vt))

class TransistorNPN(object):
    """
    Class that implements a NPN transistor between 3 pins, BCE
    """
    nb_pins = 3
    
    def __init__(self, Is=1e-12, Vt=26e-3, Br=1, Bf=100):
        self.Is = Is
        self.Vt = Vt
        self.Br = Br
        self.Bf = Bf

    def __repr__(self):
        return "Transistor NPN (%f,%f,%f,%f) between pins (%s,%s,%s)" % (self.Is, self.Vt, self.Br, self.Bf, self.pins[0], self.pins[1], self.pins[2])
    
    def update_model(self, model):
        pass

    def update_steady_state(self, state, dt):
        pass

    def update_state(self, state):
        pass

    def ib(self, state):
        return self.Is * ((self.expVbe - 1) / self.Bf + (self.expVbc - 1) / self.Br)

    def ib_vbe(self, state):
        return self.Is * self.expVbe / self.Vt / self.Bf

    def ib_vbc(self, state):
        return self.Is * self.expVbc / self.Vt / self.Br

    def ic(self, state):
        return self.Is * ((self.expVbe - self.expVbc) - (self.expVbc - 1) / self.Br)

    def ic_vbe(self, state):
        return self.Is * self.expVbe / self.Vt

    def ic_vbc(self, state):
        return self.Is * (-self.expVbc - self.expVbc / self.Br) / self.Vt

    def get_current(self, pin_index, state, steady_state):
        if pin_index == 0:
            return -self.ib(state)
        elif pin_index == 1:
            return -self.ic(state)
        return self.ib(state) + self.ic(state)

    def get_gradient(self, pin_index_ref, pin_index, state, steady_state):
        if pin_index_ref == 0 and pin_index == 0:
            return self.ib_vbc(state) + self.ib_vbe(state)
        elif pin_index_ref == 0 and pin_index == 1:
            return -self.ib_vbc(state)
        elif pin_index_ref == 0 and pin_index == 2:
            return -self.ib_vbe(state)
        elif pin_index_ref == 1 and pin_index == 0:
            return self.ic_vbc(state) + self.ic_vbe(state)
        elif pin_index_ref == 1 and pin_index == 1:
            return -self.ic_vbc(state)
        elif pin_index_ref == 1 and pin_index == 2:
            return -self.ic_vbe(state)
        elif pin_index_ref == 2 and pin_index == 0:
            return -(self.ib_vbe(state) + self.ib_vbc(state) + self.ic_vbe(state) + self.ic_vbc(state))
        elif pin_index_ref == 2 and pin_index == 1:
            return self.ib_vbc(state) + self.ic_vbc(state)
        elif pin_index_ref == 2 and pin_index == 2:
            return self.ib_vbe(state) + self.ic_vbe(state)

    def precompute(self, state):
        Vbe = retrieve_voltage(state, self.pins[0]) - retrieve_voltage(state, self.pins[2])
        Vbc = retrieve_voltage(state, self.pins[0]) - retrieve_voltage(state, self.pins[1])
        self.expVbe = math.exp(Vbe / self.Vt)
        self.expVbc = math.exp(Vbc / self.Vt)


class TransistorPNP(object):
    """
    Class that implements a PNP transistor between 3 pins, BCE
    """
    nb_pins = 3
    
    def __init__(self, Is=1e-12, Vt=26e-3, Br=1, Bf=100):
        self.Is = Is
        self.Vt = Vt
        self.Br = Br
        self.Bf = Bf

    def update_model(self, model):
        pass

    def __repr__(self):
        return "Transistor PNP (%f,%f,%f,%f) between pins (%s,%s,%s)" % (self.Is, self.Vt, self.Br, self.Bf, self.pins[0], self.pins[1], self.pins[2])
    
    def update_steady_state(self, state, dt):
        pass

    def update_state(self, state):
        pass

    def ib(self, state):
        return self.Is * ((self.expVbe - 1) / self.Bf + (self.expVbc - 1) / self.Br)

    def ib_vbe(self, state):
        return self.Is * self.expVbe / self.Vt / self.Bf

    def ib_vbc(self, state):
        return self.Is * self.expVbc / self.Vt / self.Br

    def ic(self, state):
        return self.Is * ((self.expVbe - self.expVbc) - (self.expVbc - 1) / self.Br)

    def ic_vbe(self, state):
        return self.Is * self.expVbe / self.Vt

    def ic_vbc(self, state):
        return self.Is * (-self.expVbc - self.expVbc / self.Br) / self.Vt

    def get_current(self, pin_index, state, steady_state):
        if pin_index == 0:
            return self.ib(state)
        elif pin_index == 1:
            return self.ic(state)
        return -self.ib(state) - self.ic(state)

    def get_gradient(self, pin_index_ref, pin_index, state, steady_state):
        if pin_index_ref == 0 and pin_index == 0:
            return self.ib_vbc(state) + self.ib_vbe(state)
        elif pin_index_ref == 0 and pin_index == 1:
            return -self.ib_vbc(state)
        elif pin_index_ref == 0 and pin_index == 2:
            return -self.ib_vbe(state)
        elif pin_index_ref == 1 and pin_index == 0:
            return self.ic_vbc(state) + self.ic_vbe(state)
        elif pin_index_ref == 1 and pin_index == 1:
            return -self.ic_vbc(state)
        elif pin_index_ref == 1 and pin_index == 2:
            return -self.ic_vbe(state)
        elif pin_index_ref == 2 and pin_index == 0:
            return -(self.ib_vbe(state) + self.ib_vbc(state) + self.ic_vbe(state) + self.ic_vbc(state))
        elif pin_index_ref == 2 and pin_index == 1:
            return self.ib_vbc(state) + self.ic_vbc(state)
        elif pin_index_ref == 2 and pin_index == 2:
            return self.ib_vbe(state) + self.ic_vbe(state)

    def precompute(self, state):
        Vbe = retrieve_voltage(state, self.pins[0]) - retrieve_voltage(state, self.pins[2])
        Vbc = retrieve_voltage(state, self.pins[0]) - retrieve_voltage(state, self.pins[1])
        self.expVbe = math.exp(-Vbe / self.Vt)
        self.expVbc = math.exp(-Vbc / self.Vt)


class Modeler(object):
    """
    Modeling class
    """
    def __init__(self, nb_dynamic_pins, nb_static_pins, nb_inputs = 0):
        self.components = []
        self.dynamic_pins = [[] for i in range(nb_dynamic_pins)]
        self.static_pins = [[] for i in range(nb_static_pins)]
        self.input_pins = [[] for i in range(nb_inputs)]
        self.phantom_pins = []
        self.pins = {
                'D': self.dynamic_pins,
                'S': self.static_pins,
                'I': self.input_pins,
                'P': self.phantom_pins,
                }
        
        self.dynamic_state = np.zeros(nb_dynamic_pins, dtype=np.float64)
        self.static_state = np.zeros(nb_static_pins, dtype=np.float64)
        self.input_state = np.zeros(nb_inputs, dtype=np.float64)
        self.phantom_state = []
        self.state = {
                'D': self.dynamic_state,
                'S': self.static_state,
                'I': self.input_state,
                'P': self.phantom_state,
                }
        self.initialized = False
        
    def add_component(self, component, pins):
        self.components.append(component)
        component.pins = pins
        component.update_model(self)
        for (i, pin) in enumerate(pins):
            t, pos = pin
            self.pins[t][pos].append((component, i))
            
    def __repr__(self):
        return "Model with %i pins:\n  " % len(self.pins) + "\n  ".join((repr(component) for component in self.components))

    def get_state(self, index, pin):
        """
        Retrieve the static state for a pin
        """
        for component in pin:
            if hasattr(component[0], "V"):
                return component[0].V
        raise RuntimeError("Pin %i is declared static but can't retrieve a voltage state for it" % index)
        
    def setup(self):
        """
        Initializes the internal state
        """
        for component in self.components:
            component.update_steady_state(self.state, self.dt)

        self.solve(True)

        for component in self.components:
            component.update_steady_state(self.state, self.dt)

        self.initialized = True
        
    def compute_current(self, pin, steady_state):
        """
        Compute Kirschhoff law for the non static pin
        Compute also the jacobian for all the connected pins
        """
        eq = sum([component.get_current(i, self.state, steady_state) for (component, i) in pin])
        jac = [0] * len(self.dynamic_state)
        for (component, j) in pin:
            for (i, component_pin) in enumerate(component.pins):
                if component_pin[0] == "D":
                    jac[component_pin[1]] += component.get_gradient(j, i, self.state, steady_state)
        return eq, jac
    
    def solve(self, steady_state):
        """
        Actually solve the equaltion system
        """
        iteration = 0
        while iteration < MAX_ITER and not self.iterate(steady_state):
            iteration = iteration + 1        

    def iterate(self, steady_state):
        """
        Do one iteration
        """
        for component in self.components:
            component.precompute(self.state)
        eqs = []
        jacobian = []
        for pin in self.dynamic_pins:
            eq, jac = self.compute_current(pin, steady_state)
            eqs.append(eq)
            jacobian.append(jac)
        
        eqs = np.array(eqs)
        jacobian = np.array(jacobian)
        if np.all(np.abs(jacobian)) < EPS:
            return True
        
        delta = np.linalg.solve(jacobian, eqs)
        if np.all(np.abs(delta) < EPS):
            return True

        self.dynamic_state -= delta
                
        return False
        
    def __call__(self, input):
        """
        Works out the value for the new input vector
        """
        if not self.initialized:
            self.setup()
        
        self.input_state[:] = input

        self.solve(False)
        print(self.state)
        
        for component in self.components:
            component.update_state(self.state)

        return self.dynamic_state

if __name__ == "__main__":
    model = Modeler(1, 2, 0)

    model.add_component(Voltage(0), [('S', 0)])
    model.add_component(Voltage(5), [('S', 1)])
    model.add_component(Resistor(100), [('S', 0), ('D', 0)])
    model.add_component(Resistor(200), [('D', 0), ('S', 1)])
    
    model.dt = 1.e-3
    model.setup()
  
    print(model)
