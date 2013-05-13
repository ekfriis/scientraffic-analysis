# -*- coding: utf-8 -*-

import numpy
import math
from nose.tools import eq_

from stanalysis.routerunner import generate_random_choices, build_osrm_url,\
    parse_osrm_output, generate_random_choices_exponential


def test_generate_random_choice():
    numpy.random.seed(0xDEADBEEF)
    eq_(list(generate_random_choices(5, range(10))),
        [(8, 1), (2, 1), (5, 1), (7, 4), (4, 0)])


def test_generate_random_choice_weighted():
    numpy.random.seed(0xDEADBEEF)
    input_array = numpy.array(
        [(8, 1), (2, 1), (5, 1), (7, 4), (4, 0)],
        dtype=int)

    def distance(a, b):
        return numpy.hypot(*(a - b))

    eq_(distance(input_array[2], input_array[1]), 3)

    pairs = zip(input_array[:-1], input_array[1:])

    max_distance = max(map(lambda x: distance(x[0], x[1]), pairs))

    eq_(max_distance, distance(input_array[0], input_array[1]))

    def mc_selector(a, b):
        throw = numpy.random.random_sample()
        normalized_distance = distance(a, b) * 1./max_distance

        normalized_distance = (normalized_distance**2)

        if throw < math.exp(-normalized_distance):
            return True
        return False

    result = list(generate_random_choices(5, input_array, mc_selector))
    eq_([(list(x[0]), list(x[1])) for x in result],
        [([8, 1], [2, 1]), ([5, 1], [2, 1]), ([7, 4], [8, 1]),
         ([8, 1], [7, 4]), ([7, 4], [8, 1])])

    # Make sure we have the same implementation
    numpy.random.seed(0xDEADBEEF)
    standard_impl = list(generate_random_choices_exponential(5, input_array))
    assert(numpy.array_equal(result, standard_impl))


def test_build_osrm_url():
    eq_(build_osrm_url(((34E5, -118E5), (35E5, -118E5)), 'the_host', 9999),
        'http://the_host:9999/viaroute?loc=34.000000,-118.000000&'
        'loc=35.000000,-118.000000&instructions=false&raw=true')


def test_parse_osrm_output():

    class MockResponse():
        def json(self):
            return {
                'raw_data': [
                    [0, 1, 2, 3],
                    [4, 5, 6, 7]
                ]
            }

    result = parse_osrm_output(MockResponse())
    assert(numpy.array_equal(
        result, numpy.array([[0, 1, 2, 3], [4, 5, 6, 7]], dtype=int)))
