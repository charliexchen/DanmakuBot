import numpy as np


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def relu(x, scale=0.2):
    if x > 0:
        return x
    else:
        return scale * x


def tanh(x, scale=1.0):
    return scale * np.tanh(x)


class dense_layer:
    def __init__(self, input_size, output_size, activation, initvar=0.2):
        self.initvar = initvar
        self.weights = np.random.normal(0, initvar, [output_size, input_size + 1])
        self.input_size = input_size
        self.output_size = output_size
        self.activation = activation

    def activate(self, input):
        assert (
            len(input) == self.input_size
        ), "Input size incorrect: expected {} but obtained {}".format(
            self.input_size, len(input)
        )
        return np.array(
            [self.activation(row[0] + sum(input * row[1:])) for row in self.weights]
        )

    def mutate(self, rate):
        self.weights += np.random.normal(
            0, rate, [self.output_size, self.input_size + 1]
        )

    def reset(self, var=0.2):
        self.weights = np.random.normal(0, var, [self.output_size, self.input_size + 1])


class dense_net:
    def __init__(
        self,
        input_size,
        output_size,
        output_rule,
        initvar=0.2,
        recursive=False,
        rec_size=4,
    ):
        self.input_size = input_size
        self.layers = [dense_layer(input_size, output_size, output_rule, initvar)]
        self.recursive = recursive
        if self.recursive:
            self.rec_size = rec_size
            self.previous = [0 for i in range(rec_size)]
            self.finalised = False

    def add_layer(self, output_size, activation, initvar=0.2, final=False):
        if self.recursive:
            if final:
                try:
                    assert not self.finalised
                except AssertionError:
                    print("Error -- Rec Net already finalised")
                self.layers.append(
                    dense_layer(
                        self.layers[-1].output_size,
                        output_size + self.rec_size,
                        activation,
                        initvar,
                    )
                )
                self.layers[0] = dense_layer(
                    self.rec_size + self.input_size,
                    self.layers[0].output_size,
                    self.layers[0].activation,
                    self.layers[0].initvar,
                )
                self.previous = [0 for i in range(self.rec_size)]
                self.finalised = True
            else:
                self.layers.append(
                    dense_layer(
                        self.layers[-1].output_size, output_size, activation, initvar
                    )
                )
        else:
            self.layers.append(
                dense_layer(
                    self.layers[-1].output_size, output_size, activation, initvar
                )
            )

    def activate(self, input):
        if self.recursive:
            try:
                assert self.finalised
            except AssertionError:
                print("Error -- Evaluating Rec net before finalisation")
            input = list(input) + list(self.previous)

        try:
            if self.recursive:
                assert len(input) == self.input_size + self.rec_size
            else:
                assert len(input) == self.input_size
        except AssertionError:
            if self.recursive:
                print(
                    "Input size incorrect: expected {} but obtained {}".format(
                        self.input_size + self.rec_size, len(input)
                    )
                )
            else:
                print(
                    "Input size incorrect: expected {} but obtained {}".format(
                        self.input_size, len(input)
                    )
                )

        output = input
        for layer in self.layers:
            output = layer.activate(output)

        if self.recursive:
            output_length = self.layers[-1].output_size - self.rec_size
            self.previous = output[output_length:]
            return output[:output_length]
        else:
            return output

    def mutate(self, rate):
        if type(rate) == float:
            for layer in self.layers:
                layer.mutate(rate)
        else:
            assert len(self.layers) == len(rate)
            for i in range(len(self.layers)):
                self.layers[i].mutate(rate[i])

    def reset_rec(self,):
        try:
            assert self.recursive == True
        except AssertionError:
            print("Error -- tried to reset recursion inputs to non-recursive net")
        self.previous = [0 for i in self.previous]

    def reset(self, rate):
        if type(rate) == float:
            for layer in self.layers:
                layer.reset(rate)
        else:
            assert len(self.layers) == len(rate)
            for i in range(len(self.layers)):
                self.layers[i].reset(rate[i])


def LSTM():
    def __init__(self, nets, input_size, latent_size, output_size):
        self.output_size = output_size
        self.input_size = input_size
        self.latent_size = latent_size
        self.nets = nets
        self.latent1 = [0 for i in range(latent_size)]
        self.latent2 = [0 for i in range(latent_size)]
        try:
            assert len(nets) == 5
        except:
            print("Error - LSTM requires 5 nets")
        try:
            for i in range(4):
                assert net[i].input_size == input_size + latent_size
                assert nets[i].output_size == latent_size
                if i != 2:
                    assert nets[i].layers[-1].activation == sigmoid
                else:
                    assert nets[i].layers[-1].activation == tanh
            assert nets[4].output_size == output_size
        except:
            print("Error - component neural nets wrong size")

    def activate(self, input):
        concat_input = input + self.latent1
        concat_output = [net.activate(concat_input) for net in self.nets[:3]]
        scale1 = [
            self.latent2[i] * concat_output[0][i] for i in range(self.latent_size)
        ]
        scale2 = [
            concat_output[2][i] * concat_output[1][i] for i in range(self.latent_size)
        ]
        self.latent2 = [tanh(scale1[i] + scale2[i]) for i in range(self.latent_size)]
        output = [self.latent2[i] * concat_output[3] for i in range(self.latent_size)]
        self.latent1 = output

        return self.nets[4].activate(output)

    def mutate(self, rate):
        for net in self.nets:
            net.mutate(rate)


def make_focused(net, sensor_len):
    net.input_size += 2
    net.layers[0].input_size += 2
    net.layers[0].weights = np.insert(
        net.layers[0].weights, sensor_len + 1, 0.0, axis=1
    )
    net.layers[0].weights = np.insert(
        net.layers[0].weights, sensor_len + 1, 0.0, axis=1
    )
    output_size = net.layers[-1].output_size - net.rec_size
    net.layers[-1].output_size += 1
    net.layers[-1].weights = np.insert(net.layers[-1].weights, output_size, 0.0, axis=0)
    return net


if __name__ == "__main__":
    net = dense_net(3, 10, tanh)
    print(net.layers[0].weights)
    net.add_layer(2, tanh)
    print(net.activate(np.array([1, 1, 1])))
    net.mutate(0.05)
    print(net.activate(np.array([1, 1, 1])))

    def timetest():
        net = dense_net(3, 10, tanh)
        net.add_layer(2, tanh)
        for i in range(1000):
            net.activate(np.array([1, 1, 1]))

    import cProfile

    cProfile.run("timetest()")
